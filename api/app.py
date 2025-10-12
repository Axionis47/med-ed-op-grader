import os
import uuid
import json
import urllib.request
import logging
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3

from .sanitize import (
    strip_control,
    basic_deid,
    normalize_sentences,
    confidence_summary_from_transcribe,
)
from .gatekeeper import is_sufficient
from .models import get_submission, update_submission

app = FastAPI()
logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

# Health endpoint for smoke checks
@app.get("/health")
def health():
    return {"status": "ok"}

SUBMISSIONS_TABLE = os.environ.get("SUBMISSIONS_TABLE", "Submissions")
TRANSCRIPTS_BUCKET = os.environ.get("S3_BUCKET_TRANSCRIPTS")
STAGE = os.environ.get("STAGE", "dev")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _partition_prefix(test_id: str, submission_id: str) -> str:
    return f"stage={STAGE}/test_id={test_id}/submission_id={submission_id}"


class PresignOut(BaseModel):
    submission_id: str
    test_id: str
    audio_key: str
    upload_url: str


@app.post("/presign-upload")
def presign_upload(test_id: str | None = None, content_type: str = "audio/wav"):
    if not TRANSCRIPTS_BUCKET:
        raise HTTPException(status_code=500, detail="TRANSCRIPTS_BUCKET not configured")
    if test_id is None:
        test_id = "adhoc"
    submission_id = str(uuid.uuid4())
    prefix = _partition_prefix(test_id, submission_id)
    audio_name = f"{uuid.uuid4()}.wav"
    audio_key = f"{prefix}/audio/{audio_name}"

    s3 = boto3.client("s3")
    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": TRANSCRIPTS_BUCKET, "Key": audio_key, "ContentType": content_type},
        ExpiresIn=3600,
    )
    return {"submission_id": submission_id, "test_id": test_id, "audio_key": audio_key, "upload_url": url}


class SubmissionIn(BaseModel):
    submission_id: str | None = None
    test_id: str | None = None
    audio_key: str | None = None
    transcript_key: str | None = None


@app.post("/submissions")
def create_or_get_submission(body: SubmissionIn):
    if not TRANSCRIPTS_BUCKET:
        raise HTTPException(status_code=500, detail="TRANSCRIPTS_BUCKET not configured")

    sub_id = body.submission_id or str(uuid.uuid4())
    existing = get_submission(sub_id)
    if existing:
        return existing

    test_id = body.test_id or "adhoc"
    item = {
        "submission_id": sub_id,
        "test_id": test_id,
        "status": "RECEIVED",
        "version": 1,
        "status_history": [{"at": _now_iso(), "status": "RECEIVED", "note": "create"}],
    }

    if body.audio_key:
        # Start Transcribe Medical job
        tx = boto3.client("transcribe")
        job_name = f"transcribe_{sub_id}"
        media_uri = f"s3://{TRANSCRIPTS_BUCKET}/{body.audio_key}"
        tx.start_medical_transcription_job(
            MedicalTranscriptionJobName=job_name,
            LanguageCode=os.environ.get("TRANSCRIBE_LANGUAGE", "en-US"),
            Specialty=os.environ.get("TRANSCRIBE_SPECIALTY", "PRIMARYCARE"),
            Type=os.environ.get("TRANSCRIBE_TYPE", "DICTATION"),
            Media={"MediaFileUri": media_uri},
            OutputBucketName=TRANSCRIPTS_BUCKET,
        )
        logger.info({
            "evt": "submission_status_change",
            "submission_id": sub_id,
            "from": "RECEIVED",
            "to": "TRANSCRIBING",
            "keys": {"audio": body.audio_key},
            "job": job_name,
        })
        update_submission(
            sub_id,
            status="TRANSCRIBING",
            test_id=test_id,
            audio_key=body.audio_key,
            transcribe_job_name=job_name,
            add_history={"at": _now_iso(), "status": "TRANSCRIBING", "note": f"job_name={job_name}"},
        )
        return {"submission_id": sub_id, "status": "TRANSCRIBING"}

    if body.transcript_key:
        update_submission(
            sub_id,
            status="READY_FOR_SANITIZE",
            test_id=test_id,
            transcript_key=body.transcript_key,
            add_history={"at": _now_iso(), "status": "READY_FOR_SANITIZE", "note": f"raw={body.transcript_key}"},
        )
        return {"submission_id": sub_id, "status": "READY_FOR_SANITIZE"}

    raise HTTPException(status_code=400, detail="Provide audio_key or transcript_key")


class SanitizeIn(BaseModel):
    submission_id: str
    transcript_key: str


@app.post("/sanitize")
def sanitize_endpoint(body: SanitizeIn):
    if not TRANSCRIPTS_BUCKET:
        raise HTTPException(status_code=500, detail="TRANSCRIPTS_BUCKET not configured")
    s3 = boto3.client("s3")

    # Fetch submission to get test_id and prior status
    sub = get_submission(body.submission_id) or {}
    test_id = sub.get("test_id", "adhoc")

    # load transcript
    try:
        obj = s3.get_object(Bucket=TRANSCRIPTS_BUCKET, Key=body.transcript_key)
        text = obj["Body"].read().decode("utf-8", errors="ignore")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Transcript not found: {e}")

    # process pipeline
    text = strip_control(text)
    text = basic_deid(text)
    text = normalize_sentences(text)

    ok, reason = is_sufficient(text)
    if not ok:
        update_submission(
            body.submission_id,
            status="INSUFFICIENT_CONTENT",
            add_history={"at": _now_iso(), "status": "INSUFFICIENT_CONTENT", "note": reason},
        )
        logger.info({
            "evt": "submission_status_change",
            "submission_id": body.submission_id,
            "from": sub.get("status"),
            "to": "INSUFFICIENT_CONTENT",
        })
        return {"status": "INSUFFICIENT_CONTENT", "reason": reason}

    # write sanitized to partitioned path
    prefix = _partition_prefix(test_id, body.submission_id)
    sanitized_key = f"{prefix}/sanitized/text.txt"
    s3.put_object(Bucket=TRANSCRIPTS_BUCKET, Key=sanitized_key, Body=text.encode("utf-8"))
    update_submission(
        body.submission_id,
        status="SANITIZED",
        sanitized_key=sanitized_key,
        add_history={"at": _now_iso(), "status": "SANITIZED", "note": f"sanitized={sanitized_key}"},
    )
    logger.info({
        "evt": "submission_status_change",
        "submission_id": body.submission_id,
        "from": sub.get("status"),
        "to": "SANITIZED",
        "keys": {"sanitized": sanitized_key},
    })
    return {"status": "SANITIZED", "sanitized_key": sanitized_key}


@app.get("/submissions/{submission_id}")
def read_submission(submission_id: str):
    item = get_submission(submission_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item


class PollIn(BaseModel):
    submission_id: str


@app.post("/transcribe/poll")
def poll_transcribe(body: PollIn):
    # Read submission to get job name and test_id
    item = get_submission(body.submission_id)
    if not item:
        raise HTTPException(status_code=404, detail="Submission not found")
    job_name = item.get("transcribe_job_name")
    test_id = item.get("test_id", "adhoc")
    if not job_name:
        raise HTTPException(status_code=400, detail="No transcribe_job_name on submission")

    tx = boto3.client("transcribe")
    resp = tx.get_medical_transcription_job(MedicalTranscriptionJobName=job_name)
    job = resp.get("MedicalTranscriptionJob", {})
    status = job.get("TranscriptionJobStatus")

    if status == "FAILED":
        reason = job.get("FailureReason", "Unknown")
        update_submission(
            body.submission_id,
            status="TRANSCRIBE_FAILED",
            failure_reason=reason,
            add_history={"at": _now_iso(), "status": "TRANSCRIBE_FAILED", "note": reason},
        )
        logger.info({
            "evt": "submission_status_change",
            "submission_id": body.submission_id,
            "from": item.get("status"),
            "to": "TRANSCRIBE_FAILED",
            "job": job_name,
        })
        return {"status": "TRANSCRIBE_FAILED", "reason": reason}

    if status != "COMPLETED":
        return {"status": "TRANSCRIBING"}

    # COMPLETED: fetch transcript JSON
    transcript_uri = job.get("Transcript", {}).get("TranscriptFileUri")
    if not transcript_uri:
        raise HTTPException(status_code=500, detail="Missing TranscriptFileUri")

    with urllib.request.urlopen(transcript_uri) as r:
        data = r.read()
        json_obj = json.loads(data)

    # Persist JSON and extracted text to partitioned S3
    s3 = boto3.client("s3")
    prefix = _partition_prefix(test_id, body.submission_id)
    json_key = f"{prefix}/transcribe/json.json"
    s3.put_object(Bucket=TRANSCRIPTS_BUCKET, Key=json_key, Body=json.dumps(json_obj).encode("utf-8"))

    transcripts = json_obj.get("results", {}).get("transcripts", [])
    text = transcripts[0].get("transcript", "") if transcripts else ""
    raw_key = f"{prefix}/transcribe/raw.txt"
    s3.put_object(Bucket=TRANSCRIPTS_BUCKET, Key=raw_key, Body=text.encode("utf-8"))

    conf_summary = confidence_summary_from_transcribe(json_obj)

    update_submission(
        body.submission_id,
        status="READY_FOR_SANITIZE",
        transcript_key=raw_key,
        transcribe_json_key=json_key,
        word_conf_summary=conf_summary,
        add_history={"at": _now_iso(), "status": "READY_FOR_SANITIZE", "note": f"json={json_key} raw={raw_key}"},
    )
    logger.info({
        "evt": "submission_status_change",
        "submission_id": body.submission_id,
        "from": item.get("status"),
        "to": "READY_FOR_SANITIZE",
        "keys": {"json": json_key, "raw": raw_key},
        "job": job_name,
    })
    return {"status": "READY_FOR_SANITIZE", "transcript_key": raw_key, "transcribe_json_key": json_key}


# -------------------- Phase 3 scaffolds --------------------
from typing import List, Dict, Any, Optional
import re
from .analysis import load_sanitized_text, find_hpi_bounds, find_time_events, extract_pertinents, simple_summary, simple_ddx

class AnalyzeIn(BaseModel):
    submission_id: str
    hpi_bounds: Optional[dict] = None
    cc_pack: Optional[str] = "stroke"


def _load_lines_for_submission(submission_id: str) -> List[str]:
    s3 = boto3.client("s3")
    sub = get_submission(submission_id)
    if not sub or not sub.get("sanitized_key"):
        raise HTTPException(status_code=400, detail="sanitized_key missing; run /sanitize first")
    return load_sanitized_text(s3, TRANSCRIPTS_BUCKET, sub["sanitized_key"])


@app.post("/analyze/sectioner")
def analyze_sectioner(body: AnalyzeIn):
    lines = _load_lines_for_submission(body.submission_id)
    s, e, evidence = find_hpi_bounds(lines)
    sections = [{"name": "HPI", "start_line": s, "end_line": e, "evidence": evidence}]
    return {"sections": sections}


@app.post("/analyze/timeline")
def analyze_timeline(body: AnalyzeIn):
    lines = _load_lines_for_submission(body.submission_id)
    if body.hpi_bounds is None:
        s, e, _ = find_hpi_bounds(lines)
    else:
        s = int(body.hpi_bounds.get("start_line", 1))
        e = int(body.hpi_bounds.get("end_line", len(lines)))
    tl = find_time_events(lines, (s, e))
    return tl


@app.post("/analyze/extract")
def analyze_extract(body: AnalyzeIn):
    lines = _load_lines_for_submission(body.submission_id)
    if body.hpi_bounds is None:
        s, e, _ = find_hpi_bounds(lines)
    else:
        s = int(body.hpi_bounds.get("start_line", 1))
        e = int(body.hpi_bounds.get("end_line", len(lines)))
    pertinents = extract_pertinents(lines, (s, e), body.cc_pack or "stroke")
    summary = simple_summary(lines, (s, e))
    ddx = simple_ddx(lines, (s, e))
    return {"pertinents": pertinents, "summary": summary, "ddx": ddx}


@app.post("/analyze/{submission_id}")
def analyze_orchestrate(submission_id: str):
    # Load once
    lines = _load_lines_for_submission(submission_id)
    s, e, ev = find_hpi_bounds(lines)
    sections = {"sections": [{"name": "HPI", "start_line": s, "end_line": e, "evidence": ev}]}
    tl = find_time_events(lines, (s, e))
    pertinents = extract_pertinents(lines, (s, e), "stroke")
    summary = simple_summary(lines, (s, e))
    ddx = simple_ddx(lines, (s, e))

    analysis: Dict[str, Any] = {"sections": sections["sections"], "timeline": tl, "pertinents": pertinents, "summary": summary, "ddx": ddx}

    # Persist analysis.json
    sub = get_submission(submission_id) or {}
    test_id = sub.get("test_id", "adhoc")
    prefix = _partition_prefix(test_id, submission_id)
    analysis_key = f"{prefix}/eval_json/analysis.json"
    s3 = boto3.client("s3")
    s3.put_object(Bucket=TRANSCRIPTS_BUCKET, Key=analysis_key, Body=json.dumps(analysis).encode("utf-8"))

    update_submission(
        submission_id,
        analysis_key=analysis_key,
        analysis_version=1,
        add_history={"at": _now_iso(), "status": "ANALYZED", "note": analysis_key},
    )
    return {"analysis_key": analysis_key, **analysis}
