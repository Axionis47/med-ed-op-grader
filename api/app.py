import os
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3

from .sanitize import strip_control, basic_deid, normalize_sentences
from .gatekeeper import is_sufficient

app = FastAPI()

TRANSCRIPTS_BUCKET = os.environ.get("S3_BUCKET_TRANSCRIPTS")

class SanitizeIn(BaseModel):
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
        return {"status": "INSUFFICIENT_CONTENT", "reason": reason}

    # write sanitized
    submission_id = str(uuid.uuid4())
    sanitized_key = f"sanitized/{submission_id}.txt"
    s3.put_object(Bucket=TRANSCRIPTS_BUCKET, Key=sanitized_key, Body=text.encode("utf-8"))

    return {"status": "SANITIZED", "sanitized_key": sanitized_key}
