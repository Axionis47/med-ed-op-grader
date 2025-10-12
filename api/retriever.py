from __future__ import annotations
import os
import re
from typing import Any, Dict, List, Tuple

import boto3

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE_CHARS", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP_CHARS", "100"))
TOP_K = int(os.getenv("TOP_K", "6"))

# Basic anchors
TIME_RE = re.compile(r"(?i)\b\d{1,2}:\d{2}\b|last\s+known\s+well|onset|sudden(?:ly)?")
HPI_RE = re.compile(r"(?i)\bHPI\b|history of present illness")
ROS_RE = re.compile(r"(?i)\bROS\b|review of systems")


def chunk_lines(lines: List[str], chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Dict[str, Any]]:
    chunks: List[Dict[str, Any]] = []
    cur: List[str] = []
    cur_start = 1
    cur_len = 0
    i = 1
    for ln in lines:
        l = len(ln) + 1
        if cur_len + l > chunk_size and cur:
            chunks.append({
                "text": "\n".join(cur),
                "line_start": cur_start,
                "line_end": i - 1,
            })
            # overlap by lines roughly
            back = max(0, len(cur) - max(1, overlap // 60))
            cur = cur[back:]
            cur_start = i - len(cur)
            cur_len = sum(len(x) + 1 for x in cur)
        cur.append(ln)
        cur_len += l
        i += 1
    if cur:
        chunks.append({"text": "\n".join(cur), "line_start": cur_start, "line_end": i - 1})
    return chunks


def regex_retrieve(lines: List[str], budget: int = TOP_K) -> List[Dict[str, Any]]:
    """Return up to TOP_K line windows around HPI/TIME anchors."""
    hits: List[Tuple[int, int]] = []
    n = len(lines)
    for idx, ln in enumerate(lines, start=1):
        if HPI_RE.search(ln) or TIME_RE.search(ln) or ROS_RE.search(ln):
            s = max(1, idx - 2)
            e = min(n, idx + 2)
            hits.append((s, e))
        if len(hits) >= budget:
            break
    out: List[Dict[str, Any]] = []
    for s, e in hits:
        out.append({"text": "\n".join(lines[s-1:e]), "line_start": s, "line_end": e})
    return out


def build_context(lines: List[str], budget: int = TOP_K) -> List[Dict[str, Any]]:
    # In absence of OpenSearch wiring, use regex retrieval; when AOSS is available, merge its top-k with regex.
    return regex_retrieve(lines, budget=budget)

