#!/usr/bin/env python3
"""
Simple test script to demonstrate the grading system.

This script shows how the services work together to evaluate a presentation.
"""

import json
from pathlib import Path
import sys

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent))

from shared.models.rubric import Rubric, StructureConfig
from shared.models.transcript import SegmentedTranscript, TranscriptSection, Utterance
from shared.models.grading import ComponentScores
from services.structure_evaluator.app.evaluator import StructureEvaluator
from services.feedback_composer.app.composer import FeedbackComposer


def load_rubric(rubric_path: str) -> Rubric:
    """Load a rubric from JSON file."""
    with open(rubric_path, 'r') as f:
        data = json.load(f)
    return Rubric(**data)


def create_sample_transcript() -> SegmentedTranscript:
    """Create a sample segmented transcript for testing."""
    sections = [
        TranscriptSection(
            label="CC",
            utterances=[
                Utterance(
                    speaker="student",
                    text="So tell me what brings you in today?",
                    timestamp_start="00:05",
                    timestamp_end="00:08"
                ),
                Utterance(
                    speaker="patient",
                    text="I have sudden weakness on my left side.",
                    timestamp_start="00:08",
                    timestamp_end="00:12"
                )
            ],
            timestamp_start="00:05",
            timestamp_end="00:12"
        ),
        TranscriptSection(
            label="HPI",
            utterances=[
                Utterance(
                    speaker="student",
                    text="When did you first notice the weakness?",
                    timestamp_start="00:15",
                    timestamp_end="00:18"
                ),
                Utterance(
                    speaker="patient",
                    text="About 2 hours ago.",
                    timestamp_start="00:18",
                    timestamp_end="00:20"
                )
            ],
            timestamp_start="00:15",
            timestamp_end="00:20"
        ),
        TranscriptSection(
            label="PMH",
            utterances=[
                Utterance(
                    speaker="student",
                    text="Do you have any medical history?",
                    timestamp_start="00:25",
                    timestamp_end="00:28"
                )
            ],
            timestamp_start="00:25",
            timestamp_end="00:28"
        ),
        TranscriptSection(
            label="ROS",
            utterances=[
                Utterance(
                    speaker="student",
                    text="Any other symptoms?",
                    timestamp_start="00:30",
                    timestamp_end="00:32"
                )
            ],
            timestamp_start="00:30",
            timestamp_end="00:32"
        )
    ]
    
    # Note: ROS comes after PMH (out of order), and missing SH, FH, Summary
    detected_order = ["CC", "HPI", "PMH", "ROS"]
    
    return SegmentedTranscript(
        transcript_id="test_001",
        sections=sections,
        detected_order=detected_order
    )


def main():
    """Run the test demonstration."""
    print("=" * 80)
    print("Medical Education Oral Presentation Grading System - Test Demo")
    print("=" * 80)
    print()
    
    # Load stroke rubric
    print("1. Loading stroke_v1 rubric...")
    rubric = load_rubric("data/rubrics/examples/stroke_v1.json")
    print(f"   ✓ Loaded rubric: {rubric.rubric_id} v{rubric.version}")
    print(f"   ✓ Status: {rubric.status}")
    print(f"   ✓ Weights: Structure={rubric.weights.structure}, "
          f"Questions={rubric.weights.key_questions}, "
          f"Reasoning={rubric.weights.reasoning}, "
          f"Summary={rubric.weights.summary}")
    print()
    
    # Create sample transcript
    print("2. Creating sample transcript...")
    transcript = create_sample_transcript()
    print(f"   ✓ Transcript ID: {transcript.transcript_id}")
    print(f"   ✓ Detected sections: {', '.join(transcript.detected_order)}")
    print(f"   ✓ Expected sections: {', '.join(rubric.structure.expected_order)}")
    print()
    
    # Evaluate structure
    print("3. Evaluating structure...")
    evaluator = StructureEvaluator(rubric_id=rubric.rubric_id)
    structure_result = evaluator.evaluate(
        structure_config=rubric.structure,
        segmented_transcript=transcript
    )
    print(f"   ✓ Structure score: {structure_result.score:.2f}")
    print(f"   ✓ LCS score: {structure_result.lcs_score:.2f}")
    print(f"   ✓ Penalties applied: {len(structure_result.penalties_applied)}")
    print(f"   ✓ Violations: {len(structure_result.violations)}")
    print(f"   ✓ Successes: {len(structure_result.successes)}")
    print()
    
    # Show violations
    if structure_result.violations:
        print("   Violations detected:")
        for i, violation in enumerate(structure_result.violations, 1):
            print(f"   {i}. [{violation.severity.upper()}] {violation.description}")
            print(f"      Citations: {', '.join(violation.rubric_citations)}")
        print()
    
    # Show successes
    if structure_result.successes:
        print("   Successes:")
        for i, success in enumerate(structure_result.successes, 1):
            print(f"   {i}. {success.description}")
        print()
    
    # Compute overall score (simplified - only structure for this demo)
    print("4. Computing overall score...")
    # For demo, we'll use structure score as overall (normally would include all components)
    component_scores = ComponentScores(
        structure=structure_result.score,
        key_questions=0.0,  # Not evaluated in this demo
        reasoning=0.0,      # Not evaluated in this demo
        summary=0.0         # Not evaluated in this demo
    )
    
    # Simplified overall score (just structure for demo)
    overall_score = rubric.weights.structure * structure_result.score
    print(f"   ✓ Overall score: {overall_score:.2f} (structure only)")
    print()
    
    # Compose feedback
    print("5. Composing feedback...")
    composer = FeedbackComposer(style="constructive")
    feedback = composer.compose_feedback(
        rubric_id=rubric.rubric_id,
        overall_score=overall_score,
        structure_eval=structure_result
    )
    
    print(f"   ✓ Overall summary: {feedback['overall_summary']}")
    print()
    
    print("   Detailed feedback:")
    for section in feedback['sections']:
        print(f"\n   Category: {section['category'].upper()}")
        for item in section['items']:
            icon = "✓" if item['type'] == 'success' else "✗"
            print(f"   {icon} {item['text']}")
            if item['citations']['rubric']:
                print(f"      Rubric: {', '.join(item['citations']['rubric'])}")
            if item['citations']['student']:
                print(f"      Student: {', '.join(item['citations']['student'])}")
    
    print()
    print("=" * 80)
    print("Demo complete!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Start services with: docker-compose up --build")
    print("2. Access API docs at: http://localhost:8001/docs (and other ports)")
    print("3. See SYSTEM_GUIDE.md for complete documentation")
    print()


if __name__ == "__main__":
    main()

