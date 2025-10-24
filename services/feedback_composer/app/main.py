"""Feedback Composer Service - Main FastAPI application."""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Literal
from pathlib import Path
import sys

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.evaluation import (
    StructureEvaluation,
    QuestionMatchingResult,
    ReasoningEvaluation,
    SummaryEvaluation
)
from services.feedback_composer.app.composer import FeedbackComposer

app = FastAPI(
    title="Feedback Composer Service",
    description="Generates cited feedback from evaluation results",
    version="1.0.0"
)


# Request/Response Models
class ComposeFeedbackRequest(BaseModel):
    """Request to compose feedback."""
    rubric_id: str
    overall_score: float = Field(..., ge=0, le=1)
    structure_eval: StructureEvaluation | None = None
    questions_eval: QuestionMatchingResult | None = None
    reasoning_eval: ReasoningEvaluation | None = None
    summary_eval: SummaryEvaluation | None = None
    style: Literal["constructive", "detailed", "concise"] = "constructive"


# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "feedback_composer"}


@app.post("/feedback/compose")
async def compose_feedback(request: ComposeFeedbackRequest):
    """
    Generate natural language feedback from structured evaluation results.
    
    All feedback items include citations to rubric anchors and student transcript spans.
    """
    try:
        composer = FeedbackComposer(style=request.style)
        
        feedback = composer.compose_feedback(
            rubric_id=request.rubric_id,
            overall_score=request.overall_score,
            structure_eval=request.structure_eval,
            questions_eval=request.questions_eval,
            reasoning_eval=request.reasoning_eval,
            summary_eval=request.summary_eval
        )
        
        return {"feedback": feedback}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error composing feedback: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)

