"""Feedback composition logic."""

from typing import Literal
from pathlib import Path
import sys

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.evaluation import (
    StructureEvaluation,
    QuestionMatchingResult,
    ReasoningEvaluation,
    SummaryEvaluation,
    Violation,
    Success
)
from shared.models.grading import FeedbackSection, FeedbackItem


class FeedbackComposer:
    """Composes natural language feedback from evaluation results."""
    
    def __init__(self, style: Literal["constructive", "detailed", "concise"] = "constructive"):
        """
        Initialize composer.
        
        Args:
            style: Feedback style
        """
        self.style = style
    
    def compose_feedback(
        self,
        rubric_id: str,
        overall_score: float,
        structure_eval: StructureEvaluation | None = None,
        questions_eval: QuestionMatchingResult | None = None,
        reasoning_eval: ReasoningEvaluation | None = None,
        summary_eval: SummaryEvaluation | None = None
    ) -> dict:
        """
        Compose complete feedback from evaluation results.
        
        Args:
            rubric_id: Rubric identifier
            overall_score: Overall score (0-1)
            structure_eval: Structure evaluation result
            questions_eval: Question matching result
            reasoning_eval: Reasoning evaluation result
            summary_eval: Summary evaluation result
        
        Returns:
            Feedback dictionary with overall summary and sections
        """
        # Generate overall summary
        overall_summary = self._generate_overall_summary(overall_score)
        
        # Compose feedback sections
        sections = []
        
        if structure_eval:
            sections.append(self._compose_structure_feedback(structure_eval))
        
        if questions_eval:
            sections.append(self._compose_questions_feedback(questions_eval))
        
        if reasoning_eval:
            sections.append(self._compose_reasoning_feedback(reasoning_eval))
        
        if summary_eval:
            sections.append(self._compose_summary_feedback(summary_eval))
        
        return {
            "overall_summary": overall_summary,
            "sections": [s.model_dump() for s in sections]
        }
    
    def _generate_overall_summary(self, overall_score: float) -> str:
        """Generate overall summary text."""
        percentage = int(overall_score * 100)
        
        if overall_score >= 0.9:
            quality = "Excellent work"
        elif overall_score >= 0.8:
            quality = "Strong performance"
        elif overall_score >= 0.7:
            quality = "Good effort"
        elif overall_score >= 0.6:
            quality = "Satisfactory"
        else:
            quality = "Needs improvement"
        
        return f"{quality}. You scored {percentage}% on this presentation."
    
    def _compose_structure_feedback(self, eval_result: StructureEvaluation) -> FeedbackSection:
        """Compose feedback for structure evaluation."""
        items = []
        
        # Add violations
        for violation in eval_result.violations:
            items.append(FeedbackItem(
                type="violation",
                text=violation.description,
                citations={
                    "rubric": violation.rubric_citations,
                    "student": violation.student_citations
                }
            ))
        
        # Add successes
        for success in eval_result.successes:
            items.append(FeedbackItem(
                type="success",
                text=success.description,
                citations={
                    "rubric": success.rubric_citations,
                    "student": success.student_citations
                }
            ))
        
        # Add general feedback if no specific items
        if not items:
            items.append(FeedbackItem(
                type="success",
                text="Your presentation structure was well-organized.",
                citations={
                    "rubric": [],
                    "student": []
                }
            ))
        
        return FeedbackSection(
            category="structure",
            items=items
        )
    
    def _compose_questions_feedback(self, eval_result: QuestionMatchingResult) -> FeedbackSection:
        """Compose feedback for question matching."""
        items = []
        
        # Add violations for unmatched questions
        for unmatched in eval_result.unmatched_questions:
            question_id = unmatched.get('id', 'unknown')
            label = unmatched.get('label', 'Unknown question')
            anchor = unmatched.get('anchor', '#Q.unknown')
            critical = unmatched.get('critical', False)
            
            severity = "critical" if critical else "major"
            text = f"You did not ask: {label}"
            
            items.append(FeedbackItem(
                type="violation",
                text=text,
                citations={
                    "rubric": [f"rubric://{eval_result.violations[0].rubric_citations[0].split('#')[0].replace('rubric://', '')}{anchor}"] if eval_result.violations else [],
                    "student": []
                }
            ))
        
        # Add successes for matched questions
        for match in eval_result.matches:
            text = f"Good job asking about: {match.matched_utterance.get('text', 'this topic')}"
            
            items.append(FeedbackItem(
                type="success",
                text=text,
                citations={
                    "rubric": [f"rubric://{match.question_anchor}"],
                    "student": [
                        f"student://oral#{match.matched_utterance.get('timestamp_start', '00:00')}–{match.matched_utterance.get('timestamp_end', '00:00')}"
                    ]
                }
            ))
        
        # Add violations from eval result
        for violation in eval_result.violations:
            items.append(FeedbackItem(
                type="violation",
                text=violation.description,
                citations={
                    "rubric": violation.rubric_citations,
                    "student": violation.student_citations
                }
            ))
        
        return FeedbackSection(
            category="key_questions",
            items=items
        )
    
    def _compose_reasoning_feedback(self, eval_result: ReasoningEvaluation) -> FeedbackSection:
        """Compose feedback for reasoning evaluation."""
        items = []
        
        # Add violations for missing links
        for missing in eval_result.missing_links:
            link_id = missing.get('id', 'unknown')
            description = missing.get('description', 'Unknown reasoning link')
            anchor = missing.get('anchor', '#R.reason.unknown')
            
            text = f"You did not demonstrate: {description}"
            
            items.append(FeedbackItem(
                type="violation",
                text=text,
                citations={
                    "rubric": [anchor],
                    "student": []
                }
            ))
        
        # Add successes for detected links
        for detected in eval_result.detected_links:
            link_id = detected.get('link_id', 'unknown')
            matched_text = detected.get('matched_text', '')
            timestamp_start = detected.get('timestamp_start', '00:00')
            timestamp_end = detected.get('timestamp_end', '00:00')
            anchor = detected.get('link_anchor', '#R.reason.unknown')
            
            text = f"Good clinical reasoning: \"{matched_text}\""
            
            items.append(FeedbackItem(
                type="success",
                text=text,
                citations={
                    "rubric": [anchor],
                    "student": [f"student://oral#{timestamp_start}–{timestamp_end}"]
                }
            ))
        
        # Add violations from eval result
        for violation in eval_result.violations:
            items.append(FeedbackItem(
                type="violation",
                text=violation.description,
                citations={
                    "rubric": violation.rubric_citations,
                    "student": violation.student_citations
                }
            ))
        
        return FeedbackSection(
            category="reasoning",
            items=items
        )
    
    def _compose_summary_feedback(self, eval_result: SummaryEvaluation) -> FeedbackSection:
        """Compose feedback for summary evaluation."""
        items = []
        
        # Add violations
        for violation in eval_result.violations:
            items.append(FeedbackItem(
                type="violation",
                text=violation.description,
                citations={
                    "rubric": violation.rubric_citations,
                    "student": violation.student_citations
                }
            ))
        
        # Add successes for matched elements
        for element_id in eval_result.matched_elements:
            text = f"Your summary included: {element_id.replace('_', ' ')}"
            
            items.append(FeedbackItem(
                type="success",
                text=text,
                citations={
                    "rubric": [],
                    "student": []
                }
            ))
        
        # Add successes from eval result
        for success in eval_result.successes:
            items.append(FeedbackItem(
                type="success",
                text=success.description,
                citations={
                    "rubric": success.rubric_citations,
                    "student": success.student_citations
                }
            ))
        
        return FeedbackSection(
            category="summary",
            items=items
        )

