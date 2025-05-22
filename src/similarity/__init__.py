"""
Similarity analysis module for AllSeeingEye.

This module provides tools for analyzing code similarity, detecting
duplicate code, and generating refactoring suggestions.
"""

from .code_similarity import CodeSimilarityAnalyzer
from .token_analyzer import TokenAnalyzer
from .refactoring_suggestions import RefactoringSuggestionGenerator

__all__ = ['CodeSimilarityAnalyzer', 'TokenAnalyzer', 'RefactoringSuggestionGenerator']
