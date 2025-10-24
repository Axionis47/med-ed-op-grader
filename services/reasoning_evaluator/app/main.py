"""
Reasoning Evaluator Service

This service handles:
1. Pattern-based detection of clinical reasoning links
2. Dual citation requirement (rubric + student)
3. Context extraction around matches

Port: 8005
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from pathlib import Path
import sys

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.rubric import ReasoningLink
from shared.models.transcript import SegmentedTranscript
from shared.models.evaluation import ReasoningEvaluation
from services.reasoning_evaluator.app.evaluator import ReasoningEvaluator

app = FastAPI(
    title="Reasoning Evaluator Service",
    description="Evaluate clinical reasoning using pattern matching",
    version="1.0.0"
)


# Request Models
class EvaluateReasoningRequest(BaseModel):
    """Request to evaluate reasoning."""
    rubric_id: str = Field(..., description="Rubric identifier")
    reasoning_links: List[ReasoningLink] = Field(..., description="Required reasoning links from rubric")
    segmented_transcript: SegmentedTranscript = Field(..., description="Segmented transcript")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "rubric_id": "stroke_v1",
                "reasoning_links": [
                    {
                        "id": "L1",
                        "anchor": "#R.reasoning.L1",
                        "description": "Link symptoms to stroke",
                        "pattern": "(?:sudden|acute).{0,50}(?:weakness|stroke)"
                    }
                ],
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
        "service": "reasoning_evaluator"
    }


@app.post("/evaluate/reasoning", response_model=ReasoningEvaluation)
async def evaluate_reasoning(request: EvaluateReasoningRequest):
    """
    Evaluate clinical reasoning in the transcript.
    
    The evaluation process:
    1. Extract student utterances (preferring Summary section)
    2. For each required reasoning link, search for pattern
    3. If found, create dual citation (rubric + student)
    4. Compute score as ratio of detected to required links
    
    Returns:
    - Score (detected_count / required_count)
    - Detected links with dual citations
    - Missing links
    - Violations and successes
    """
    try:
        evaluator = ReasoningEvaluator(rubric_id=request.rubric_id)
        
        result = evaluator.evaluate(
            reasoning_links=request.reasoning_links,
            segmented_transcript=request.segmented_transcript
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to evaluate reasoning: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)

