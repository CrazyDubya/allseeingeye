#!/usr/bin/env python3
"""
Code chunking utilities for AllSeeingEye.
"""

import re
from typing import List

class CodeChunker:
    """Splits code into meaningful, overlapping chunks."""

    def __init__(self, chunk_size=1024, overlap=100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, code: str, language: str) -> List[str]:
        """
        Chunks the given code into smaller pieces.

        Args:
            code (str): The code to chunk.
            language (str): The language of the code.

        Returns:
            List[str]: A list of code chunks.
        """
        if language == "python":
            return self._chunk_python(code)
        else:
            return self._chunk_generic(code)

    def _chunk_python(self, code: str) -> List[str]:
        """Chunks Python code by function."""
        chunks = []
        functions = re.split(r"\n(def|class)\s+", code)

        current_chunk = ""
        for i in range(1, len(functions), 2):
            func_type = functions[i]
            func_code = functions[i+1]

            if len(current_chunk) + len(func_type) + len(func_code) > self.chunk_size:
                chunks.append(current_chunk)
                current_chunk = ""

            current_chunk += f"\n{func_type} {func_code}"

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _chunk_generic(self, code: str) -> List[str]:
        """Chunks generic code by line."""
        chunks = []
        lines = code.splitlines()

        start = 0
        while start < len(lines):
            end = start + self.chunk_size
            chunk = "\n".join(lines[start:end])
            chunks.append(chunk)
            start = end - self.overlap

        return chunks
