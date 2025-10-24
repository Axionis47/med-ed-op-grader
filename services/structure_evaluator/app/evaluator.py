"""Structure evaluation logic."""

from pathlib import Path
import sys

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.rubric import StructureConfig, Penalty
from shared.models.transcript import SegmentedTranscript
from shared.models.evaluation import StructureEvaluation, Violation, Success
from shared.utils.lcs import longest_common_subsequence, get_lcs_elements


class StructureEvaluator:
    """Evaluates presentation structure using LCS algorithm."""
    
    def __init__(self, rubric_id: str):
        """
        Initialize evaluator.
        
        Args:
            rubric_id: Rubric identifier for citation generation
        """
        self.rubric_id = rubric_id
    
    def evaluate(
        self,
        structure_config: StructureConfig,
        segmented_transcript: SegmentedTranscript
    ) -> StructureEvaluation:
        """
        Evaluate structure of a presentation.
        
        Args:
            structure_config: Structure configuration from rubric
            segmented_transcript: Segmented transcript with detected sections
        
        Returns:
            StructureEvaluation with score and feedback
        """
        expected_order = structure_config.expected_order
        detected_order = segmented_transcript.detected_order
        
        # Compute LCS score
        lcs_length = longest_common_subsequence(detected_order, expected_order)
        lcs_score = lcs_length / len(expected_order) if expected_order else 1.0
        
        # Get LCS elements for success feedback
        lcs_elements = get_lcs_elements(detected_order, expected_order)
        
        # Detect violations and apply penalties
        violations = []
        successes = []
        penalties_applied = []
        total_penalty = 0.0
        
        # Check for specific penalties
        for penalty in structure_config.penalties:
            violation = self._check_penalty(
                penalty,
                detected_order,
                expected_order,
                segmented_transcript
            )
            if violation:
                violations.append(violation)
                penalties_applied.append({
                    'id': penalty.id,
                    'value': penalty.value,
                    'description': penalty.description
                })
                total_penalty += penalty.value
        
        # Generate success feedback for correct ordering
        if lcs_elements:
            success_text = f"Correctly ordered sections: {', '.join(lcs_elements)}"
            successes.append(Success(
                description=success_text,
                rubric_citations=[f"rubric://{self.rubric_id}{structure_config.anchor}"],
                student_citations=[]
            ))
        
        # Check for missing sections
        missing_sections = set(expected_order) - set(detected_order)
        if missing_sections:
            for section in missing_sections:
                # Check if there's a specific penalty for this missing section
                penalty_found = False
                for penalty in structure_config.penalties:
                    if f"missing_{section.lower()}" in penalty.id:
                        penalty_found = True
                        break
                
                if not penalty_found:
                    # Generic missing section violation
                    violations.append(Violation(
                        description=f"Missing {section} section",
                        rubric_citations=[f"rubric://{self.rubric_id}{structure_config.anchor}"],
                        student_citations=[],
                        severity="major"
                    ))
        
        # Check for out-of-order sections
        out_of_order = self._detect_out_of_order(detected_order, expected_order, lcs_elements)
        if out_of_order:
            for section1, section2 in out_of_order:
                # Check if there's a specific penalty for this swap
                penalty_found = False
                for penalty in structure_config.penalties:
                    if f"swap_{section2.lower()}_before_{section1.lower()}" in penalty.id:
                        penalty_found = True
                        break
                
                if not penalty_found:
                    violations.append(Violation(
                        description=f"{section2} appears before {section1} (expected order: {section1} → {section2})",
                        rubric_citations=[f"rubric://{self.rubric_id}{structure_config.anchor}"],
                        student_citations=[],
                        severity="minor"
                    ))
        
        # Compute final score
        final_score = max(0.0, min(1.0, lcs_score + total_penalty))
        
        return StructureEvaluation(
            score=final_score,
            lcs_score=lcs_score,
            penalties_applied=penalties_applied,
            detected_order=detected_order,
            expected_order=expected_order,
            violations=violations,
            successes=successes
        )
    
    def _check_penalty(
        self,
        penalty: Penalty,
        detected_order: list[str],
        expected_order: list[str],
        segmented_transcript: SegmentedTranscript
    ) -> Violation | None:
        """
        Check if a specific penalty applies.
        
        Args:
            penalty: Penalty definition
            detected_order: Detected section order
            expected_order: Expected section order
            segmented_transcript: Segmented transcript
        
        Returns:
            Violation if penalty applies, None otherwise
        """
        # Check for missing sections
        if "missing_" in penalty.id:
            section_name = penalty.id.replace("missing_", "").upper()
            if section_name not in detected_order:
                return Violation(
                    description=penalty.description,
                    rubric_citations=[f"rubric://{self.rubric_id}{penalty.anchor}"],
                    student_citations=[],
                    severity="major"
                )
        
        # Check for swapped sections
        if "swap_" in penalty.id:
            # Extract section names from penalty ID (e.g., "swap_ros_before_hpi")
            parts = penalty.id.replace("swap_", "").split("_before_")
            if len(parts) == 2:
                section1 = parts[1].upper()  # Should come first
                section2 = parts[0].upper()  # Should come second
                
                if section1 in detected_order and section2 in detected_order:
                    idx1 = detected_order.index(section1)
                    idx2 = detected_order.index(section2)
                    
                    if idx2 < idx1:  # section2 appears before section1
                        return Violation(
                            description=penalty.description,
                            rubric_citations=[f"rubric://{self.rubric_id}{penalty.anchor}"],
                            student_citations=[],
                            severity="major"
                        )
        
        return None
    
    def _detect_out_of_order(
        self,
        detected_order: list[str],
        expected_order: list[str],
        lcs_elements: list[str]
    ) -> list[tuple[str, str]]:
        """
        Detect pairs of sections that are out of order.
        
        Args:
            detected_order: Detected section order
            expected_order: Expected section order
            lcs_elements: Elements in the LCS
        
        Returns:
            List of (section1, section2) tuples where section2 should come after section1
        """
        out_of_order = []
        
        # Create expected order mapping
        expected_positions = {section: i for i, section in enumerate(expected_order)}
        
        # Check each pair of adjacent sections in detected order
        for i in range(len(detected_order) - 1):
            section1 = detected_order[i]
            section2 = detected_order[i + 1]
            
            # Skip if either section is not in expected order
            if section1 not in expected_positions or section2 not in expected_positions:
                continue
            
            # Check if they're in wrong order
            if expected_positions[section1] > expected_positions[section2]:
                out_of_order.append((section2, section1))  # (should be first, should be second)
        
        return out_of_order

