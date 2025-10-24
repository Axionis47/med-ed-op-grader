"""Tests for shared utility functions."""

import pytest
from .lcs import longest_common_subsequence, lcs_score, get_lcs_elements
from .timestamp import parse_timestamp, timestamp_to_seconds, format_timestamp, calculate_duration
from .tokenizer import count_tokens, count_tokens_advanced


class TestLCS:
    """Tests for LCS algorithm."""
    
    def test_identical_sequences(self):
        """Test LCS with identical sequences."""
        seq1 = ['A', 'B', 'C', 'D']
        seq2 = ['A', 'B', 'C', 'D']
        assert longest_common_subsequence(seq1, seq2) == 4
        assert lcs_score(seq1, seq2) == 1.0
    
    def test_partial_match(self):
        """Test LCS with partial match."""
        seq1 = ['A', 'B', 'C', 'D']
        seq2 = ['A', 'C', 'D']
        assert longest_common_subsequence(seq1, seq2) == 3
        # lcs_score divides by len(expected) which is seq2 (3), so 3/3 = 1.0
        assert lcs_score(seq1, seq2) == 1.0
    
    def test_no_match(self):
        """Test LCS with no match."""
        seq1 = ['A', 'B', 'C']
        seq2 = ['X', 'Y', 'Z']
        assert longest_common_subsequence(seq1, seq2) == 0
        assert lcs_score(seq1, seq2) == 0.0
    
    def test_clinical_sections(self):
        """Test LCS with clinical section order."""
        expected = ['CC', 'HPI', 'ROS', 'PMH', 'SH', 'FH', 'Summary']
        detected = ['CC', 'HPI', 'PMH', 'ROS', 'SH']
        lcs_length = longest_common_subsequence(detected, expected)
        # LCS is ['CC', 'HPI', 'ROS', 'SH'] = 4 (PMH is out of order)
        assert lcs_length == 4
    
    def test_get_lcs_elements(self):
        """Test getting actual LCS elements."""
        seq1 = ['A', 'B', 'C', 'D']
        seq2 = ['A', 'C', 'D', 'E']
        elements = get_lcs_elements(seq1, seq2)
        assert elements == ['A', 'C', 'D']


class TestTimestamp:
    """Tests for timestamp utilities."""
    
    def test_parse_timestamp_mmss(self):
        """Test parsing MM:SS format."""
        hours, minutes, seconds = parse_timestamp("01:30")
        assert hours == 0
        assert minutes == 1
        assert seconds == 30
    
    def test_parse_timestamp_hhmmss(self):
        """Test parsing HH:MM:SS format."""
        hours, minutes, seconds = parse_timestamp("1:05:30")
        assert hours == 1
        assert minutes == 5
        assert seconds == 30
    
    def test_timestamp_to_seconds_mmss(self):
        """Test converting MM:SS to seconds."""
        assert timestamp_to_seconds("01:30") == 90.0
        assert timestamp_to_seconds("00:05") == 5.0
    
    def test_timestamp_to_seconds_hhmmss(self):
        """Test converting HH:MM:SS to seconds."""
        assert timestamp_to_seconds("1:05:30") == 3930.0
    
    def test_format_timestamp(self):
        """Test formatting seconds to timestamp."""
        assert format_timestamp(90) == "01:30"
        assert format_timestamp(3930) == "1:05:30"
        assert format_timestamp(5) == "00:05"
    
    def test_calculate_duration(self):
        """Test calculating duration between timestamps."""
        assert calculate_duration("01:00", "01:30") == 30.0
        assert calculate_duration("00:05", "00:10") == 5.0
    
    def test_invalid_timestamp(self):
        """Test invalid timestamp format."""
        with pytest.raises(ValueError):
            parse_timestamp("invalid")
        with pytest.raises(ValueError):
            parse_timestamp("1:2:3:4")


class TestTokenizer:
    """Tests for tokenizer utilities."""
    
    def test_count_tokens_whitespace(self):
        """Test whitespace tokenization."""
        assert count_tokens("This is a test.") == 4
        assert count_tokens("Hello world") == 2
        assert count_tokens("") == 0
    
    def test_count_tokens_words(self):
        """Test word tokenization."""
        assert count_tokens("This is a test.", method="words") == 4
        assert count_tokens("Hello, world!", method="words") == 2
    
    def test_count_tokens_advanced(self):
        """Test advanced tokenization."""
        # Hyphenated words should be single tokens
        assert count_tokens_advanced("65-year-old male") == 2
        
        # Regular words
        assert count_tokens_advanced("This is a test") == 4
        
        # Contractions
        assert count_tokens_advanced("don't can't won't") == 3
    
    def test_invalid_method(self):
        """Test invalid tokenization method."""
        with pytest.raises(ValueError):
            count_tokens("test", method="invalid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

