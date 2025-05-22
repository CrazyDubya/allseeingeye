#!/usr/bin/env python3
"""
Ollama LLM provider for AllSeeingEye
"""

import os
import json
import time
import logging
import hashlib
import tempfile
from typing import Dict, Any, Optional, List, Union, Tuple

# Configure logging
logger = logging.getLogger("OllamaProvider")

# Import the base provider
from src.llm.provider_base import LLMProvider


class OllamaProvider(LLMProvider):
    """LLM provider using Ollama"""
    
    def __init__(self, 
                 model: str = "gemma:7b", 
                 api_base: str = "http://localhost:11434",
                 cache_dir: Optional[str] = None,
                 retries: int = 3,
                 retry_delay: int = 5):
        """
        Initialize the Ollama provider.
        
        Args:
            model: Model name to use
            api_base: Base URL for the Ollama API
            cache_dir: Directory to store cached responses
            retries: Number of retries on failure
            retry_delay: Delay between retries in seconds
        """
        super().__init__(cache_dir)
        self.model = model
        self.api_base = api_base
        self.retries = retries
        self.retry_delay = retry_delay
        
        # Try to import ollama
        try:
            import ollama
            self.ollama = ollama
            self.is_available = True
            
            # Configure API base
            if api_base:
                ollama.BASE_URL = api_base
                
        except ImportError:
            logger.warning("Ollama not available. Install with: pip install ollama")
            self.ollama = None
            self.is_available = False
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a response from Ollama.
        
        Args:
            prompt: The prompt to send to Ollama
            **kwargs: Additional arguments for Ollama
            
        Returns:
            Dictionary containing the response
        """
        if not self.is_available:
            return {"error": "Ollama not available", "text": ""}
        
        # Get model and other parameters
        model = kwargs.pop("model", self.model)
        use_cache = kwargs.pop("use_cache", True)
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(prompt, model=model, **kwargs)
            cached = self._get_cached_response(cache_key)
            if cached:
                logger.debug(f"Using cached response for {cache_key}")
                return cached
        
        # Generate response with retries
        for attempt in range(self.retries):
            try:
                logger.debug(f"Generating response from Ollama ({attempt+1}/{self.retries})")
                response = self.ollama.generate(model=model, prompt=prompt, **kwargs)
                
                # Cache the response
                if use_cache:
                    self._cache_response(cache_key, response)
                
                return response
                
            except Exception as e:
                logger.error(f"Error generating response from Ollama: {e}")
                if attempt < self.retries - 1:
                    logger.info(f"Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
        
        # If all retries failed
        return {"error": "Failed to generate response after retries", "text": ""}
