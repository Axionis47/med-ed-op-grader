"""
Summary evaluation logic.

This module handles:
1. Token counting for succinctness
2. Required element detection
3. Combined scoring (50% succinct + 50% elements)
"""

import re
from typing import List, Dict, Optional
from pathlib import Path
import sys

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.rubric import SummaryConfig, SummaryElement
from shared.models.transcript import SegmentedTranscript
from shared.models.evaluation import SummaryEvaluation, Violation, Success
from shared.utils.tokenizer import count_tokens_advanced


class SummaryEvaluator:
    """
    Evaluate summary section of presentation.
    
    Evaluates:
    1. Succinctness (token count vs max_tokens)
    2. Required elements (pattern matching)
    3. Combined score
    """
    
    def __init__(self, rubric_id: str):
        """
        Initialize the evaluator.
        
        Args:
            rubric_id: Identifier for the rubric being used
        """
        self.rubric_id = rubric_id
    
    def _get_summary_text(self, segmented_transcript: SegmentedTranscript) -> str:
        """
        Extract summary text from transcript.
        
        Args:
            segmented_transcript: Segmented transcript
            
        Returns:
            Summary text (student utterances from Summary section)
        """
        for section in segmented_transcript.sections:
            if section.label == "Summary":
                student_utterances = [
                    u.text for u in section.utterances
                    if u.speaker == "student"
                ]
                return " ".join(student_utterances)
        return ""
    
    def _compute_succinct_score(
        self,
        token_count: int,
        max_tokens: int,
        min_tokens: int = 40
    ) -> float:
        """
        Compute succinctness score.
        
        Formula:
        - If token_count < min_tokens: score = token_count / min_tokens
        - If min_tokens <= token_count <= max_tokens: score = 1.0
        - If token_count > max_tokens: score = max(0, 1 - (token_count - max_tokens) / max_tokens)
        
        Args:
            token_count: Actual token count
            max_tokens: Maximum allowed tokens
            min_tokens: Minimum recommended tokens
            
        Returns:
            Succinctness score in [0, 1]
        """
        if token_count < min_tokens:
            # Too short
            return token_count / min_tokens
        elif token_count <= max_tokens:
            # Perfect range
            return 1.0
        else:
            # Too long - penalize
            excess = token_count - max_tokens
            penalty = excess / max_tokens
            return max(0.0, 1.0 - penalty)
    
    def _detect_element(
        self,
        element: SummaryElement,
        summary_text: str
    ) -> bool:
        """
        Detect if a required element is present in summary.
        
        Args:
            element: Required element to detect
            summary_text: Summary text to search
            
        Returns:
            True if element is detected, False otherwise
        """
        try:
            regex = re.compile(element.pattern, re.IGNORECASE)
            return bool(regex.search(summary_text))
        except re.error:
            # Invalid regex, return False
            return False
    
    def evaluate(
        self,
        summary_config: SummaryConfig,
        segmented_transcript: SegmentedTranscript
    ) -> SummaryEvaluation:
        """
        Evaluate summary section.
        
        Args:
            summary_config: Summary configuration from rubric
            segmented_transcript: Segmented transcript to evaluate
            
        Returns:
            SummaryEvaluation with scores and detected elements
        """
        # Extract summary text
        summary_text = self._get_summary_text(segmented_transcript)
        
        # Count tokens
        token_count = count_tokens_advanced(summary_text)
        
        # Compute succinctness score
        succinct_score = self._compute_succinct_score(
            token_count,
            summary_config.max_tokens,
            summary_config.min_tokens
        )
        
        # Detect required elements
        matched_elements = []
        missing_elements = []
        violations = []
        successes = []
        
        for element in summary_config.required_elements:
            if self._detect_element(element, summary_text):
                matched_elements.append(element.id)
                
                # Record success
                rubric_citation = f"rubric://{self.rubric_id}#{element.anchor}"
                successes.append(Success(
                    description=f"Included required element: {element.description}",
                    rubric_citations=[rubric_citation],
                    student_citations=[f"student://summary#tokens={token_count}"]
                ))
            else:
                missing_elements.append(element.id)
                
                # Record violation
                rubric_citation = f"rubric://{self.rubric_id}#{element.anchor}"
                violations.append(Violation(
                    description=f"Missing required element: {element.description}",
                    rubric_citations=[rubric_citation],
                    student_citations=[],
                    severity="major" if element.is_critical else "minor"
                ))
        
        # Compute elements score
        if len(summary_config.required_elements) > 0:
            elements_score = len(matched_elements) / len(summary_config.required_elements)
        else:
            elements_score = 1.0
        
        # Add violation for token count if needed
        if token_count > summary_config.max_tokens:
            rubric_citation = f"rubric://{self.rubric_id}#{summary_config.anchor}"
            violations.append(Violation(
                description=f"Summary too long: {token_count} tokens (max: {summary_config.max_tokens})",
                rubric_citations=[rubric_citation],
                student_citations=[f"student://summary#tokens={token_count}"],
                severity="minor"
            ))
        elif token_count < summary_config.min_tokens:
            rubric_citation = f"rubric://{self.rubric_id}#{summary_config.anchor}"
            violations.append(Violation(
                description=f"Summary too short: {token_count} tokens (min: {summary_config.min_tokens})",
                rubric_citations=[rubric_citation],
                student_citations=[f"student://summary#tokens={token_count}"],
                severity="minor"
            ))
        
        # Combined score: 50% succinct + 50% elements
        combined_score = 0.5 * succinct_score + 0.5 * elements_score
        
        return SummaryEvaluation(
            score=combined_score,
            violations=violations,
            successes=successes,
            token_count=token_count,
            max_tokens=summary_config.max_tokens,
            succinct_score=succinct_score,
            elements_score=elements_score,
            matched_elements=matched_elements,
            missing_elements=missing_elements
        )

