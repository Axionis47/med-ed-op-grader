import os
import uuid
import json
import urllib.request
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

# Health endpoint for smoke checks
@app.get("/health")
def health():
    return {"status": "ok"}

SUBMISSIONS_TABLE = os.environ.get("SUBMISSIONS_TABLE", "Submissions")
TRANSCRIPTS_BUCKET = os.environ.get("S3_BUCKET_TRANSCRIPTS")


class SanitizeIn(BaseModel):
    submission_id: str
    transcript_key: str


@app.post("/sanitize")
def sanitize_endpoint(body: SanitizeIn):
    if not TRANSCRIPTS_BUCKET:
        raise HTTPException(status_code=500, detail="TRANSCRIPTS_BUCKET not configured")
    s3 = boto3.client("s3")
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
        update_submission(body.submission_id, status="INSUFFICIENT_CONTENT")
        return {"status": "INSUFFICIENT_CONTENT", "reason": reason}

    # write sanitized
    sanitized_key = f"sanitized/{body.submission_id}.txt"
    s3.put_object(Bucket=TRANSCRIPTS_BUCKET, Key=sanitized_key, Body=text.encode("utf-8"))
    update_submission(
        body.submission_id,
        status="SANITIZED",
        sanitized_key=sanitized_key,
    )
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
    # Read submission to get job name
    item = get_submission(body.submission_id)
    if not item:
        raise HTTPException(status_code=404, detail="Submission not found")
    job_name = item.get("transcribe_job_name")
    if not job_name:
        raise HTTPException(status_code=400, detail="No transcribe_job_name on submission")

    tx = boto3.client("transcribe")
    resp = tx.get_medical_transcription_job(MedicalTranscriptionJobName=job_name)
    job = resp.get("MedicalTranscriptionJob", {})
    status = job.get("TranscriptionJobStatus")

    if status == "FAILED":
        reason = job.get("FailureReason", "Unknown")
        update_submission(body.submission_id, status="TRANSCRIBE_FAILED", failure_reason=reason)
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

    # Persist JSON and extracted text to S3
    s3 = boto3.client("s3")
    json_key = f"json/{body.submission_id}.json"
    s3.put_object(Bucket=TRANSCRIPTS_BUCKET, Key=json_key, Body=json.dumps(json_obj).encode("utf-8"))

    transcripts = json_obj.get("results", {}).get("transcripts", [])
    text = transcripts[0].get("transcript", "") if transcripts else ""
    raw_key = f"raw/{body.submission_id}.txt"
    s3.put_object(Bucket=TRANSCRIPTS_BUCKET, Key=raw_key, Body=text.encode("utf-8"))

    conf_summary = confidence_summary_from_transcribe(json_obj)

    update_submission(
        body.submission_id,
        status="READY_FOR_SANITIZE",
        transcript_key=raw_key,
        transcribe_json_key=json_key,
        word_conf_summary=conf_summary,
    )
    return {"status": "READY_FOR_SANITIZE", "transcript_key": raw_key, "transcribe_json_key": json_key}
