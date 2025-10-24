"""Shared Pydantic models for the grading system."""

from .citations import RubricCitation, StudentCitation, Citation
from .rubric import (
    Rubric,
    RubricWeights,
    StructureConfig,
    Penalty,
    KeyQuestion,
    KeyQuestionsPolicy,
    ReasoningConfig,
    ReasoningLink,
    SummaryConfig,
    SummaryElement,
    CommunicationConfig,
    CommunicationRule,
)
from .transcript import (
    Transcript,
    Utterance,
    TranscriptSection,
    SegmentedTranscript,
)
from .evaluation import (
    EvaluationResult,
    Violation,
    Success,
    StructureEvaluation,
    QuestionMatch,
    QuestionMatchingResult,
    ReasoningEvaluation,
    SummaryEvaluation,
)
from .grading import (
    GradingRequest,
    GradingResponse,
    ComponentScores,
    ScoreBreakdown,
    FeedbackSection,
    FeedbackItem,
)

__all__ = [
    # Citations
    "RubricCitation",
    "StudentCitation",
    "Citation",
    # Rubric
    "Rubric",
    "RubricWeights",
    "StructureConfig",
    "Penalty",
    "KeyQuestion",
    "KeyQuestionsPolicy",
    "ReasoningConfig",
    "ReasoningLink",
    "SummaryConfig",
    "SummaryElement",
    "CommunicationConfig",
    "CommunicationRule",
    # Transcript
    "Transcript",
    "Utterance",
    "TranscriptSection",
    "SegmentedTranscript",
    # Evaluation
    "EvaluationResult",
    "Violation",
    "Success",
    "StructureEvaluation",
    "QuestionMatch",
    "QuestionMatchingResult",
    "ReasoningEvaluation",
    "SummaryEvaluation",
    # Grading
    "GradingRequest",
    "GradingResponse",
    "ComponentScores",
    "ScoreBreakdown",
    "FeedbackSection",
    "FeedbackItem",
]

