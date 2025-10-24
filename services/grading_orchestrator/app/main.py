"""
Grading Orchestrator Service

This service coordinates the complete grading workflow:
1. Fetch rubric from Rubric Management
2. Parse and segment transcript
3. Evaluate all components (structure, questions, reasoning, summary)
4. Compute final weighted score
5. Generate cited feedback

Port: 8000
"""

from fastapi import FastAPI, HTTPException, Response
from pathlib import Path
import sys
import os
import httpx

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.grading import GradingRequest, GradingResponse
from shared.utils.metrics import (
    track_request, record_component_score, record_overall_score,
    set_service_health, get_metrics, get_metrics_content_type
)
from services.grading_orchestrator.app.orchestrator import GradingOrchestrator

app = FastAPI(
    title="Grading Orchestrator Service",
    description="Orchestrate complete grading workflow across all microservices",
    version="1.0.0"
)


# Initialize orchestrator with service URLs
# Use environment variables for flexibility, with defaults for Docker Compose
orchestrator = GradingOrchestrator(
    rubric_service_url=os.getenv("RUBRIC_SERVICE_URL", "http://rubric-management:8001"),
    transcript_service_url=os.getenv("TRANSCRIPT_SERVICE_URL", "http://transcript-processing:8002"),
    question_service_url=os.getenv("QUESTION_SERVICE_URL", "http://question-matching:8003"),
    structure_service_url=os.getenv("STRUCTURE_SERVICE_URL", "http://structure-evaluator:8004"),
    reasoning_service_url=os.getenv("REASONING_SERVICE_URL", "http://reasoning-evaluator:8005"),
    summary_service_url=os.getenv("SUMMARY_SERVICE_URL", "http://summary-evaluator:8006"),
    scoring_service_url=os.getenv("SCORING_SERVICE_URL", "http://scoring:8007"),
    feedback_service_url=os.getenv("FEEDBACK_SERVICE_URL", "http://feedback-composer:8008")
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    set_service_health("grading_orchestrator", True)
    return {
        "status": "healthy",
        "service": "grading_orchestrator"
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type()
    )


@app.post("/grade", response_model=GradingResponse)
async def grade_presentation(request: GradingRequest):
    """
    Grade a medical education oral presentation.
    
    This is the main endpoint that orchestrates the complete grading workflow:
    
    **Workflow Steps:**
    1. Fetch rubric from Rubric Management Service
    2. Parse and segment transcript using Transcript Processing Service
    3. Evaluate components in parallel:
       - Structure (LCS-based)
       - Key Questions (BM25 + embeddings)
       - Clinical Reasoning (pattern matching)
       - Summary (token counting + elements)
    4. Compute weighted final score using Scoring Service
    5. Generate cited feedback using Feedback Composer Service
    
    **Input:**
    - rubric_id: Identifier for the rubric to use
    - raw_text: Raw transcript text with timestamps and speakers
    - transcript_id: Identifier for this transcript
    
    **Output:**
    - overall_score: Weighted final score [0, 1]
    - component_scores: Individual scores for each component
    - score_breakdown: Detailed breakdown with contributions
    - feedback: Cited feedback with violations and successes
    
    **Example Request:**
    ```json
    {
      "rubric_id": "stroke_v1",
      "raw_text": "[00:05] Student: Tell me what brings you in today?\\n[00:08] Patient: I have weakness.",
      "transcript_id": "stroke_001"
    }
    ```
    """
    try:
        result = await orchestrator.grade(request)

        # Record metrics
        record_overall_score(result.overall_score)
        for component, score in result.component_scores.model_dump().items():
            record_component_score(component, score)

        return result
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Service error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to grade presentation: {str(e)}"
        )


@app.get("/services/status")
async def check_services_status():
    """
    Check the status of all dependent services.
    
    Returns the health status of each microservice.
    """
    import httpx
    
    services = {
        "rubric_management": os.getenv("RUBRIC_SERVICE_URL", "http://rubric-management:8001"),
        "transcript_processing": os.getenv("TRANSCRIPT_SERVICE_URL", "http://transcript-processing:8002"),
        "question_matching": os.getenv("QUESTION_SERVICE_URL", "http://question-matching:8003"),
        "structure_evaluator": os.getenv("STRUCTURE_SERVICE_URL", "http://structure-evaluator:8004"),
        "reasoning_evaluator": os.getenv("REASONING_SERVICE_URL", "http://reasoning-evaluator:8005"),
        "summary_evaluator": os.getenv("SUMMARY_SERVICE_URL", "http://summary-evaluator:8006"),
        "scoring": os.getenv("SCORING_SERVICE_URL", "http://scoring:8007"),
        "feedback_composer": os.getenv("FEEDBACK_SERVICE_URL", "http://feedback-composer:8008")
    }
    
    status = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in services.items():
            try:
                response = await client.get(f"{url}/health")
                status[name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": url
                }
            except Exception as e:
                status[name] = {
                    "status": "unreachable",
                    "url": url,
                    "error": str(e)
                }
    
    return {
        "orchestrator": "healthy",
        "services": status,
        "all_healthy": all(s["status"] == "healthy" for s in status.values())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

