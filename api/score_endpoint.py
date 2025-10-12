from __future__ import annotations
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

import boto3

from .scoring import run_all_scoring
from .epa import suggest_epa
from .feedback import compose_feedback
from .models import get_submission, update_submission
from .app import _partition_prefix  # reuse helper

BUCKET = os.getenv("S3_BUCKET_TRANSCRIPTS")
PROMPT_BUNDLE_ID = os.getenv("PROMPT_BUNDLE_ID", "bundle_2025_10_op@1.0.0")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_analysis_json(s3, key: str) -> Dict[str, Any]:
    obj = s3.get_object(Bucket=BUCKET, Key=key)
    data = obj["Body"].read().decode("utf-8", errors="ignore")
    return json.loads(data)


def score_submission(submission_id: str) -> Dict[str, Any]:
    sub = get_submission(submission_id)
    if not sub:
        raise ValueError("submission not found")
    if not sub.get("analysis_key"):
        raise ValueError("analysis_key missing; run /analyze first")

    s3 = boto3.client("s3")
    analysis = _load_analysis_json(s3, sub["analysis_key"]) or {}

    # 1) Deterministic scoring
    scoring_bundle = run_all_scoring(analysis)

    # Flatten section_scores map for EPA
    section_scores: Dict[str, int] = {}
    for step in scoring_bundle["steps"]:
        for sec in step["sections"]:
            section_scores[sec["id"]] = int(sec.get("score", 0))

    # 2) EPA suggestion + clipping
    epa = suggest_epa(analysis, section_scores)

    # 3) Feedback
    all_sections = [s for step in scoring_bundle["steps"] for s in step["sections"]]
    feedback = compose_feedback(all_sections, analysis, sub.get("cc_pack") or "stroke")

    # 4) Persist score.json
    test_id = sub.get("test_id") or "adhoc"
    prefix = _partition_prefix(test_id, submission_id)
    score_key = f"{prefix}/eval_json/score.json"

    score_doc = {
        "submission_id": submission_id,
        "rubric": {"id": "op_universal", "version": 3},
        "steps": scoring_bundle["steps"],
        "overall": scoring_bundle["overall"],
        "epa": epa,
        "feedback": feedback,
        "timeline": analysis.get("timeline"),
        "version": {"scoring": "1.0.0", "prompt_bundle_id": PROMPT_BUNDLE_ID},
        "updated_at": _now_iso(),
    }

    s3.put_object(Bucket=BUCKET, Key=score_key, Body=json.dumps(score_doc).encode("utf-8"))

    # 5) Update DDB
    update_submission(
        submission_id,
        status="SCORED",
        score_key=score_key,
        overall_sum=int(scoring_bundle["overall"]["sum"]),
        epa=epa,
        add_history={"at": _now_iso(), "status": "SCORED", "note": score_key},
    )

    return {"score_key": score_key, **score_doc}


def get_score(submission_id: str) -> Dict[str, Any]:
    sub = get_submission(submission_id)
    if not sub or not sub.get("score_key"):
        raise ValueError("score not found")
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=BUCKET, Key=sub["score_key"])  # type: ignore
    data = obj["Body"].read().decode("utf-8", errors="ignore")
    return json.loads(data)

