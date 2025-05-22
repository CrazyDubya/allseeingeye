#!/usr/bin/env python3
"""
Mock LLM provider for AllSeeingEye
"""

import logging
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger("MockProvider")

# Import the base provider
from src.llm.provider_base import LLMProvider


class MockProvider(LLMProvider):
    """Mock LLM provider for testing"""
    
    def __init__(self, responses: Optional[Dict[str, str]] = None):
        """
        Initialize the mock provider.
        
        Args:
            responses: Dictionary of prompt patterns to responses
        """
        super().__init__(None)
        self.responses = responses or {}
        self.is_available = True
    
    def generate(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Generate a mock response.
        
        Args:
            prompt: The prompt
            **kwargs: Additional arguments (ignored)
            
        Returns:
            Dictionary containing the mocked response
        """
        # Look for a matching pattern
        for pattern, response in self.responses.items():
            if pattern in prompt:
                return {"text": response}
        
        # Default response
        return {
            "text": "This is a mock response from the LLM.",
            "model": kwargs.get("model", "mock"),
            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt
        }
    
    def add_response(self, pattern: str, response: str) -> None:
        """
        Add a response pattern.
        
        Args:
            pattern: The pattern to match in prompts
            response: The response to return
        """
        self.responses[pattern] = response
    
    def clear_responses(self) -> None:
        """Clear all response patterns"""
        self.responses = {}
