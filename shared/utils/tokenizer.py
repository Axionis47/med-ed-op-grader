"""Token counting utilities."""

import re


def count_tokens(text: str, method: str = "whitespace") -> int:
    """
    Count tokens in text.
    
    For MVP, we use simple whitespace tokenization.
    Can be enhanced with proper tokenizers (e.g., tiktoken) later.
    
    Args:
        text: Text to tokenize
        method: Tokenization method ("whitespace" or "words")
    
    Returns:
        Number of tokens
    
    Example:
        >>> count_tokens("This is a test.")
        4
        >>> count_tokens("65-year-old male with headache")
        4
    """
    if method == "whitespace":
        # Simple whitespace tokenization
        return len(text.split())
    elif method == "words":
        # Word tokenization (alphanumeric sequences)
        words = re.findall(r'\b\w+\b', text)
        return len(words)
    else:
        raise ValueError(f"Unknown tokenization method: {method}")


def count_tokens_advanced(text: str) -> int:
    """
    Advanced token counting using more sophisticated rules.
    
    This method:
    - Treats hyphenated words as single tokens
    - Handles contractions properly
    - Counts numbers as single tokens
    
    Args:
        text: Text to tokenize
    
    Returns:
        Number of tokens
    
    Example:
        >>> count_tokens_advanced("65-year-old male with headache")
        5
    """
    # Pattern matches:
    # - Hyphenated words (e.g., "65-year-old")
    # - Contractions (e.g., "don't")
    # - Regular words
    # - Numbers
    pattern = r"\b[\w]+-[\w]+(?:-[\w]+)*\b|\b\w+'\w+\b|\b\w+\b"
    tokens = re.findall(pattern, text.lower())
    return len(tokens)

