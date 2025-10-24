"""Transcript data models."""

from typing import Literal
from pydantic import BaseModel, Field


class Utterance(BaseModel):
    """Single utterance in a transcript."""
    
    speaker: Literal["student", "patient", "system"] = Field(..., description="Speaker identifier")
    text: str = Field(..., description="Utterance text")
    timestamp_start: str = Field(..., description="Start timestamp (MM:SS or HH:MM:SS)")
    timestamp_end: str = Field(..., description="End timestamp (MM:SS or HH:MM:SS)")
    
    def get_duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        def parse_timestamp(ts: str) -> float:
            parts = ts.split(':')
            if len(parts) == 2:  # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            else:
                raise ValueError(f"Invalid timestamp format: {ts}")
        
        start = parse_timestamp(self.timestamp_start)
        end = parse_timestamp(self.timestamp_end)
        return end - start


class TranscriptSection(BaseModel):
    """Section of a transcript (e.g., CC, HPI, ROS)."""
    
    label: str = Field(..., description="Section label (CC, HPI, ROS, PMH, SH, FH, Summary)")
    utterances: list[Utterance] = Field(default_factory=list, description="Utterances in this section")
    timestamp_start: str = Field(..., description="Section start timestamp")
    timestamp_end: str = Field(..., description="Section end timestamp")
    
    def get_student_utterances(self) -> list[Utterance]:
        """Get only student utterances."""
        return [u for u in self.utterances if u.speaker == "student"]
    
    def get_text(self) -> str:
        """Get concatenated text of all utterances."""
        return " ".join(u.text for u in self.utterances)


class Transcript(BaseModel):
    """Raw transcript."""
    
    transcript_id: str = Field(..., description="Unique transcript identifier")
    transcript_type: Literal["oral", "summary"] = Field(..., description="Type of transcript")
    utterances: list[Utterance] = Field(default_factory=list, description="All utterances")
    
    def get_student_utterances(self) -> list[Utterance]:
        """Get only student utterances."""
        return [u for u in self.utterances if u.speaker == "student"]


class SegmentedTranscript(BaseModel):
    """Transcript segmented into clinical sections."""
    
    transcript_id: str = Field(..., description="Unique transcript identifier")
    sections: list[TranscriptSection] = Field(default_factory=list, description="Segmented sections")
    detected_order: list[str] = Field(default_factory=list, description="Detected section order")
    
    def get_section(self, label: str) -> TranscriptSection | None:
        """Get section by label."""
        for section in self.sections:
            if section.label == label:
                return section
        return None
    
    def has_section(self, label: str) -> bool:
        """Check if section exists."""
        return self.get_section(label) is not None

