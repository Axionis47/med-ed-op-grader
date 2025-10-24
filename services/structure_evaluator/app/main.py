"""Structure Evaluator Service - Main FastAPI application."""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from pathlib import Path
import sys

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.rubric import StructureConfig
from shared.models.transcript import SegmentedTranscript
from shared.models.evaluation import StructureEvaluation
from services.structure_evaluator.app.evaluator import StructureEvaluator

app = FastAPI(
    title="Structure Evaluator Service",
    description="Validates section order and completeness using LCS algorithm",
    version="1.0.0"
)


# Request/Response Models
class EvaluateStructureRequest(BaseModel):
    """Request to evaluate structure."""
    rubric_id: str
    structure_config: StructureConfig
    segmented_transcript: SegmentedTranscript


# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "structure_evaluator"}


@app.post("/evaluate/structure", response_model=StructureEvaluation)
async def evaluate_structure(request: EvaluateStructureRequest):
    """
    Evaluate the structure of a presentation.
    
    Uses Longest Common Subsequence (LCS) algorithm to compute base score,
    then applies penalties for specific violations.
    """
    try:
        evaluator = StructureEvaluator(rubric_id=request.rubric_id)
        result = evaluator.evaluate(
            structure_config=request.structure_config,
            segmented_transcript=request.segmented_transcript
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating structure: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)

