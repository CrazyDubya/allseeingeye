#!/usr/bin/env python3
"""
Vector store utilities for AllSeeingEye.
"""

import faiss
import numpy as np
from typing import List

class VectorStore:
    """Stores and searches vector embeddings."""

    def __init__(self, dimension: int):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.chunks = []

    def add(self, embeddings: List[List[float]], chunks: List[str]):
        """
        Adds vector embeddings to the store.

        Args:
            embeddings (List[List[float]]): A list of vector embeddings.
            chunks (List[str]): A list of code chunks.
        """
        self.index.add(np.array(embeddings, dtype=np.float32))
        self.chunks.extend(chunks)

    def search(self, query_embedding: List[float], k: int = 5) -> List[str]:
        """
        Searches the vector store for the most similar embeddings.

        Args:
            query_embedding (List[float]): The query embedding.
            k (int, optional): The number of results to return. Defaults to 5.

        Returns:
            List[str]: A list of the most similar code chunks.
        """
        distances, indices = self.index.search(np.array([query_embedding], dtype=np.float32), k)
        return [self.chunks[i] for i in indices[0]]
