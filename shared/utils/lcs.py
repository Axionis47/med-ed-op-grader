"""Longest Common Subsequence (LCS) algorithm for structure evaluation."""

from typing import TypeVar, Sequence

T = TypeVar('T')


def longest_common_subsequence(seq1: Sequence[T], seq2: Sequence[T]) -> int:
    """
    Compute the length of the longest common subsequence between two sequences.
    
    Uses dynamic programming with O(m*n) time complexity and O(m*n) space complexity.
    
    Args:
        seq1: First sequence
        seq2: Second sequence
    
    Returns:
        Length of the longest common subsequence
    
    Example:
        >>> longest_common_subsequence(['A', 'B', 'C', 'D'], ['A', 'C', 'D'])
        3
        >>> longest_common_subsequence(['CC', 'HPI', 'ROS'], ['CC', 'HPI', 'PMH', 'ROS'])
        3
    """
    m, n = len(seq1), len(seq2)
    
    # Create DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Fill DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    return dp[m][n]


def lcs_score(detected: Sequence[T], expected: Sequence[T]) -> float:
    """
    Compute LCS-based score normalized by expected sequence length.
    
    Args:
        detected: Detected sequence
        expected: Expected sequence
    
    Returns:
        Score in range [0, 1]
    
    Example:
        >>> lcs_score(['CC', 'HPI', 'ROS'], ['CC', 'HPI', 'ROS', 'PMH'])
        0.75
    """
    if not expected:
        return 1.0
    
    lcs_length = longest_common_subsequence(detected, expected)
    return lcs_length / len(expected)


def get_lcs_elements(seq1: Sequence[T], seq2: Sequence[T]) -> list[T]:
    """
    Get the actual elements in the longest common subsequence.
    
    Args:
        seq1: First sequence
        seq2: Second sequence
    
    Returns:
        List of elements in the LCS
    
    Example:
        >>> get_lcs_elements(['A', 'B', 'C', 'D'], ['A', 'C', 'D', 'E'])
        ['A', 'C', 'D']
    """
    m, n = len(seq1), len(seq2)
    
    # Create DP table
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    # Fill DP table
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    # Backtrack to find LCS elements
    result = []
    i, j = m, n
    while i > 0 and j > 0:
        if seq1[i - 1] == seq2[j - 1]:
            result.append(seq1[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    
    return list(reversed(result))

