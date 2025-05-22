#!/usr/bin/env python3
"""
Base LLM provider for AllSeeingEye
"""

import os
import json
import logging
import hashlib
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger("LLMProvider")


class LLMProvider:
    """Base class for LLM providers"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the LLM provider.
        
        Args:
            cache_dir: Directory to store cached responses
        """
        self.cache_dir = cache_dir
        
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            **kwargs: Additional arguments for the LLM
            
        Returns:
            Dictionary containing the response
        """
        raise NotImplementedError("Subclasses must implement generate()")
    
    def _get_cache_key(self, prompt: str, **kwargs) -> str:
        """
        Generate a cache key for the prompt and arguments.
        
        Args:
            prompt: The prompt
            **kwargs: Additional arguments
            
        Returns:
            Cache key as a string
        """
        # Create a dictionary with all parameters
        params = {
            "prompt": prompt,
            **kwargs
        }
        
        # Convert to a stable string representation and hash it
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(param_str.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get a cached response if available.
        
        Args:
            cache_key: The cache key
            
        Returns:
            Cached response or None if not found
        """
        if not self.cache_dir:
            return None
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading cache: {e}")
                return None
        
        return None
    
    def _cache_response(self, cache_key: str, response: Dict[str, Any]) -> None:
        """
        Cache a response.
        
        Args:
            cache_key: The cache key
            response: The response to cache
        """
        if not self.cache_dir:
            return
        
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            with open(cache_file, "w") as f:
                json.dump(response, f)
        except Exception as e:
            logger.warning(f"Error writing cache: {e}")
