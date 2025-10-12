from __future__ import annotations
from typing import Any, Dict, List, Tuple

MANDATORY_PERTINENTS = {"forehead spared", "no seizure", "ear rash"}


def _hpi_bounds_from_analysis(analysis: Dict[str, Any]) -> Tuple[int, int]:
    sections = analysis.get("sections") or []
    for s in sections:
        if (s.get("name") or s.get("id")) in ("HPI", "hpi"):
            return int(s.get("start_line", 1)), int(s.get("end_line", 1))
    # fallback
    return 1, 1


def presence_v1(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Check for presence of core sections from sectioner output.
    We treat section names: CC, HPI, PMH/PSH, FH, SH, ROS.
    Evidence uses section bounds when present; fallback to HPI evidence.
    """
    sections = analysis.get("sections") or []
    names = {str((s.get("name") or s.get("id") or "")).strip().lower() for s in sections}
    required = ["cc", "hpi", "pmh", "psh", "fh", "sh", "ros"]
    present = set()
    for r in required:
        # treat pmh/psh if either found
        if r in ("pmh", "psh"):
            if ("pmh" in names) or ("psh" in names) or ("pmh/psh" in names):
                present.add("pmh_psh")
        else:
            if r in names or (r == "cc" and any("chief" in n for n in names)):
                present.add(r)
    # count unique buckets: cc, hpi, pmh_psh, fh, sh, ros
    have = set()
    for r in ("cc", "hpi", "pmh_psh", "fh", "sh", "ros"):
        if r in present:
            have.add(r)
    missing = 6 - len(have)
    if missing == 0:
        score = 2
        rationale = "All core sections present"
    elif missing == 1:
        score = 1
        rationale = "One core section missing"
    else:
        score = 0
        rationale = f"{missing} core sections missing"

    # evidence: prefer HPI bounds when available
    ev: List[List[int]] = []
    for s in sections:
        nm = str((s.get("name") or s.get("id") or "")).strip().lower()
        if nm in ("hpi", "cc", "ros") and s.get("start_line") and s.get("end_line"):
            ev.append([int(s["start_line"]), int(s["end_line"])])
            break
    if not ev:
        s, e = _hpi_bounds_from_analysis(analysis)
        ev = [[s, e]]

    return {"id": "sections_present", "score": score, "rationale": rationale, "evidence": ev, "action": "Ensure all core sections (CC, HPI, PMH/PSH, FH, SH, ROS) are documented."}


def hpi_quality_v2(analysis: Dict[str, Any]) -> Dict[str, Any]:
    tl = analysis.get("timeline") or {}
    events = tl.get("events") or []
    onset = next((ev for ev in events if ev.get("type") == "onset" and (ev.get("confidence") or 0) >= 0.7), None)
    pertinents = (analysis.get("pertinents") or {}).get("items") or []
    ddx = analysis.get("ddx") or analysis.get("DDx") or analysis.get("ddx", [])
    ddx = analysis.get("ddx") or [] if isinstance(ddx, list) else []

    hpi_pert = [p for p in pertinents if p.get("placement") == "hpi"]
    ev = []
    if onset and onset.get("evidence"):
        ev.extend(onset["evidence"])  # capture onset evidence

    if onset and len(hpi_pert) >= 2 and len(ddx) >= 3:
        score, rationale = 2, "Onset anchored with >=2 associated HPI findings and DDx considered"
    elif onset:
        score, rationale = 1, "Onset anchored but associated findings or DDx context are thin"
    else:
        score, rationale = 0, "Missing onset anchor (clock or LKW) in HPI"

    if not ev:
        s, e = _hpi_bounds_from_analysis(analysis)
        ev = [[s, e]]

    return {"id": "hpi_quality", "score": score, "rationale": rationale, "evidence": ev, "action": "State onset/LKW with confidence and tie ≥2 symptoms to DDx in HPI."}


def patient_profile_v1(analysis: Dict[str, Any]) -> Dict[str, Any]:
    names = {str((s.get("name") or s.get("id") or "")).strip().lower() for s in (analysis.get("sections") or [])}
    have = sum([
        1 if ("pmh" in names or "pmh/psh" in names) else 0,
        1 if ("meds" in names or "medications" in names or "allergies" in names) else 0,
        1 if ("fh" in names) else 0,
        1 if ("sh" in names) else 0,
    ])
    if have >= 3:
        score, rationale = 2, "PMH/meds+allergies/FH/SH largely present"
    elif have >= 1:
        score, rationale = 1, "Some patient profile elements are thin or missing"
    else:
        score, rationale = 0, "Patient profile largely missing"
    s, e = _hpi_bounds_from_analysis(analysis)
    return {"id": "patient_profile", "score": score, "rationale": rationale, "evidence": [[s, e]], "action": "Document PMH/meds/allergies/FH/SH succinctly and pertinently."}


def ros_focused_v1(analysis: Dict[str, Any]) -> Dict[str, Any]:
    names = {str((s.get("name") or s.get("id") or "")).strip().lower() for s in (analysis.get("sections") or [])}
    pertinents = (analysis.get("pertinents") or {}).get("items") or []
    has_ros = ("ros" in names)
    has_cc_pert = any(p.get("placement") == "hpi" for p in pertinents)
    if has_ros and has_cc_pert:
        score, rationale = 2, "ROS present and focused on CC domains"
    elif has_ros:
        score, rationale = 1, "ROS present but generic/superficial"
    else:
        score, rationale = 0, "ROS missing"
    s, e = _hpi_bounds_from_analysis(analysis)
    return {"id": "ros_focused", "score": score, "rationale": rationale, "evidence": [[s, e]], "action": "Target ROS to complaint-specific systems; avoid exhaustive lists."}


def pertinents_in_hpi_v1(analysis: Dict[str, Any]) -> Dict[str, Any]:
    items = (analysis.get("pertinents") or {}).get("items") or []
    hpi_items = [it for it in items if it.get("placement") == "hpi"]
    names_hpi = {it.get("name", "").lower() for it in hpi_items}
    all_mandatory_in_hpi = all(m in names_hpi for m in MANDATORY_PERTINENTS)

    other_hpi = len([it for it in hpi_items if it.get("name", "").lower() not in MANDATORY_PERTINENTS])

    if all_mandatory_in_hpi and other_hpi >= 1:
        score, rationale = 2, "Mandatory discriminators in HPI plus ≥1 other"
    elif any(it.get("placement") == "ros" for it in items):
        score, rationale = 1, "Pertinents found but credited outside HPI (capped)"
    elif hpi_items:
        score, rationale = 1, "Some HPI pertinents present but mandatory set incomplete"
    else:
        score, rationale = 0, "Pertinents missing in HPI"

    ev: List[List[int]] = []
    for it in hpi_items:
        if it.get("evidence"):
            ev.extend(it["evidence"])
    if not ev:
        s, e = _hpi_bounds_from_analysis(analysis)
        ev = [[s, e]]

    return {"id": "pertinents_in_hpi", "score": score, "rationale": rationale, "evidence": ev, "action": "State mandatory discriminators inside HPI (forehead spared, no seizure, no ear rash)."}


def summary_two_sentences_v1(analysis: Dict[str, Any]) -> Dict[str, Any]:
    summ = analysis.get("summary") or {}
    has_two = bool(summ.get("has_two_sentences"))
    if has_two:
        score, rationale = 2, "Two-sentence summary present"
    elif summ.get("history_sentence"):
        score, rationale = 1, "Single-sentence summary present"
    else:
        score, rationale = 0, "Summary missing"
    ev = summ.get("evidence") or [[1, 1]]
    return {"id": "summary_two_sentences", "score": score, "rationale": rationale, "evidence": ev, "action": "End HPI with two-sentence summary (history + exam)."}


def problem_list_v1(analysis: Dict[str, Any]) -> Dict[str, Any]:
    ddx = analysis.get("ddx") or []
    if len(ddx) >= 2:
        score, rationale = (2 if len(ddx) >= 3 else 1), ("≥2 problems framed via DDx" if len(ddx) >= 3 else "One problem identified")
    elif len(ddx) == 1:
        score, rationale = 1, "One problem identified"
    else:
        score, rationale = 0, "No problems identified"
    s, e = _hpi_bounds_from_analysis(analysis)
    return {"id": "problem_list", "score": score, "rationale": rationale, "evidence": [[s, e]], "action": "List ≥2 specific problems framed diagnostically."}


def ddx_v1(analysis: Dict[str, Any]) -> Dict[str, Any]:
    ddx = analysis.get("ddx") or []
    all_have = all(
        isinstance(d, dict) and d.get("dx") and isinstance(d.get("why_for"), list) and isinstance(d.get("why_against"), list) and (d.get("priority") is not None)
        for d in ddx
    )
    if len(ddx) >= 3 and all_have:
        score, rationale = 2, "≥3 DDx with why-for/against and priorities"
    elif ddx:
        score, rationale = 1, "DDx present but incomplete (list-only or missing reasoning/priorities)"
    else:
        score, rationale = 0, "No differential diagnosis provided"
    s, e = _hpi_bounds_from_analysis(analysis)
    return {"id": "ddx", "score": score, "rationale": rationale, "evidence": [[s, e]], "action": "State ≥3 DDx with why-for/against and clear priorities."}


def run_all_scoring(analysis: Dict[str, Any]) -> Dict[str, Any]:
    # Results grouped roughly by rubric steps
    history = [
        presence_v1(analysis),
        hpi_quality_v2(analysis),
        ros_focused_v1(analysis),
        pertinents_in_hpi_v1(analysis),
        summary_two_sentences_v1(analysis),
    ]
    assessment_plan = [
        problem_list_v1(analysis),
        ddx_v1(analysis),
    ]
    # Sum with a cap of 16
    total = sum(s["score"] for s in history + assessment_plan)
    total = min(total, 16)
    return {
        "steps": [
            {"id": "history", "sections": history},
            {"id": "assessment_plan", "sections": assessment_plan},
        ],
        "overall": {"sum": total, "max": 16},
    }

