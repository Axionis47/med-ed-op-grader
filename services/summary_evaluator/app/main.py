"""
Summary Evaluator Service

This service handles:
1. Token counting for succinctness evaluation
2. Required element detection using patterns
3. Combined scoring (50% succinct + 50% elements)

Port: 8006
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
import sys

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.rubric import SummaryConfig
from shared.models.transcript import SegmentedTranscript
from shared.models.evaluation import SummaryEvaluation
from services.summary_evaluator.app.evaluator import SummaryEvaluator

app = FastAPI(
    title="Summary Evaluator Service",
    description="Evaluate summary section for succinctness and required elements",
    version="1.0.0"
)


# Request Models
class EvaluateSummaryRequest(BaseModel):
    """Request to evaluate summary."""
    rubric_id: str = Field(..., description="Rubric identifier")
    summary_config: SummaryConfig = Field(..., description="Summary configuration from rubric")
    segmented_transcript: SegmentedTranscript = Field(..., description="Segmented transcript")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "rubric_id": "stroke_v1",
                "summary_config": {
                    "anchor": "#R.summary",
                    "max_tokens": 80,
                    "min_tokens": 40,
                    "required_elements": [
                        {
                            "id": "E1",
                            "anchor": "#R.summary.E1",
                            "description": "Age and demographics",
                            "pattern": "\\d+.{0,20}(?:year|yo)",
                            "is_critical": True
                        }
                    ]
                },
                "segmented_transcript": {
                    "transcript_id": "test_001",
                    "sections": [],
                    "detected_order": []
                }
            }
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "summary_evaluator"
    }


@app.post("/evaluate/summary", response_model=SummaryEvaluation)
async def evaluate_summary(request: EvaluateSummaryRequest):
    """
    Evaluate summary section of the presentation.
    
    The evaluation process:
    1. Extract summary text from Summary section
    2. Count tokens using advanced tokenizer
    3. Compute succinctness score based on token count
    4. Detect required elements using pattern matching
    5. Compute elements score as ratio of matched to required
    6. Combine scores: 50% succinct + 50% elements
    
    Returns:
    - Combined score
    - Succinctness score
    - Elements score
    - Token count
    - Matched and missing elements
    - Violations and successes
    """
    try:
        evaluator = SummaryEvaluator(rubric_id=request.rubric_id)
        
        result = evaluator.evaluate(
            summary_config=request.summary_config,
            segmented_transcript=request.segmented_transcript
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to evaluate summary: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)

