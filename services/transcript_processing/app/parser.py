"""
Transcript parsing and segmentation logic.

This module handles:
1. Parsing raw transcript text into structured utterances
2. Segmenting transcripts into clinical sections
3. Detecting section boundaries using keywords
"""

import re
from typing import List, Optional, Tuple
from pathlib import Path
import sys

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.transcript import Utterance, TranscriptSection, SegmentedTranscript


class TranscriptParser:
    """Parse raw transcript text into structured utterances."""
    
    # Common speaker labels
    SPEAKER_PATTERNS = [
        r"^(Student|student|STUDENT):\s*",
        r"^(Patient|patient|PATIENT):\s*",
        r"^(Examiner|examiner|EXAMINER):\s*",
        r"^(S|s):\s*",
        r"^(P|p):\s*",
    ]
    
    # Timestamp patterns: [MM:SS] or [HH:MM:SS] or (MM:SS) or (HH:MM:SS)
    TIMESTAMP_PATTERN = r"[\[\(](\d{1,2}:\d{2}(?::\d{2})?)[\]\)]"
    
    def __init__(self):
        """Initialize the parser."""
        self.speaker_regex = re.compile("|".join(self.SPEAKER_PATTERNS))
        self.timestamp_regex = re.compile(self.TIMESTAMP_PATTERN)
    
    def parse(self, raw_text: str, transcript_id: str = "unknown") -> List[Utterance]:
        """
        Parse raw transcript text into utterances.
        
        Expected format:
        [00:05] Student: Tell me what brings you in today?
        [00:08] Patient: I have sudden weakness on my left side.
        
        Args:
            raw_text: Raw transcript text
            transcript_id: Identifier for the transcript
            
        Returns:
            List of Utterance objects
        """
        utterances = []
        lines = raw_text.strip().split('\n')
        
        current_timestamp = "00:00"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract timestamp if present
            timestamp_match = self.timestamp_regex.search(line)
            if timestamp_match:
                current_timestamp = timestamp_match.group(1)
                # Remove timestamp from line
                line = self.timestamp_regex.sub('', line).strip()
            
            # Extract speaker
            speaker = "unknown"
            text = line
            
            speaker_match = self.speaker_regex.match(line)
            if speaker_match:
                # Determine which pattern matched
                if any(s in speaker_match.group(0).lower() for s in ['student', 's:']):
                    speaker = "student"
                elif any(s in speaker_match.group(0).lower() for s in ['patient', 'p:']):
                    speaker = "patient"
                elif 'examiner' in speaker_match.group(0).lower():
                    speaker = "examiner"
                
                # Remove speaker label from text
                text = self.speaker_regex.sub('', line).strip()
            
            if text:
                utterances.append(Utterance(
                    speaker=speaker,
                    text=text,
                    timestamp_start=current_timestamp,
                    timestamp_end=current_timestamp  # Will be updated by segmenter
                ))
        
        return utterances


class TranscriptSegmenter:
    """Segment transcript into clinical sections."""
    
    # Section keywords for boundary detection
    SECTION_KEYWORDS = {
        "CC": [
            "what brings you in",
            "chief complaint",
            "what's going on",
            "what happened",
            "tell me about",
        ],
        "HPI": [
            "when did",
            "how long",
            "describe the",
            "tell me more about",
            "history of present illness",
        ],
        "ROS": [
            "review of systems",
            "any other symptoms",
            "anything else bothering",
            "any fever",
            "any headache",
            "any chest pain",
            "any shortness of breath",
        ],
        "PMH": [
            "past medical history",
            "any medical conditions",
            "any chronic conditions",
            "do you have diabetes",
            "do you have hypertension",
        ],
        "SH": [
            "social history",
            "do you smoke",
            "do you drink",
            "what do you do for work",
            "who do you live with",
        ],
        "FH": [
            "family history",
            "any family members",
            "does anyone in your family",
            "family medical history",
        ],
        "Summary": [
            "so to summarize",
            "in summary",
            "let me summarize",
            "to recap",
            "so this is a",
        ],
    }
    
    def __init__(self):
        """Initialize the segmenter."""
        pass
    
    def _detect_section(self, utterance: Utterance) -> Optional[str]:
        """
        Detect which section an utterance belongs to based on keywords.
        
        Args:
            utterance: The utterance to classify
            
        Returns:
            Section label or None if no match
        """
        text_lower = utterance.text.lower()
        
        # Check each section's keywords
        for section, keywords in self.SECTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return section
        
        return None
    
    def segment(
        self,
        utterances: List[Utterance],
        transcript_id: str = "unknown"
    ) -> SegmentedTranscript:
        """
        Segment utterances into clinical sections.
        
        Args:
            utterances: List of utterances to segment
            transcript_id: Identifier for the transcript
            
        Returns:
            SegmentedTranscript with sections and detected order
        """
        sections = []
        current_section_label = None
        current_section_utterances = []
        current_section_start = None
        detected_order = []
        
        for i, utterance in enumerate(utterances):
            # Only student utterances can trigger section changes
            if utterance.speaker == "student":
                detected_label = self._detect_section(utterance)
                
                if detected_label and detected_label != current_section_label:
                    # Save previous section if exists
                    if current_section_label and current_section_utterances:
                        sections.append(TranscriptSection(
                            label=current_section_label,
                            utterances=current_section_utterances,
                            timestamp_start=current_section_start,
                            timestamp_end=current_section_utterances[-1].timestamp_end
                        ))
                        detected_order.append(current_section_label)
                    
                    # Start new section
                    current_section_label = detected_label
                    current_section_utterances = [utterance]
                    current_section_start = utterance.timestamp_start
                else:
                    # Continue current section
                    if current_section_label:
                        current_section_utterances.append(utterance)
            else:
                # Patient/examiner utterances belong to current section
                if current_section_label:
                    current_section_utterances.append(utterance)
        
        # Save final section
        if current_section_label and current_section_utterances:
            sections.append(TranscriptSection(
                label=current_section_label,
                utterances=current_section_utterances,
                timestamp_start=current_section_start,
                timestamp_end=current_section_utterances[-1].timestamp_end
            ))
            detected_order.append(current_section_label)
        
        return SegmentedTranscript(
            transcript_id=transcript_id,
            sections=sections,
            detected_order=detected_order
        )


class TranscriptProcessor:
    """High-level processor combining parsing and segmentation."""
    
    def __init__(self):
        """Initialize the processor."""
        self.parser = TranscriptParser()
        self.segmenter = TranscriptSegmenter()
    
    def process(
        self,
        raw_text: str,
        transcript_id: str = "unknown"
    ) -> SegmentedTranscript:
        """
        Process raw transcript text into segmented transcript.
        
        Args:
            raw_text: Raw transcript text
            transcript_id: Identifier for the transcript
            
        Returns:
            SegmentedTranscript with parsed and segmented data
        """
        # Parse into utterances
        utterances = self.parser.parse(raw_text, transcript_id)
        
        # Segment into sections
        segmented = self.segmenter.segment(utterances, transcript_id)
        
        return segmented

