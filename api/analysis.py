import os
import re
import json
from typing import List, Dict, Tuple
from datetime import datetime, timezone

import boto3

# Phase 3 utilities (Bedrock + retrieval fallback)
from .bedrock_client import converse_json
from .retriever import build_context


# Simple utilities for Phase 3 scaffolds (no external calls yet)

TIME_RE = re.compile(r"(?i)\b\d{1,2}:\d{2}\b|last\s+known\s+well|sudden(?:ly)?|onset|this\s+morning|yesterday|timeline")
HPI_MARK_RE = re.compile(r"(?i)\bHPI\b|history of present illness")
ROS_MARK_RE = re.compile(r"(?i)\bROS\b|review of systems")

STROKE_PERT_RE = {
    "forehead spared": re.compile(r"(?i)forehead\s+spared"),
    "no seizure": re.compile(r"(?i)no\s+seizure|denies\s+seizure|without\s+seizure"),
    "ear rash": re.compile(r"(?i)ear\s+rash"),
    "aphasia": re.compile(r"(?i)aphasia"),
    "dysarthria": re.compile(r"(?i)dysarthria"),
    "vertigo": re.compile(r"(?i)vertigo"),
    "facial droop": re.compile(r"(?i)facial\s+droop"),
}

PROMPTS_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "prompts", "bundles", os.getenv("PROMPT_BUNDLE_ID", "bundle_2025_10_op@1.0.0")))


def _load_system(name: str) -> str:
    try:
        with open(os.path.join(PROMPTS_ROOT, f"{name}.system.txt"), "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return "Return ONLY valid JSON per schema with evidence line ranges."


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_sanitized_text(s3, bucket: str, key: str) -> List[str]:
    obj = s3.get_object(Bucket=bucket, Key=key)
    text = obj["Body"].read().decode("utf-8", errors="ignore")
    lines = [ln.rstrip("\n\r") for ln in text.splitlines()]
    return lines


def find_hpi_bounds(lines: List[str]) -> Tuple[int, int, List[List[int]]]:
    """Return (start_line, end_line, evidence_spans). 1-based inclusive lines.
    First try LLM sectioner; fallback to heuristic from HPI -> ROS.
    """
    try:
        system = _load_system("sectioner")
        ctx = build_context(lines)
        payload = {"text": "\n".join(lines), "lines_total": len(lines), "context": ctx}
        out = converse_json("sectioner", system, payload)
        if out and out.get("sections"):
            sel = None
            for sec in out["sections"]:
                name = (sec.get("name") or "").lower()
                if "hpi" in name or "present illness" in name:
                    sel = sec
                    break
            if not sel:
                sel = out["sections"][0]
            s = max(1, int(sel.get("start_line", 1)))
            e = max(s, int(sel.get("end_line", s)))
            ev = sel.get("evidence") or [[s, min(s + 1, e)]]
            return s, e, ev
    except Exception:
        pass
    # Fallback heuristic
    n = len(lines)
    start = 1
    end = n
    ev: List[List[int]] = []
    for i, ln in enumerate(lines, start=1):
        if HPI_MARK_RE.search(ln):
            start = i
            ev.append([i, i])
            break
    for j in range(start, n + 1):
        if j <= n and ROS_MARK_RE.search(lines[j - 1]):
            end = max(start, j - 1)
            break
    return start, end, ev or [[start, min(start + 1, end)]]


def find_time_events(lines: List[str], bounds: Tuple[int, int]) -> Dict:
    s, e = bounds
    # Try LLM timeline constrained to HPI window
    try:
        system = _load_system("timeline")
        hpi_text = "\n".join(lines[s - 1 : e])
        payload = {"hpi_text": hpi_text, "bounds": [s, e]}
        out = converse_json("timeline", system, payload)
        if out and isinstance(out.get("events"), list):
            return {"events": out.get("events", []), "conflicts": out.get("conflicts", [])}
    except Exception:
        pass
    # Fallback heuristic
    events = []
    conflicts: List[Dict] = []
    for i in range(s, e + 1):
        ln = lines[i - 1]
        if TIME_RE.search(ln):
            events.append({
                "type": "onset",
                "time_text": TIME_RE.search(ln).group(0),
                "t_offset_min": 0,
                "confidence": 0.8,
                "placement": "hpi",
                "evidence": [[i, i]],
            })
            break
    return {"events": events, "conflicts": conflicts}


def extract_pertinents(lines: List[str], bounds: Tuple[int, int], cc_pack: str) -> Dict:
    s, e = bounds
    # Try LLM extractor with placement awareness
    try:
        system = _load_system("pertinents")
        payload = {"text": "\n".join(lines), "bounds": [s, e], "cc_pack": cc_pack}
        out = converse_json("pertinents", system, payload)
        if out and isinstance(out.get("items"), list) and out["items"]:
            return {"items": out["items"]}
    except Exception:
        pass
    # Fallback regex-based extractor
    items = []
    for name, rx in STROKE_PERT_RE.items():
        found_line = None
        placement = "other"
        for i, ln in enumerate(lines, start=1):
            if rx.search(ln):
                found_line = i
                placement = "hpi" if s <= i <= e else "other"
                break
        if found_line is not None:
            items.append({
                "name": name,
                "mandatory": name in {"forehead spared", "no seizure", "ear rash"},
                "present": True,
                "placement": placement,
                "evidence": [[found_line, found_line]],
            })
    return {"items": items}


def simple_summary(lines: List[str], bounds: Tuple[int, int]) -> Dict:
    s, e = bounds
    # Try LLM summary constrained to HPI bounds
    try:
        system = _load_system("summary")
        hpi_text = "\n".join(lines[s - 1 : e])
        payload = {"hpi_text": hpi_text, "bounds": [s, e]}
        out = converse_json("summary", system, payload)
        if out and isinstance(out.get("evidence"), list):
            return out
    except Exception:
        pass
    # Fallback heuristic
    hpi_lines = [ln for i, ln in enumerate(lines, start=1) if s <= i <= e and ln.strip()]
    has_two = len(hpi_lines) >= 2
    ev = []
    if hpi_lines:
        first_line_idx = next(i for i, ln in enumerate(lines, start=1) if s <= i <= e and ln.strip())
        ev = [[first_line_idx, first_line_idx]]
    history_sentence = hpi_lines[0] if hpi_lines else None
    exam_sentence = hpi_lines[1] if has_two else None
    return {
        "has_two_sentences": has_two,
        "history_sentence": history_sentence,
        "exam_sentence": exam_sentence,
        "evidence": ev or [[s, min(s + 1, e)]],
    }


def simple_ddx(lines: List[str], bounds: Tuple[int, int]) -> List[Dict]:
    s, e = bounds
    # Try LLM DDx within HPI window
    try:
        system = _load_system("ddx")
        hpi_text = "\n".join(lines[s - 1 : e])
        payload = {"hpi_text": hpi_text, "bounds": [s, e]}
        out = converse_json("ddx", system, payload)
        if out and isinstance(out.get("items"), list) and out["items"]:
            return out["items"]
    except Exception:
        pass
    # Fallback scaffolded DDx
    ev = [[s, s]]
    return [
        {"dx": "ischemic stroke", "why_for": ["focal deficits"], "why_against": [], "priority": 1, "evidence": ev},
        {"dx": "hemorrhagic stroke", "why_for": [], "why_against": ["no severe headache"], "priority": 2, "evidence": ev},
        {"dx": "Bell's palsy", "why_for": ["facial droop"], "why_against": ["forehead spared"], "priority": 3, "evidence": ev},
    ]

