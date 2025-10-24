"""Grading request and response models."""

from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field


class ComponentScores(BaseModel):
    """Scores for each grading component."""
    
    structure: float = Field(..., ge=0, le=1, description="Structure score")
    key_questions: float = Field(..., ge=0, le=1, description="Key questions score")
    reasoning: float = Field(..., ge=0, le=1, description="Reasoning score")
    summary: float = Field(..., ge=0, le=1, description="Summary score")
    communication: float = Field(0.0, ge=0, le=1, description="Communication score (0 for MVP)")


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown for a component."""
    
    score: float = Field(..., ge=0, le=1, description="Component score")
    weight: float = Field(..., ge=0, le=1, description="Component weight")
    contribution: float = Field(..., description="Contribution to overall score")


class FeedbackItem(BaseModel):
    """Individual feedback item."""
    
    type: Literal["violation", "success"] = Field(..., description="Feedback type")
    text: str = Field(..., description="Feedback text")
    citations: dict = Field(..., description="Citations (rubric and student)")


class FeedbackSection(BaseModel):
    """Feedback for a specific category."""
    
    category: str = Field(..., description="Category name")
    items: list[FeedbackItem] = Field(default_factory=list, description="Feedback items")


class GradingRequest(BaseModel):
    """Request to grade a student submission."""
    
    rubric_id: str = Field(..., description="Rubric identifier")
    rubric_version: str | None = Field(None, description="Rubric version (latest if not specified)")
    student_id: str = Field(..., description="Student identifier")
    submission: dict = Field(..., description="Student submission (oral_transcript, summary_text)")


class GradingResponse(BaseModel):
    """Complete grading response."""
    
    grading_id: str = Field(..., description="Unique grading identifier")
    rubric_id: str = Field(..., description="Rubric identifier")
    rubric_version: str = Field(..., description="Rubric version used")
    student_id: str = Field(..., description="Student identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Grading timestamp")
    
    overall_score: float = Field(..., ge=0, le=1, description="Overall score")
    component_scores: ComponentScores = Field(..., description="Component scores")
    score_breakdown: dict[str, ScoreBreakdown] = Field(..., description="Detailed score breakdown")
    
    feedback: dict = Field(..., description="Feedback structure")
    detailed_results: dict = Field(..., description="Detailed evaluation results")

