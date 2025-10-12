import os
import boto3

def start_medical_transcription(submission_id: str, bucket: str, audio_key: str, language: str | None = None) -> str:
    """Starts a Transcribe Medical job and returns the job name."""
    language = language or os.environ.get("TRANSCRIBE_LANGUAGE", "en-US")
    job_name = f"transcribe_{submission_id}"
    media_uri = f"s3://{bucket}/{audio_key}"

    client = boto3.client("transcribe")
    client.start_medical_transcription_job(
        MedicalTranscriptionJobName=job_name,
        LanguageCode=language,
        Specialty="PRIMARYCARE",
        Type="DICTATION",
        Media={"MediaFileUri": media_uri},
        OutputBucketName=bucket,
        Settings={
            "ShowSpeakerLabels": False,
            "ShowAlternatives": False,
            "ChannelIdentification": False,
        },
    )
    return job_name

