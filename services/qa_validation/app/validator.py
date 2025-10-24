"""
QA validation logic for rubrics.

This module validates rubrics before approval to ensure:
1. Weights sum to 1.0
2. At least one critical question exists
3. All anchors are unique
4. Token bounds are reasonable (40-120)
5. No duplicate phrases in questions
"""

from typing import List, Dict, Set
from pathlib import Path
import sys

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.rubric import Rubric


class ValidationIssue:
    """Represents a validation issue."""
    
    def __init__(self, severity: str, category: str, message: str):
        """
        Initialize validation issue.
        
        Args:
            severity: "error" or "warning"
            category: Category of the issue
            message: Human-readable message
        """
        self.severity = severity
        self.category = category
        self.message = message
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message
        }


class RubricValidator:
    """Validates rubrics for quality assurance."""
    
    def __init__(self):
        """Initialize the validator."""
        self.issues: List[ValidationIssue] = []
    
    def _add_error(self, category: str, message: str):
        """Add an error issue."""
        self.issues.append(ValidationIssue("error", category, message))
    
    def _add_warning(self, category: str, message: str):
        """Add a warning issue."""
        self.issues.append(ValidationIssue("warning", category, message))
    
    def _validate_weights(self, rubric: Rubric) -> bool:
        """
        Validate that weights sum to 1.0.
        
        Args:
            rubric: Rubric to validate
            
        Returns:
            True if valid, False otherwise
        """
        weights = rubric.weights
        total = (
            weights.structure +
            weights.key_questions +
            weights.reasoning +
            weights.summary +
            weights.communication
        )
        
        # Allow small floating point error
        if abs(total - 1.0) > 0.001:
            self._add_error(
                "weights",
                f"Weights must sum to 1.0, got {total:.4f}"
            )
            return False
        
        # Check individual weights are non-negative
        if any(w < 0 for w in [
            weights.structure,
            weights.key_questions,
            weights.reasoning,
            weights.summary,
            weights.communication
        ]):
            self._add_error("weights", "All weights must be non-negative")
            return False
        
        return True
    
    def _validate_critical_questions(self, rubric: Rubric) -> bool:
        """
        Validate that at least one critical question exists.
        
        Args:
            rubric: Rubric to validate
            
        Returns:
            True if valid, False otherwise
        """
        critical_count = sum(1 for q in rubric.key_questions if q.is_critical)
        
        if critical_count == 0:
            self._add_error(
                "questions",
                "At least one critical question must be defined"
            )
            return False
        
        return True
    
    def _validate_unique_anchors(self, rubric: Rubric) -> bool:
        """
        Validate that all anchors are unique.
        
        Args:
            rubric: Rubric to validate
            
        Returns:
            True if valid, False otherwise
        """
        anchors: Set[str] = set()
        duplicates: List[str] = []
        
        # Collect all anchors
        all_anchors = [
            rubric.structure.anchor,
            rubric.summary.anchor,
            rubric.reasoning.anchor,
        ]
        
        # Add structure penalties
        for penalty in rubric.structure.penalties:
            all_anchors.append(penalty.anchor)
        
        # Add questions
        for question in rubric.key_questions:
            all_anchors.append(question.anchor)
        
        # Add reasoning links
        for link in rubric.reasoning.required_links:
            all_anchors.append(link.anchor)
        
        # Add summary elements
        for element in rubric.summary.required_elements:
            all_anchors.append(element.anchor)
        
        # Check for duplicates
        for anchor in all_anchors:
            if anchor in anchors:
                duplicates.append(anchor)
            anchors.add(anchor)
        
        if duplicates:
            self._add_error(
                "anchors",
                f"Duplicate anchors found: {', '.join(duplicates)}"
            )
            return False
        
        return True
    
    def _validate_token_bounds(self, rubric: Rubric) -> bool:
        """
        Validate that token bounds are reasonable.
        
        Args:
            rubric: Rubric to validate
            
        Returns:
            True if valid, False otherwise
        """
        min_tokens = rubric.summary.min_tokens
        max_tokens = rubric.summary.max_tokens
        
        # Check bounds
        if min_tokens < 20:
            self._add_warning(
                "summary",
                f"min_tokens ({min_tokens}) is very low, consider at least 40"
            )
        
        if max_tokens > 150:
            self._add_warning(
                "summary",
                f"max_tokens ({max_tokens}) is very high, consider at most 120"
            )
        
        if min_tokens >= max_tokens:
            self._add_error(
                "summary",
                f"min_tokens ({min_tokens}) must be less than max_tokens ({max_tokens})"
            )
            return False
        
        return True
    
    def _validate_duplicate_phrases(self, rubric: Rubric) -> bool:
        """
        Validate that no duplicate phrases exist across questions.
        
        Args:
            rubric: Rubric to validate
            
        Returns:
            True if valid, False otherwise
        """
        all_phrases: Set[str] = set()
        duplicates: List[str] = []
        
        for question in rubric.key_questions:
            for phrase in question.phrases:
                phrase_lower = phrase.lower().strip()
                if phrase_lower in all_phrases:
                    duplicates.append(phrase)
                all_phrases.add(phrase_lower)
        
        if duplicates:
            self._add_warning(
                "questions",
                f"Duplicate phrases found: {', '.join(duplicates[:5])}"
            )
        
        return True
    
    def _validate_question_phrases(self, rubric: Rubric) -> bool:
        """
        Validate that all questions have at least one phrase.
        
        Args:
            rubric: Rubric to validate
            
        Returns:
            True if valid, False otherwise
        """
        for question in rubric.key_questions:
            if not question.phrases:
                self._add_error(
                    "questions",
                    f"Question {question.id} has no phrases defined"
                )
                return False
        
        return True
    
    def validate(self, rubric: Rubric) -> Dict:
        """
        Validate a rubric.
        
        Args:
            rubric: Rubric to validate
            
        Returns:
            Validation result with is_valid flag and issues
        """
        self.issues = []
        
        # Run all validations
        self._validate_weights(rubric)
        self._validate_critical_questions(rubric)
        self._validate_unique_anchors(rubric)
        self._validate_token_bounds(rubric)
        self._validate_duplicate_phrases(rubric)
        self._validate_question_phrases(rubric)
        
        # Check if any errors exist
        errors = [issue for issue in self.issues if issue.severity == "error"]
        warnings = [issue for issue in self.issues if issue.severity == "warning"]
        
        return {
            "is_valid": len(errors) == 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": [issue.to_dict() for issue in errors],
            "warnings": [issue.to_dict() for issue in warnings],
            "all_issues": [issue.to_dict() for issue in self.issues]
        }

