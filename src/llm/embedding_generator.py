#!/usr/bin/env python3
"""
Embedding generation utilities for AllSeeingEye.
"""

from sentence_transformers import SentenceTransformer
from typing import List

class EmbeddingGenerator:
    """Generates vector embeddings for code chunks."""

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def generate(self, code_chunks: List[str]) -> List[List[float]]:
        """
        Generates vector embeddings for the given code chunks.

        Args:
            code_chunks (List[str]): A list of code chunks.

        Returns:
            List[List[float]]: A list of vector embeddings.
        """
        return self.model.encode(code_chunks, convert_to_tensor=False).tolist()
