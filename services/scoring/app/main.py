"""Scoring Service - Main FastAPI application."""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from pathlib import Path
import sys

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.rubric import RubricWeights
from shared.models.grading import ComponentScores, ScoreBreakdown

app = FastAPI(
    title="Scoring Service",
    description="Applies formulas and computes final scores",
    version="1.0.0"
)


# Request/Response Models
class ComputeScoreRequest(BaseModel):
    """Request to compute weighted final score."""
    rubric_weights: RubricWeights
    component_scores: ComponentScores


class ComputeScoreResponse(BaseModel):
    """Response with overall score and breakdown."""
    overall_score: float = Field(..., ge=0, le=1, description="Overall weighted score")
    breakdown: dict[str, ScoreBreakdown] = Field(..., description="Detailed score breakdown")


# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "scoring"}


@app.post("/score/compute", response_model=ComputeScoreResponse)
async def compute_score(request: ComputeScoreRequest):
    """
    Compute weighted final score from component scores.
    
    Formula:
    overall = w_struct*structure + w_keys*keys + w_reason*reason + w_summary*summary
    
    Where weights must sum to 1.0.
    """
    try:
        weights = request.rubric_weights
        scores = request.component_scores
        
        # Compute weighted contributions
        breakdown = {}
        
        breakdown['structure'] = ScoreBreakdown(
            score=scores.structure,
            weight=weights.structure,
            contribution=weights.structure * scores.structure
        )
        
        breakdown['key_questions'] = ScoreBreakdown(
            score=scores.key_questions,
            weight=weights.key_questions,
            contribution=weights.key_questions * scores.key_questions
        )
        
        breakdown['reasoning'] = ScoreBreakdown(
            score=scores.reasoning,
            weight=weights.reasoning,
            contribution=weights.reasoning * scores.reasoning
        )
        
        breakdown['summary'] = ScoreBreakdown(
            score=scores.summary,
            weight=weights.summary,
            contribution=weights.summary * scores.summary
        )
        
        if weights.communication > 0:
            breakdown['communication'] = ScoreBreakdown(
                score=scores.communication,
                weight=weights.communication,
                contribution=weights.communication * scores.communication
            )
        
        # Compute overall score
        overall_score = sum(b.contribution for b in breakdown.values())
        
        # Clamp to [0, 1]
        overall_score = max(0.0, min(1.0, overall_score))
        
        return ComputeScoreResponse(
            overall_score=overall_score,
            breakdown=breakdown
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing score: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)

