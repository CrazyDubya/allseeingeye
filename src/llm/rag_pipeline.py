#!/usr/bin/env python3
"""
RAG pipeline for AllSeeingEye.
"""

from .code_chunker import CodeChunker
from .embedding_generator import EmbeddingGenerator
from .vector_store import VectorStore
from .integration import get_llm_integration
from .prompt_formatter import PromptFormatter

class RAGPipeline:
    """Orchestrates the RAG pipeline."""

    def __init__(self, llm_provider="ollama", llm_model="gemma:7b"):
        self.llm = get_llm_integration(provider=llm_provider, config={"model": llm_model})
        self.chunker = CodeChunker()
        self.embedder = EmbeddingGenerator()
        self.vector_store = VectorStore(dimension=384) # all-MiniLM-L6-v2 has a dimension of 384

    def build(self, files_content: dict):
        """
        Builds the RAG pipeline.

        Args:
            files_content (dict): A dictionary of file contents.
        """
        for category in files_content:
            for file_path, file_info in files_content[category].items():
                if "content" in file_info:
                    chunks = self.chunker.chunk(file_info["content"], "python") # Assuming python for now
                    if chunks:
                        embeddings = self.embedder.generate(chunks)
                        self.vector_store.add(embeddings, chunks)

    def query(self, query: str) -> str:
        """
        Queries the RAG pipeline.

        Args:
            query (str): The natural language query.

        Returns:
            str: The answer to the query.
        """
        query_embedding = self.embedder.generate([query])[0]
        retrieved_chunks = self.vector_store.search(query_embedding)

        context = "\n\n".join(retrieved_chunks)
        prompt = f"Question: {query}\n\nContext:\n{context}\n\nAnswer:"

        response = self.llm.provider.generate(prompt)
        return response.get("text", "")
