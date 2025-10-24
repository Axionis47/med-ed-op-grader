"""Citation models for rubric and student references."""

from typing import Literal, Union
from pydantic import BaseModel, Field, field_validator
import re


class RubricCitation(BaseModel):
    """Citation to a rubric anchor.
    
    Format: rubric://<rubric_id>#<anchor>
    Example: rubric://stroke_v1#Q.onset_time
    """
    
    rubric_id: str = Field(..., description="Rubric identifier")
    anchor: str = Field(..., description="Anchor within rubric (e.g., #Q.onset_time)")
    
    @field_validator('anchor')
    @classmethod
    def validate_anchor(cls, v: str) -> str:
        """Ensure anchor starts with #."""
        if not v.startswith('#'):
            raise ValueError("Anchor must start with #")
        return v
    
    def to_uri(self) -> str:
        """Convert to URI format."""
        return f"rubric://{self.rubric_id}{self.anchor}"
    
    @classmethod
    def from_uri(cls, uri: str) -> "RubricCitation":
        """Parse from URI format."""
        pattern = r"^rubric://([^#]+)(#.+)$"
        match = re.match(pattern, uri)
        if not match:
            raise ValueError(f"Invalid rubric citation URI: {uri}")
        return cls(rubric_id=match.group(1), anchor=match.group(2))
    
    def __str__(self) -> str:
        return self.to_uri()


class StudentCitation(BaseModel):
    """Citation to student transcript or summary.
    
    Formats:
    - Oral: student://oral#<timestamp_start>–<timestamp_end>
    - Summary: student://summary#tokens=<count>
    - Summary: student://summary#<timestamp_start>–<timestamp_end>
    """
    
    source: Literal["oral", "summary"] = Field(..., description="Source type")
    citation_type: Literal["timestamp", "tokens"] = Field(..., description="Citation type")
    
    # For timestamp citations
    timestamp_start: str | None = Field(None, description="Start timestamp (MM:SS or HH:MM:SS)")
    timestamp_end: str | None = Field(None, description="End timestamp (MM:SS or HH:MM:SS)")
    
    # For token count citations
    token_count: int | None = Field(None, description="Token count")
    
    @field_validator('timestamp_start', 'timestamp_end')
    @classmethod
    def validate_timestamp(cls, v: str | None) -> str | None:
        """Validate timestamp format."""
        if v is None:
            return v
        pattern = r"^(\d{1,2}:)?\d{1,2}:\d{2}$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid timestamp format: {v}. Expected MM:SS or HH:MM:SS")
        return v
    
    def to_uri(self) -> str:
        """Convert to URI format."""
        if self.citation_type == "timestamp":
            return f"student://{self.source}#{self.timestamp_start}–{self.timestamp_end}"
        else:
            return f"student://{self.source}#tokens={self.token_count}"
    
    @classmethod
    def from_uri(cls, uri: str) -> "StudentCitation":
        """Parse from URI format."""
        # Parse source
        source_match = re.match(r"^student://(oral|summary)#(.+)$", uri)
        if not source_match:
            raise ValueError(f"Invalid student citation URI: {uri}")
        
        source = source_match.group(1)
        fragment = source_match.group(2)
        
        # Check if it's a token count citation
        token_match = re.match(r"^tokens=(\d+)$", fragment)
        if token_match:
            return cls(
                source=source,
                citation_type="tokens",
                token_count=int(token_match.group(1))
            )
        
        # Otherwise, it's a timestamp citation
        timestamp_match = re.match(r"^(.+)–(.+)$", fragment)
        if not timestamp_match:
            raise ValueError(f"Invalid student citation fragment: {fragment}")
        
        return cls(
            source=source,
            citation_type="timestamp",
            timestamp_start=timestamp_match.group(1),
            timestamp_end=timestamp_match.group(2)
        )
    
    def __str__(self) -> str:
        return self.to_uri()


class Citation(BaseModel):
    """Combined citation model for feedback items."""
    
    rubric_citations: list[str] = Field(default_factory=list, description="List of rubric citation URIs")
    student_citations: list[str] = Field(default_factory=list, description="List of student citation URIs")
    
    def add_rubric_citation(self, citation: RubricCitation) -> None:
        """Add a rubric citation."""
        uri = citation.to_uri()
        if uri not in self.rubric_citations:
            self.rubric_citations.append(uri)
    
    def add_student_citation(self, citation: StudentCitation) -> None:
        """Add a student citation."""
        uri = citation.to_uri()
        if uri not in self.student_citations:
            self.student_citations.append(uri)
    
    def validate_citations(self) -> bool:
        """Ensure at least one rubric citation exists."""
        return len(self.rubric_citations) > 0

