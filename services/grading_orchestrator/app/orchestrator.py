"""
Grading orchestration logic.

This module coordinates the complete grading workflow:
1. Fetch rubric
2. Parse and segment transcript
3. Evaluate all components (parallel where possible)
4. Compute final score
5. Generate feedback
"""

import asyncio
import httpx
from typing import Dict, Optional
from pathlib import Path
import sys

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.grading import GradingRequest, GradingResponse, ComponentScores, ScoreBreakdown


class GradingOrchestrator:
    """
    Orchestrates the complete grading workflow.
    
    Coordinates calls to all microservices to grade a presentation.
    """
    
    def __init__(
        self,
        rubric_service_url: str = "http://rubric-management:8001",
        transcript_service_url: str = "http://transcript-processing:8002",
        question_service_url: str = "http://question-matching:8003",
        structure_service_url: str = "http://structure-evaluator:8004",
        reasoning_service_url: str = "http://reasoning-evaluator:8005",
        summary_service_url: str = "http://summary-evaluator:8006",
        scoring_service_url: str = "http://scoring:8007",
        feedback_service_url: str = "http://feedback-composer:8008"
    ):
        """
        Initialize the orchestrator.
        
        Args:
            *_service_url: URLs for each microservice
        """
        self.rubric_service_url = rubric_service_url
        self.transcript_service_url = transcript_service_url
        self.question_service_url = question_service_url
        self.structure_service_url = structure_service_url
        self.reasoning_service_url = reasoning_service_url
        self.summary_service_url = summary_service_url
        self.scoring_service_url = scoring_service_url
        self.feedback_service_url = feedback_service_url
    
    async def _fetch_rubric(self, rubric_id: str, client: httpx.AsyncClient) -> Dict:
        """Fetch rubric from Rubric Management Service."""
        response = await client.get(f"{self.rubric_service_url}/rubrics/{rubric_id}")
        response.raise_for_status()
        return response.json()
    
    async def _process_transcript(
        self,
        raw_text: str,
        transcript_id: str,
        client: httpx.AsyncClient
    ) -> Dict:
        """Process transcript using Transcript Processing Service."""
        response = await client.post(
            f"{self.transcript_service_url}/transcripts/process",
            json={"raw_text": raw_text, "transcript_id": transcript_id}
        )
        response.raise_for_status()
        return response.json()
    
    async def _evaluate_structure(
        self,
        rubric_id: str,
        structure_config: Dict,
        segmented_transcript: Dict,
        client: httpx.AsyncClient
    ) -> Dict:
        """Evaluate structure using Structure Evaluator Service."""
        response = await client.post(
            f"{self.structure_service_url}/evaluate/structure",
            json={
                "rubric_id": rubric_id,
                "structure_config": structure_config,
                "segmented_transcript": segmented_transcript
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def _match_questions(
        self,
        key_questions: list,
        segmented_transcript: Dict,
        client: httpx.AsyncClient
    ) -> Dict:
        """Match questions using Question Matching Service."""
        response = await client.post(
            f"{self.question_service_url}/match/questions",
            json={
                "key_questions": key_questions,
                "segmented_transcript": segmented_transcript
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def _evaluate_reasoning(
        self,
        rubric_id: str,
        reasoning_links: list,
        segmented_transcript: Dict,
        client: httpx.AsyncClient
    ) -> Dict:
        """Evaluate reasoning using Reasoning Evaluator Service."""
        response = await client.post(
            f"{self.reasoning_service_url}/evaluate/reasoning",
            json={
                "rubric_id": rubric_id,
                "reasoning_links": reasoning_links,
                "segmented_transcript": segmented_transcript
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def _evaluate_summary(
        self,
        rubric_id: str,
        summary_config: Dict,
        segmented_transcript: Dict,
        client: httpx.AsyncClient
    ) -> Dict:
        """Evaluate summary using Summary Evaluator Service."""
        response = await client.post(
            f"{self.summary_service_url}/evaluate/summary",
            json={
                "rubric_id": rubric_id,
                "summary_config": summary_config,
                "segmented_transcript": segmented_transcript
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def _compute_score(
        self,
        rubric_weights: Dict,
        component_scores: Dict,
        client: httpx.AsyncClient
    ) -> Dict:
        """Compute final score using Scoring Service."""
        response = await client.post(
            f"{self.scoring_service_url}/score/compute",
            json={
                "rubric_weights": rubric_weights,
                "component_scores": component_scores
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def _compose_feedback(
        self,
        rubric_id: str,
        overall_score: float,
        structure_eval: Dict,
        question_eval: Dict,
        reasoning_eval: Dict,
        summary_eval: Dict,
        client: httpx.AsyncClient
    ) -> Dict:
        """Compose feedback using Feedback Composer Service."""
        response = await client.post(
            f"{self.feedback_service_url}/feedback/compose",
            json={
                "rubric_id": rubric_id,
                "overall_score": overall_score,
                "structure_eval": structure_eval,
                "question_eval": question_eval,
                "reasoning_eval": reasoning_eval,
                "summary_eval": summary_eval
            }
        )
        response.raise_for_status()
        return response.json()
    
    async def grade(self, request: GradingRequest) -> GradingResponse:
        """
        Execute complete grading workflow.
        
        Args:
            request: Grading request with rubric_id and raw_text
            
        Returns:
            GradingResponse with scores and feedback
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Fetch rubric
            rubric = await self._fetch_rubric(request.rubric_id, client)
            
            # Step 2: Process transcript
            segmented_transcript = await self._process_transcript(
                request.raw_text,
                request.transcript_id,
                client
            )
            
            # Step 3: Evaluate all components in parallel
            structure_task = self._evaluate_structure(
                request.rubric_id,
                rubric["structure"],
                segmented_transcript,
                client
            )
            
            question_task = self._match_questions(
                rubric["key_questions"],
                segmented_transcript,
                client
            )
            
            reasoning_task = self._evaluate_reasoning(
                request.rubric_id,
                rubric["reasoning"]["required_links"],
                segmented_transcript,
                client
            )
            
            summary_task = self._evaluate_summary(
                request.rubric_id,
                rubric["summary"],
                segmented_transcript,
                client
            )
            
            # Wait for all evaluations
            structure_eval, question_eval, reasoning_eval, summary_eval = await asyncio.gather(
                structure_task,
                question_task,
                reasoning_task,
                summary_task
            )
            
            # Step 4: Compute final score
            component_scores = {
                "structure": structure_eval["score"],
                "key_questions": question_eval["score"],
                "reasoning": reasoning_eval["score"],
                "summary": summary_eval["score"],
                "communication": 0.0  # Not evaluated yet
            }
            
            score_result = await self._compute_score(
                rubric["weights"],
                component_scores,
                client
            )
            
            # Step 5: Compose feedback
            feedback = await self._compose_feedback(
                request.rubric_id,
                score_result["overall_score"],
                structure_eval,
                question_eval,
                reasoning_eval,
                summary_eval,
                client
            )
            
            # Build response
            return GradingResponse(
                transcript_id=request.transcript_id,
                rubric_id=request.rubric_id,
                rubric_version=rubric["version"],
                overall_score=score_result["overall_score"],
                component_scores=ComponentScores(**component_scores),
                score_breakdown=ScoreBreakdown(**score_result["breakdown"]),
                feedback=feedback
            )

