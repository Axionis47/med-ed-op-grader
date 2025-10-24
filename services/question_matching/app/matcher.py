"""
Question matching logic using BM25 and sentence embeddings.

This module implements hybrid matching:
1. BM25 for lexical matching
2. Sentence embeddings for semantic similarity
3. Combined scoring with configurable weights
"""

import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import sys

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.models.rubric import KeyQuestion
from shared.models.transcript import Utterance, SegmentedTranscript
from shared.models.evaluation import QuestionMatch, QuestionMatchingResult

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    SentenceTransformer = None
    np = None


class QuestionMatcher:
    """
    Hybrid question matcher using BM25 and embeddings.
    
    Combines lexical (BM25) and semantic (embeddings) matching
    for robust phrase detection in student transcripts.
    """
    
    def __init__(
        self,
        bm25_weight: float = 0.4,
        embedding_weight: float = 0.6,
        match_threshold: float = 0.5,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the matcher.
        
        Args:
            bm25_weight: Weight for BM25 score (0-1)
            embedding_weight: Weight for embedding score (0-1)
            match_threshold: Minimum combined score to consider a match
            embedding_model: Sentence transformer model name
        """
        self.bm25_weight = bm25_weight
        self.embedding_weight = embedding_weight
        self.match_threshold = match_threshold
        
        # Initialize embedding model if available
        if SentenceTransformer is not None:
            try:
                self.embedding_model = SentenceTransformer(embedding_model)
            except Exception as e:
                print(f"Warning: Could not load embedding model: {e}")
                self.embedding_model = None
        else:
            self.embedding_model = None
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25."""
        # Lowercase and split on non-alphanumeric
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def _compute_bm25_score(
        self,
        query_phrases: List[str],
        utterances: List[Utterance]
    ) -> List[float]:
        """
        Compute BM25 scores for each query phrase.
        
        Args:
            query_phrases: List of phrases to search for
            utterances: List of utterances to search in
            
        Returns:
            List of max BM25 scores for each query phrase
        """
        if BM25Okapi is None:
            # Fallback to simple substring matching
            scores = []
            for phrase in query_phrases:
                phrase_lower = phrase.lower()
                max_score = 0.0
                for utterance in utterances:
                    if phrase_lower in utterance.text.lower():
                        max_score = 1.0
                        break
                scores.append(max_score)
            return scores
        
        # Tokenize all utterances
        corpus = [self._tokenize(u.text) for u in utterances]
        
        if not corpus:
            return [0.0] * len(query_phrases)
        
        # Create BM25 index
        bm25 = BM25Okapi(corpus)
        
        # Score each query phrase
        scores = []
        for phrase in query_phrases:
            query_tokens = self._tokenize(phrase)
            phrase_scores = bm25.get_scores(query_tokens)
            # Normalize to [0, 1]
            max_score = max(phrase_scores) if len(phrase_scores) > 0 else 0.0
            normalized = min(max_score / 10.0, 1.0)  # Heuristic normalization
            scores.append(normalized)
        
        return scores
    
    def _compute_embedding_score(
        self,
        query_phrases: List[str],
        utterances: List[Utterance]
    ) -> List[float]:
        """
        Compute semantic similarity scores using embeddings.
        
        Args:
            query_phrases: List of phrases to search for
            utterances: List of utterances to search in
            
        Returns:
            List of max similarity scores for each query phrase
        """
        if self.embedding_model is None or np is None:
            # Fallback to simple substring matching
            scores = []
            for phrase in query_phrases:
                phrase_lower = phrase.lower()
                max_score = 0.0
                for utterance in utterances:
                    if phrase_lower in utterance.text.lower():
                        max_score = 1.0
                        break
                scores.append(max_score)
            return scores
        
        if not utterances:
            return [0.0] * len(query_phrases)
        
        # Encode query phrases
        query_embeddings = self.embedding_model.encode(query_phrases)
        
        # Encode utterances
        utterance_texts = [u.text for u in utterances]
        utterance_embeddings = self.embedding_model.encode(utterance_texts)
        
        # Compute cosine similarity for each query
        scores = []
        for query_emb in query_embeddings:
            # Compute similarity with all utterances
            similarities = np.dot(utterance_embeddings, query_emb) / (
                np.linalg.norm(utterance_embeddings, axis=1) * np.linalg.norm(query_emb)
            )
            max_similarity = float(np.max(similarities))
            scores.append(max_similarity)
        
        return scores
    
    def _find_best_match_utterance(
        self,
        phrase: str,
        utterances: List[Utterance]
    ) -> Optional[Utterance]:
        """
        Find the utterance that best matches the phrase.
        
        Args:
            phrase: Phrase to search for
            utterances: List of utterances
            
        Returns:
            Best matching utterance or None
        """
        if self.embedding_model is None or np is None:
            # Fallback to substring matching
            phrase_lower = phrase.lower()
            for utterance in utterances:
                if phrase_lower in utterance.text.lower():
                    return utterance
            return None
        
        # Use embeddings to find best match
        query_emb = self.embedding_model.encode([phrase])[0]
        utterance_texts = [u.text for u in utterances]
        utterance_embeddings = self.embedding_model.encode(utterance_texts)
        
        similarities = np.dot(utterance_embeddings, query_emb) / (
            np.linalg.norm(utterance_embeddings, axis=1) * np.linalg.norm(query_emb)
        )
        
        best_idx = int(np.argmax(similarities))
        return utterances[best_idx]
    
    def match_questions(
        self,
        key_questions: List[KeyQuestion],
        segmented_transcript: SegmentedTranscript
    ) -> QuestionMatchingResult:
        """
        Match key questions against transcript.
        
        Args:
            key_questions: List of key questions from rubric
            segmented_transcript: Segmented transcript to search
            
        Returns:
            QuestionMatchingResult with matches and scores
        """
        # Get all student utterances
        all_utterances = []
        for section in segmented_transcript.sections:
            all_utterances.extend([u for u in section.utterances if u.speaker == "student"])
        
        matches = []
        unmatched_questions = []
        total_weight = 0.0
        matched_weight = 0.0
        
        for question in key_questions:
            # Compute weight
            weight = 2.0 if question.is_critical else 1.0
            total_weight += weight
            
            # Get all phrases for this question
            phrases = question.phrases
            
            # Compute BM25 scores
            bm25_scores = self._compute_bm25_score(phrases, all_utterances)
            
            # Compute embedding scores
            embedding_scores = self._compute_embedding_score(phrases, all_utterances)
            
            # Combine scores
            combined_scores = [
                self.bm25_weight * bm25 + self.embedding_weight * emb
                for bm25, emb in zip(bm25_scores, embedding_scores)
            ]
            
            # Find best matching phrase
            max_score = max(combined_scores) if combined_scores else 0.0
            best_phrase_idx = combined_scores.index(max_score) if combined_scores else 0
            best_phrase = phrases[best_phrase_idx] if phrases else ""
            
            # Check if match exceeds threshold
            if max_score >= self.match_threshold:
                # Find the utterance that best matches
                best_utterance = self._find_best_match_utterance(best_phrase, all_utterances)
                
                match = QuestionMatch(
                    question_id=question.id,
                    question_anchor=question.anchor,
                    matched_phrase=best_phrase,
                    confidence=max_score,
                    student_citation=f"student://oral#{best_utterance.timestamp_start}–{best_utterance.timestamp_end}" if best_utterance else "",
                    is_critical=question.is_critical,
                    weight=weight
                )
                matches.append(match)
                matched_weight += weight
            else:
                unmatched_questions.append(question.id)
        
        return QuestionMatchingResult(
            matches=matches,
            unmatched_questions=unmatched_questions,
            total_weight=total_weight,
            matched_weight=matched_weight
        )

