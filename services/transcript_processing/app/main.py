"""
Transcript Processing Service

This service handles:
1. Parsing raw transcript text into structured utterances
2. Segmenting transcripts into clinical sections
3. Detecting section boundaries

Port: 8002
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from pathlib import Path
import sys

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.transcript import Utterance, SegmentedTranscript
from services.transcript_processing.app.parser import (
    TranscriptParser,
    TranscriptSegmenter,
    TranscriptProcessor
)

app = FastAPI(
    title="Transcript Processing Service",
    description="Parse and segment medical education oral presentation transcripts",
    version="1.0.0"
)


# Request/Response Models
class ParseRequest(BaseModel):
    """Request to parse raw transcript."""
    raw_text: str = Field(..., description="Raw transcript text with timestamps and speakers")
    transcript_id: str = Field(default="unknown", description="Identifier for the transcript")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "raw_text": "[00:05] Student: Tell me what brings you in today?\n[00:08] Patient: I have weakness.",
                "transcript_id": "stroke_001"
            }
        }
    }


class ParseResponse(BaseModel):
    """Response from parsing."""
    transcript_id: str
    utterances: List[Utterance]
    utterance_count: int


class SegmentRequest(BaseModel):
    """Request to segment utterances."""
    utterances: List[Utterance] = Field(..., description="List of utterances to segment")
    transcript_id: str = Field(default="unknown", description="Identifier for the transcript")


class ProcessRequest(BaseModel):
    """Request to process (parse + segment) raw transcript."""
    raw_text: str = Field(..., description="Raw transcript text")
    transcript_id: str = Field(default="unknown", description="Identifier for the transcript")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "raw_text": "[00:05] Student: Tell me what brings you in today?\n[00:08] Patient: I have sudden weakness on my left side.\n[00:15] Student: When did you first notice the weakness?\n[00:18] Patient: About 2 hours ago.",
                "transcript_id": "stroke_001"
            }
        }
    }


# Initialize processors
parser = TranscriptParser()
segmenter = TranscriptSegmenter()
processor = TranscriptProcessor()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "transcript_processing"
    }


@app.post("/transcripts/parse", response_model=ParseResponse)
async def parse_transcript(request: ParseRequest):
    """
    Parse raw transcript text into structured utterances.
    
    Expected format:
    - [MM:SS] Speaker: Text
    - [HH:MM:SS] Speaker: Text
    
    Supported speakers: Student, Patient, Examiner (or S, P abbreviations)
    """
    try:
        utterances = parser.parse(request.raw_text, request.transcript_id)
        
        return ParseResponse(
            transcript_id=request.transcript_id,
            utterances=utterances,
            utterance_count=len(utterances)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse transcript: {str(e)}")


@app.post("/transcripts/segment", response_model=SegmentedTranscript)
async def segment_transcript(request: SegmentRequest):
    """
    Segment utterances into clinical sections.
    
    Detects sections based on keywords:
    - CC (Chief Complaint)
    - HPI (History of Present Illness)
    - ROS (Review of Systems)
    - PMH (Past Medical History)
    - SH (Social History)
    - FH (Family History)
    - Summary
    """
    try:
        segmented = segmenter.segment(request.utterances, request.transcript_id)
        return segmented
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to segment transcript: {str(e)}")


@app.post("/transcripts/process", response_model=SegmentedTranscript)
async def process_transcript(request: ProcessRequest):
    """
    Process raw transcript (parse + segment in one step).
    
    This is the recommended endpoint for most use cases.
    It combines parsing and segmentation into a single operation.
    """
    try:
        segmented = processor.process(request.raw_text, request.transcript_id)
        return segmented
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process transcript: {str(e)}")


@app.get("/sections/keywords")
async def get_section_keywords():
    """
    Get the keywords used for section detection.
    
    Useful for understanding how sections are identified.
    """
    return {
        "section_keywords": TranscriptSegmenter.SECTION_KEYWORDS,
        "description": "Keywords used to detect section boundaries in transcripts"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

