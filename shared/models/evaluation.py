"""Evaluation result models."""

from typing import Literal
from pydantic import BaseModel, Field
from .citations import Citation


class Violation(BaseModel):
    """Represents a grading violation."""
    
    description: str = Field(..., description="Human-readable description of the violation")
    rubric_citations: list[str] = Field(..., description="Rubric citation URIs")
    student_citations: list[str] = Field(default_factory=list, description="Student citation URIs")
    severity: Literal["critical", "major", "minor"] = Field(..., description="Violation severity")
    
    def validate_citations(self) -> bool:
        """Ensure at least one rubric citation exists."""
        return len(self.rubric_citations) > 0


class Success(BaseModel):
    """Represents a successful grading criterion."""
    
    description: str = Field(..., description="Human-readable description of the success")
    rubric_citations: list[str] = Field(..., description="Rubric citation URIs")
    student_citations: list[str] = Field(default_factory=list, description="Student citation URIs")
    
    def validate_citations(self) -> bool:
        """Ensure at least one rubric citation exists."""
        return len(self.rubric_citations) > 0


class EvaluationResult(BaseModel):
    """Base evaluation result structure."""
    
    score: float = Field(..., ge=0, le=1, description="Score in range [0, 1]")
    violations: list[Violation] = Field(default_factory=list, description="List of violations")
    successes: list[Success] = Field(default_factory=list, description="List of successes")


class StructureEvaluation(EvaluationResult):
    """Structure evaluation result."""
    
    lcs_score: float = Field(..., ge=0, le=1, description="LCS-based score")
    penalties_applied: list[dict] = Field(default_factory=list, description="Applied penalties")
    detected_order: list[str] = Field(default_factory=list, description="Detected section order")
    expected_order: list[str] = Field(default_factory=list, description="Expected section order")


class QuestionMatch(BaseModel):
    """Represents a matched question."""

    question_id: str = Field(..., description="Question identifier")
    question_anchor: str = Field(..., description="Question anchor")
    matched_phrase: str = Field(..., description="Phrase that matched")
    confidence: float = Field(..., ge=0, le=1, description="Match confidence score")
    student_citation: str = Field(..., description="Student citation URI")
    is_critical: bool = Field(..., description="Whether question is critical")
    weight: float = Field(..., description="Question weight (2.0 for critical, 1.0 for non-critical)")


class QuestionMatchingResult(EvaluationResult):
    """Question matching evaluation result."""

    matches: list[QuestionMatch] = Field(default_factory=list, description="Matched questions")
    unmatched_questions: list[str] = Field(default_factory=list, description="Unmatched question IDs")
    total_weight: float = Field(..., description="Total weight of all questions")
    matched_weight: float = Field(..., description="Weight of matched questions")


class ReasoningEvaluation(EvaluationResult):
    """Reasoning evaluation result."""
    
    detected_links: list[dict] = Field(default_factory=list, description="Detected reasoning links")
    missing_links: list[dict] = Field(default_factory=list, description="Missing reasoning links")
    required_count: int = Field(..., description="Number of required links")
    detected_count: int = Field(..., description="Number of detected links")


class SummaryEvaluation(EvaluationResult):
    """Summary evaluation result."""
    
    token_count: int = Field(..., description="Actual token count")
    max_tokens: int = Field(..., description="Maximum allowed tokens")
    succinct_score: float = Field(..., ge=0, le=1, description="Succinctness score")
    elements_score: float = Field(..., ge=0, le=1, description="Required elements score")
    matched_elements: list[str] = Field(default_factory=list, description="Matched element IDs")
    missing_elements: list[str] = Field(default_factory=list, description="Missing element IDs")

