"""
Reasoning evaluation logic using pattern matching.

This module handles:
1. Pattern-based detection of clinical reasoning links
2. Dual citation requirement (rubric + student)
3. Context extraction around matches
"""

import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.rubric import ReasoningLink
from shared.models.transcript import SegmentedTranscript, Utterance
from shared.models.evaluation import ReasoningEvaluation, Violation, Success


class ReasoningEvaluator:
    """
    Evaluate clinical reasoning using pattern matching.
    
    Detects reasoning links in student transcripts using regex patterns
    and ensures dual citations (rubric + student).
    """
    
    def __init__(self, rubric_id: str):
        """
        Initialize the evaluator.
        
        Args:
            rubric_id: Identifier for the rubric being used
        """
        self.rubric_id = rubric_id
    
    def _find_pattern_in_utterances(
        self,
        pattern: str,
        utterances: List[Utterance],
        context_window: int = 2
    ) -> Optional[Tuple[Utterance, str]]:
        """
        Find a pattern in utterances and return the matching utterance.
        
        Args:
            pattern: Regex pattern to search for
            utterances: List of utterances to search
            context_window: Number of utterances before/after to include in context
            
        Returns:
            Tuple of (matching utterance, context) or None if not found
        """
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            # Invalid regex, return None
            return None
        
        for i, utterance in enumerate(utterances):
            if regex.search(utterance.text):
                # Found a match
                # Extract context (surrounding utterances)
                start_idx = max(0, i - context_window)
                end_idx = min(len(utterances), i + context_window + 1)
                context_utterances = utterances[start_idx:end_idx]
                context = " ".join([u.text for u in context_utterances])
                
                return (utterance, context)
        
        return None
    
    def _get_student_utterances(
        self,
        segmented_transcript: SegmentedTranscript
    ) -> List[Utterance]:
        """
        Extract all student utterances from transcript.
        
        Args:
            segmented_transcript: Segmented transcript
            
        Returns:
            List of student utterances
        """
        student_utterances = []
        for section in segmented_transcript.sections:
            for utterance in section.utterances:
                if utterance.speaker == "student":
                    student_utterances.append(utterance)
        return student_utterances
    
    def _get_summary_utterances(
        self,
        segmented_transcript: SegmentedTranscript
    ) -> List[Utterance]:
        """
        Extract utterances from the Summary section.
        
        Args:
            segmented_transcript: Segmented transcript
            
        Returns:
            List of summary utterances
        """
        for section in segmented_transcript.sections:
            if section.label == "Summary":
                return [u for u in section.utterances if u.speaker == "student"]
        return []
    
    def evaluate(
        self,
        reasoning_links: List[ReasoningLink],
        segmented_transcript: SegmentedTranscript
    ) -> ReasoningEvaluation:
        """
        Evaluate clinical reasoning in the transcript.
        
        Args:
            reasoning_links: Required reasoning links from rubric
            segmented_transcript: Segmented transcript to evaluate
            
        Returns:
            ReasoningEvaluation with detected/missing links and score
        """
        # Get student utterances (prefer summary, but include all)
        summary_utterances = self._get_summary_utterances(segmented_transcript)
        all_student_utterances = self._get_student_utterances(segmented_transcript)
        
        # Prefer summary for reasoning, but fall back to all utterances
        search_utterances = summary_utterances if summary_utterances else all_student_utterances
        
        detected_links = []
        missing_links = []
        violations = []
        successes = []
        
        for link in reasoning_links:
            # Try to find the pattern
            match_result = self._find_pattern_in_utterances(
                link.pattern,
                search_utterances
            )
            
            if match_result:
                utterance, context = match_result
                
                # Create dual citation
                rubric_citation = f"rubric://{self.rubric_id}#{link.anchor}"
                student_citation = f"student://oral#{utterance.timestamp_start}–{utterance.timestamp_end}"
                
                # Record detected link
                detected_links.append({
                    "link_id": link.id,
                    "anchor": link.anchor,
                    "description": link.description,
                    "rubric_citation": rubric_citation,
                    "student_citation": student_citation,
                    "context": context[:200]  # Limit context length
                })
                
                # Record success
                successes.append(Success(
                    description=f"Demonstrated reasoning: {link.description}",
                    rubric_citations=[rubric_citation],
                    student_citations=[student_citation]
                ))
            else:
                # Link not found
                rubric_citation = f"rubric://{self.rubric_id}#{link.anchor}"
                
                missing_links.append({
                    "link_id": link.id,
                    "anchor": link.anchor,
                    "description": link.description,
                    "rubric_citation": rubric_citation
                })
                
                # Record violation
                violations.append(Violation(
                    description=f"Missing clinical reasoning: {link.description}",
                    rubric_citations=[rubric_citation],
                    student_citations=[],
                    severity="major"
                ))
        
        # Compute score
        required_count = len(reasoning_links)
        detected_count = len(detected_links)
        
        if required_count > 0:
            score = detected_count / required_count
        else:
            score = 1.0  # No reasoning required
        
        return ReasoningEvaluation(
            score=score,
            violations=violations,
            successes=successes,
            detected_links=detected_links,
            missing_links=missing_links,
            required_count=required_count,
            detected_count=detected_count
        )

