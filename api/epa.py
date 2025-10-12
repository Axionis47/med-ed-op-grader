from __future__ import annotations
import json
import os
from typing import Any, Dict, List

import boto3

MODEL_ID = os.getenv("BEDROCK_MODEL_EXTRACTOR", "anthropic.claude-3-5-sonnet-20240620-v1:0")
PROMPT_BUNDLE_ID = os.getenv("PROMPT_BUNDLE_ID", "bundle_2025_10_op@1.0.0")


def _fallback_epa(section_scores: Dict[str, int]) -> Dict[str, int]:
    # Simple heuristic if Bedrock call fails
    base6 = 4 if (section_scores.get("sections_present", 0) >= 1 and section_scores.get("hpi_quality", 0) >= 1) else 3
    base2 = 3 if section_scores.get("ddx", 0) >= 1 else 2
    return {"epa6": base6, "epa2": base2}


def _apply_clipping(epa: Dict[str, int], section_scores: Dict[str, int]) -> Dict[str, Any]:
    clipped_by: List[str] = []
    if section_scores.get("sections_present", 0) == 0 or section_scores.get("hpi_quality", 0) == 0:
        if epa["epa6"] > 3:
            epa["epa6"] = 3
            clipped_by.append("presence_or_hpi_quality_zero")
    if section_scores.get("ddx", 0) == 0:
        if epa["epa2"] > 2:
            epa["epa2"] = 2
            clipped_by.append("ddx_zero")
    return {**epa, "clipped_by": clipped_by}


def suggest_epa(analysis: Dict[str, Any], section_scores: Dict[str, int]) -> Dict[str, Any]:
    """Call Bedrock once to suggest EPA-6 and EPA-2, then apply clipping rules."""
    runtime = boto3.client("bedrock-runtime")
    system = (
        "You are an assessor. Return STRICT JSON with keys epa6 (1-5) and epa2 (1-3). "
        "Consider history quality, pertinents, and DDx reasoning. Do not include text beyond JSON."
    )
    user = {
        "prompt_bundle_id": PROMPT_BUNDLE_ID,
        "section_scores": section_scores,
        "analysis_preview": {
            "timeline": analysis.get("timeline", {}),
            "pertinents_count": len((analysis.get("pertinents") or {}).get("items", [])),
            "ddx_count": len(analysis.get("ddx") or []),
            "summary_has_two": bool((analysis.get("summary") or {}).get("has_two_sentences")),
        },
    }
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "system": system,
        "max_tokens": 200,
        "temperature": 0,
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": json.dumps(user)}]},
        ],
    }
    suggested = None
    try:
        resp = runtime.invoke_model(modelId=MODEL_ID, body=json.dumps(body))
        data = json.loads(resp.get("body").read().decode("utf-8"))
        # Anthropic responses include content list
        txt = "".join([c.get("text", "") for c in (data.get("content") or [])])
        suggested = json.loads(txt) if txt.strip().startswith("{") else None
    except Exception:
        suggested = None

    if not suggested:
        suggested = _fallback_epa(section_scores)

    clipped = _apply_clipping({"epa6": int(suggested.get("epa6", 3)), "epa2": int(suggested.get("epa2", 2))}, section_scores)
    return {"epa6": clipped["epa6"], "epa2": clipped["epa2"], "suggested": suggested, "clipped_by": clipped.get("clipped_by", [])}

