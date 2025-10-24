"""
Question Matching Service

This service handles:
1. BM25-based lexical matching
2. Embedding-based semantic matching
3. Hybrid scoring for robust phrase detection

Port: 8003
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from pathlib import Path
import sys

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.rubric import KeyQuestion
from shared.models.transcript import SegmentedTranscript
from shared.models.evaluation import QuestionMatchingResult
from services.question_matching.app.matcher import QuestionMatcher

app = FastAPI(
    title="Question Matching Service",
    description="Match key questions using BM25 and semantic embeddings",
    version="1.0.0"
)


# Request/Response Models
class MatchRequest(BaseModel):
    """Request to match questions."""
    key_questions: List[KeyQuestion] = Field(..., description="Key questions from rubric")
    segmented_transcript: SegmentedTranscript = Field(..., description="Segmented transcript")
    bm25_weight: float = Field(default=0.4, ge=0.0, le=1.0, description="Weight for BM25 score")
    embedding_weight: float = Field(default=0.6, ge=0.0, le=1.0, description="Weight for embedding score")
    match_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum score to consider a match")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "key_questions": [
                    {
                        "id": "Q1",
                        "anchor": "#R.questions.Q1",
                        "phrases": ["when did", "what time"],
                        "is_critical": True
                    }
                ],
                "segmented_transcript": {
                    "transcript_id": "test_001",
                    "sections": [],
                    "detected_order": []
                },
                "bm25_weight": 0.4,
                "embedding_weight": 0.6,
                "match_threshold": 0.5
            }
        }
    }


class ConfigResponse(BaseModel):
    """Configuration information."""
    bm25_available: bool
    embeddings_available: bool
    embedding_model: str
    default_bm25_weight: float
    default_embedding_weight: float
    default_threshold: float


# Initialize matcher
matcher = QuestionMatcher()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "question_matching"
    }


@app.post("/match/questions", response_model=QuestionMatchingResult)
async def match_questions(request: MatchRequest):
    """
    Match key questions against transcript using hybrid BM25 + embeddings.
    
    The matching process:
    1. Extract all student utterances from transcript
    2. For each question, compute BM25 scores for all phrases
    3. For each question, compute embedding similarity scores
    4. Combine scores using weighted average
    5. Match if combined score exceeds threshold
    
    Returns:
    - Matched questions with confidence scores
    - Unmatched question IDs
    - Total and matched weights
    """
    try:
        # Create matcher with custom weights if provided
        custom_matcher = QuestionMatcher(
            bm25_weight=request.bm25_weight,
            embedding_weight=request.embedding_weight,
            match_threshold=request.match_threshold
        )
        
        result = custom_matcher.match_questions(
            key_questions=request.key_questions,
            segmented_transcript=request.segmented_transcript
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to match questions: {str(e)}")


@app.get("/config", response_model=ConfigResponse)
async def get_config():
    """
    Get configuration information about the matching service.
    
    Returns information about:
    - Whether BM25 is available
    - Whether embeddings are available
    - Default weights and thresholds
    """
    try:
        from rank_bm25 import BM25Okapi
        bm25_available = True
    except ImportError:
        bm25_available = False
    
    try:
        from sentence_transformers import SentenceTransformer
        embeddings_available = True
    except ImportError:
        embeddings_available = False
    
    return ConfigResponse(
        bm25_available=bm25_available,
        embeddings_available=embeddings_available,
        embedding_model="all-MiniLM-L6-v2",
        default_bm25_weight=0.4,
        default_embedding_weight=0.6,
        default_threshold=0.5
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

