import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import boto3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .models import put_submission, get_submission
from .transcribe_client import start_medical_transcription

app = FastAPI()

SUBMISSIONS_TABLE = os.environ.get("SUBMISSIONS_TABLE", "Submissions")
TRANSCRIPTS_BUCKET = os.environ.get("S3_BUCKET_TRANSCRIPTS")


class SubmissionIn(BaseModel):
    audio_key: Optional[str] = None
    transcript_key: Optional[str] = None


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/presign-upload")
def presign_upload(key: Optional[str] = None, content_type: str = "audio/wav"):
    if not TRANSCRIPTS_BUCKET:
        raise HTTPException(status_code=500, detail="TRANSCRIPTS_BUCKET not configured")
    if key is None:
        key = f"raw/{uuid.uuid4()}.wav"
    else:
        key = f"raw/{key}"
    s3 = boto3.client("s3")
    url = s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": TRANSCRIPTS_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=3600,
    )
    return {"upload_url": url, "audio_key": key}


@app.post("/submissions")
def create_submission(body: SubmissionIn):
    submission_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "submission_id": submission_id,
        "created_at": now,
        "status": "RECEIVED",
    }

    if body.audio_key:
        if not TRANSCRIPTS_BUCKET:
            raise HTTPException(status_code=500, detail="TRANSCRIPTS_BUCKET not configured")
        job_name = start_medical_transcription(
            submission_id=submission_id,
            bucket=TRANSCRIPTS_BUCKET,
            audio_key=body.audio_key,
        )
        item.update(
            {
                "status": "TRANSCRIBING",
                "audio_key": body.audio_key,
                "transcribe_job_name": job_name,
            }
        )
    elif body.transcript_key:
        item.update({"status": "READY_FOR_SANITIZE", "transcript_key": body.transcript_key})
    else:
        raise HTTPException(status_code=400, detail="Provide audio_key or transcript_key")

    put_submission(SUBMISSIONS_TABLE, item)
    return {"submission_id": submission_id, "status": item["status"]}


@app.get("/submissions/{submission_id}")
def read_submission(submission_id: str):
    item = get_submission(SUBMISSIONS_TABLE, submission_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item

