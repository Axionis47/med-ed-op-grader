from __future__ import annotations
from typing import Any, Dict, List


def _line_span(ev: List[List[int]]) -> str:
    if not ev:
        return "(no-evidence)"
    a, b = ev[0]
    return f"lines {a}-{b}"


def compose_feedback(section_results: List[Dict[str, Any]], analysis: Dict[str, Any], cc_pack: str) -> Dict[str, Any]:
    """Compose student-friendly and instructor-friendly feedback.
    Ensures each section has >=1 evidence span; if none, marks unsupported.
    """
    fb_sections: List[Dict[str, Any]] = []
    for sec in section_results:
        ev = sec.get("evidence") or []
        status = None
        if not ev:
            status = "unsupported"
            sec["score"] = 0  # safe default if no evidence
            if not sec.get("action"):
                sec["action"] = "Re-state with evidence."
            ev = [[1, 1]]
            sec["evidence"] = ev
        well = "Meets key criteria" if sec.get("score", 0) == 2 else ("Partially meets" if sec.get("score", 0) == 1 else "Needs improvement")
        fb_sections.append({
            "id": sec.get("id"),
            "well": well,
            "action": sec.get("action", "One specific next step"),
            "evidence": ev,
            **({"status": status} if status else {}),
        })
    return {"sections": fb_sections}

