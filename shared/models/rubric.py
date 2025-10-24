"""Rubric data models."""

from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class RubricWeights(BaseModel):
    """Weights for each grading category."""
    
    structure: float = Field(..., ge=0, le=1, description="Weight for structure evaluation")
    key_questions: float = Field(..., ge=0, le=1, description="Weight for key questions")
    reasoning: float = Field(..., ge=0, le=1, description="Weight for clinical reasoning")
    summary: float = Field(..., ge=0, le=1, description="Weight for summary evaluation")
    communication: float = Field(0.0, ge=0, le=1, description="Weight for communication (0 for MVP)")
    
    @field_validator('communication')
    @classmethod
    def validate_weights_sum(cls, v: float, info) -> float:
        """Validate that all weights sum to 1.0."""
        if info.data:
            total = (
                info.data.get('structure', 0) +
                info.data.get('key_questions', 0) +
                info.data.get('reasoning', 0) +
                info.data.get('summary', 0) +
                v
            )
            if abs(total - 1.0) > 0.001:  # Allow small floating point errors
                raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


class Penalty(BaseModel):
    """Penalty definition for structure violations."""
    
    id: str = Field(..., description="Unique penalty identifier")
    anchor: str = Field(..., description="Rubric anchor for this penalty")
    description: str = Field(..., description="Human-readable description")
    value: float = Field(..., le=0, description="Penalty value (negative)")
    
    @field_validator('anchor')
    @classmethod
    def validate_anchor(cls, v: str) -> str:
        """Ensure anchor starts with #."""
        if not v.startswith('#'):
            raise ValueError("Anchor must start with #")
        return v


class StructureConfig(BaseModel):
    """Configuration for structure evaluation."""
    
    anchor: str = Field(..., description="Base anchor for structure category")
    expected_order: list[str] = Field(..., description="Expected section order")
    penalties: list[Penalty] = Field(default_factory=list, description="Penalty definitions")
    
    @field_validator('anchor')
    @classmethod
    def validate_anchor(cls, v: str) -> str:
        """Ensure anchor starts with #."""
        if not v.startswith('#'):
            raise ValueError("Anchor must start with #")
        return v


class KeyQuestion(BaseModel):
    """Definition of a key question to be asked."""
    
    id: str = Field(..., description="Unique question identifier")
    anchor: str = Field(..., description="Rubric anchor for this question")
    label: str = Field(..., description="Human-readable question label")
    critical: bool = Field(..., description="Whether this is a critical question")
    phrases: list[str] = Field(..., description="Phrases that match this question")
    
    @field_validator('anchor')
    @classmethod
    def validate_anchor(cls, v: str) -> str:
        """Ensure anchor starts with #."""
        if not v.startswith('#'):
            raise ValueError("Anchor must start with #")
        return v
    
    @field_validator('phrases')
    @classmethod
    def validate_phrases(cls, v: list[str]) -> list[str]:
        """Ensure at least one phrase exists."""
        if not v:
            raise ValueError("At least one phrase must be provided")
        return v


class KeyQuestionsPolicy(BaseModel):
    """Policy for key questions evaluation."""
    
    anchor: str = Field(..., description="Base anchor for key questions category")
    critical_weight: float = Field(2.0, gt=0, description="Weight for critical questions")
    noncritical_weight: float = Field(1.0, gt=0, description="Weight for non-critical questions")
    coverage_threshold: float = Field(0.7, ge=0, le=1, description="Minimum coverage threshold")
    
    @field_validator('anchor')
    @classmethod
    def validate_anchor(cls, v: str) -> str:
        """Ensure anchor starts with #."""
        if not v.startswith('#'):
            raise ValueError("Anchor must start with #")
        return v


class ReasoningLink(BaseModel):
    """Required clinical reasoning link."""
    
    id: str = Field(..., description="Unique link identifier")
    anchor: str = Field(..., description="Rubric anchor for this link")
    description: str = Field(..., description="Human-readable description")
    pattern: str = Field(..., description="Regex pattern to detect this link")
    
    @field_validator('anchor')
    @classmethod
    def validate_anchor(cls, v: str) -> str:
        """Ensure anchor starts with #."""
        if not v.startswith('#'):
            raise ValueError("Anchor must start with #")
        return v


class ReasoningConfig(BaseModel):
    """Configuration for clinical reasoning evaluation."""
    
    anchor: str = Field(..., description="Base anchor for reasoning category")
    required_links: list[ReasoningLink] = Field(default_factory=list, description="Required reasoning links")
    major_gap_penalty: float = Field(-0.5, le=0, description="Penalty for major reasoning gaps")
    
    @field_validator('anchor')
    @classmethod
    def validate_anchor(cls, v: str) -> str:
        """Ensure anchor starts with #."""
        if not v.startswith('#'):
            raise ValueError("Anchor must start with #")
        return v


class SummaryElement(BaseModel):
    """Required element in summary."""
    
    id: str = Field(..., description="Unique element identifier")
    anchor: str = Field(..., description="Rubric anchor for this element")
    description: str = Field(..., description="Human-readable description")
    pattern: str | None = Field(None, description="Optional regex pattern to detect this element")
    
    @field_validator('anchor')
    @classmethod
    def validate_anchor(cls, v: str) -> str:
        """Ensure anchor starts with #."""
        if not v.startswith('#'):
            raise ValueError("Anchor must start with #")
        return v


class SummaryConfig(BaseModel):
    """Configuration for summary evaluation."""
    
    anchor: str = Field(..., description="Base anchor for summary category")
    max_tokens: int = Field(..., ge=40, le=120, description="Maximum allowed tokens")
    overflow_divisor: int = Field(20, gt=0, description="Divisor for overflow penalty")
    required_elements: list[SummaryElement] = Field(default_factory=list, description="Required elements")
    
    @field_validator('anchor')
    @classmethod
    def validate_anchor(cls, v: str) -> str:
        """Ensure anchor starts with #."""
        if not v.startswith('#'):
            raise ValueError("Anchor must start with #")
        return v


class CommunicationRule(BaseModel):
    """Communication evaluation rule."""
    
    id: str = Field(..., description="Unique rule identifier")
    anchor: str = Field(..., description="Rubric anchor for this rule")
    description: str = Field(..., description="Human-readable description")
    
    @field_validator('anchor')
    @classmethod
    def validate_anchor(cls, v: str) -> str:
        """Ensure anchor starts with #."""
        if not v.startswith('#'):
            raise ValueError("Anchor must start with #")
        return v


class CommunicationConfig(BaseModel):
    """Configuration for communication evaluation."""
    
    anchor: str = Field(..., description="Base anchor for communication category")
    weight: float = Field(0.0, ge=0, le=1, description="Weight (0 for MVP)")
    rules: list[CommunicationRule] = Field(default_factory=list, description="Communication rules")
    
    @field_validator('anchor')
    @classmethod
    def validate_anchor(cls, v: str) -> str:
        """Ensure anchor starts with #."""
        if not v.startswith('#'):
            raise ValueError("Anchor must start with #")
        return v


class Rubric(BaseModel):
    """Complete rubric definition."""
    
    rubric_id: str = Field(..., description="Unique rubric identifier")
    version: str = Field(..., description="Semantic version (e.g., 1.0.0)")
    status: Literal["draft", "approved", "archived"] = Field("draft", description="Rubric status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    weights: RubricWeights = Field(..., description="Category weights")
    structure: StructureConfig = Field(..., description="Structure evaluation config")
    key_questions: list[KeyQuestion] = Field(..., description="Key questions to evaluate")
    key_questions_policy: KeyQuestionsPolicy = Field(..., description="Key questions policy")
    reasoning: ReasoningConfig = Field(..., description="Reasoning evaluation config")
    summary: SummaryConfig = Field(..., description="Summary evaluation config")
    communication: CommunicationConfig = Field(..., description="Communication evaluation config")
    
    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate semantic version format."""
        import re
        pattern = r"^\d+\.\d+\.\d+$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid semantic version: {v}. Expected format: X.Y.Z")
        return v
    
    def get_all_anchors(self) -> set[str]:
        """Get all anchors defined in this rubric."""
        anchors = {
            self.structure.anchor,
            self.key_questions_policy.anchor,
            self.reasoning.anchor,
            self.summary.anchor,
            self.communication.anchor,
        }
        
        # Add penalty anchors
        for penalty in self.structure.penalties:
            anchors.add(penalty.anchor)
        
        # Add question anchors
        for question in self.key_questions:
            anchors.add(question.anchor)
        
        # Add reasoning link anchors
        for link in self.reasoning.required_links:
            anchors.add(link.anchor)
        
        # Add summary element anchors
        for element in self.summary.required_elements:
            anchors.add(element.anchor)
        
        # Add communication rule anchors
        for rule in self.communication.rules:
            anchors.add(rule.anchor)
        
        return anchors
    
    def validate_unique_anchors(self) -> bool:
        """Validate that all anchors are unique."""
        anchors = []
        
        # Collect all anchors
        anchors.append(self.structure.anchor)
        anchors.extend([p.anchor for p in self.structure.penalties])
        anchors.extend([q.anchor for q in self.key_questions])
        anchors.append(self.key_questions_policy.anchor)
        anchors.extend([l.anchor for l in self.reasoning.required_links])
        anchors.append(self.reasoning.anchor)
        anchors.extend([e.anchor for e in self.summary.required_elements])
        anchors.append(self.summary.anchor)
        anchors.extend([r.anchor for r in self.communication.rules])
        anchors.append(self.communication.anchor)
        
        return len(anchors) == len(set(anchors))

