#!/usr/bin/env python3
"""
LLM integration for AllSeeingEye
"""

import os
import json
import re
import logging
import tempfile
from typing import Dict, Any, Optional, List, Union, Tuple

# Configure logging
logger = logging.getLogger("LLMIntegration")

# Import providers
from src.llm.provider_base import LLMProvider
from src.llm.ollama_provider import OllamaProvider
from src.llm.mock_provider import MockProvider


class LLMIntegration:
    """Main class for LLM integration"""
    
    def __init__(self, 
                 provider: str = "ollama",
                 cache_dir: Optional[str] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the LLM integration.
        
        Args:
            provider: Provider to use ("ollama" or "mock")
            cache_dir: Directory to store cached responses
            config: Configuration dictionary for the provider
        """
        self.config = config or {}
        
        # Set up cache directory
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = os.path.join(
                tempfile.gettempdir(), 
                "allseeingeye_llm_cache"
            )
            os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize provider
        if provider == "ollama":
            self.provider = OllamaProvider(
                model=self.config.get("model", "gemma:7b"),
                api_base=self.config.get("api_base", "http://localhost:11434"),
                cache_dir=self.cache_dir,
                retries=self.config.get("retries", 3),
                retry_delay=self.config.get("retry_delay", 5)
            )
        elif provider == "mock":
            self.provider = MockProvider(
                responses=self.config.get("responses", {})
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def is_available(self) -> bool:
        """
        Check if the LLM provider is available.
        
        Returns:
            True if available, False otherwise
        """
        return getattr(self.provider, "is_available", True)
    
    def summarize_code(self, code: str, filename: str = None) -> str:
        """
        Generate a summary of code.
        
        Args:
            code: The code to summarize
            filename: Optional filename for context
            
        Returns:
            Summary text
        """
        file_context = f"Filename: {filename}\n\n" if filename else ""
        
        prompt = f"""
        {file_context}Please analyze the following code and provide a brief summary:
        
        ```
        {code}
        ```
        
        Include:
        1. What the code does
        2. Key functionality
        3. Notable libraries or dependencies
        4. Potential issues or improvements
        
        Format your response as a concise paragraph. Focus only on the most important aspects.
        """
        
        response = self.provider.generate(prompt)
        
        if "error" in response:
            logger.error(f"Error summarizing code: {response['error']}")
            return f"Error generating summary: {response.get('error', 'Unknown error')}"
        
        return response.get("text", "")
    
    def analyze_codebase_structure(self, structure: str) -> str:
        """
        Analyze the structure of a codebase.
        
        Args:
            structure: String representation of the codebase structure
            
        Returns:
            Analysis text
        """
        prompt = f"""
        Please analyze the following codebase structure and provide insights:
        
        ```
        {structure}
        ```
        
        Include:
        1. Overall architecture
        2. Main components and their responsibilities
        3. Organization patterns
        4. Suggestions for improvement
        
        Format your response as a concise analysis. Focus on the big picture.
        """
        
        response = self.provider.generate(prompt)
        
        if "error" in response:
            logger.error(f"Error analyzing structure: {response['error']}")
            return f"Error analyzing structure: {response.get('error', 'Unknown error')}"
        
        return response.get("text", "")
    
    def generate_recommendations(self, codebase_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate recommendations for improving a codebase.
        
        Args:
            codebase_analysis: Dictionary with codebase analysis data
            
        Returns:
            List of recommendation dictionaries
        """
        # Extract relevant information
        file_count = codebase_analysis.get("statistics", {}).get("total_files", 0)
        categories = codebase_analysis.get("statistics", {}).get("files_by_category", {})
        
        prompt = f"""
        Please generate recommendations for improving a codebase with the following characteristics:
        
        - Total files: {file_count}
        - File categories: {json.dumps(categories, indent=2)}
        
        Generate exactly 5 recommendations, each with:
        1. A title
        2. A description
        3. Expected benefit
        4. Estimated complexity (Low, Medium, High)
        
        Format your response as JSON conforming to this schema:
        {{
            "recommendations": [
                {{
                    "title": "string",
                    "description": "string",
                    "benefit": "string",
                    "complexity": "string"
                }}
            ]
        }}
        
        Ensure the output is valid JSON. Focus on actionable recommendations.
        """
        
        response = self.provider.generate(prompt)
        
        if "error" in response:
            logger.error(f"Error generating recommendations: {response['error']}")
            return []
        
        # Parse recommendations from response
        try:
            text = response.get("text", "")
            
            # Extract JSON from the text (it might be surrounded by other text)
            json_match = re.search(r'(\{[\s\S]*\})', text)
            
            if json_match:
                recommendations_json = json.loads(json_match.group(1))
                return recommendations_json.get("recommendations", [])
            else:
                logger.error("No JSON found in response")
                return []
                
        except Exception as e:
            logger.error(f"Error parsing recommendations: {e}")
            return []
    
    def analyze_code_quality(self, code: str, filename: str = None) -> Dict[str, Any]:
        """
        Analyze code quality and provide suggestions.
        
        Args:
            code: The code to analyze
            filename: Optional filename for context
            
        Returns:
            Dictionary with analysis results
        """
        file_context = f"Filename: {filename}\n\n" if filename else ""
        
        prompt = f"""
        {file_context}Please analyze the following code for quality and provide suggestions:
        
        ```
        {code}
        ```
        
        Structure your response as a JSON object with the following sections:
        1. "overview": General assessment of the code quality
        2. "strengths": List of code strengths
        3. "issues": List of issues found, each with:
           - "severity": "low", "medium", or "high"
           - "description": Description of the issue
           - "suggestion": How to fix it
        4. "suggestions": General improvement suggestions
        
        Format the response as a valid JSON object.
        """
        
        response = self.provider.generate(prompt)
        
        if "error" in response:
            logger.error(f"Error analyzing code quality: {response['error']}")
            return {"error": response.get('error', 'Unknown error')}
        
        # Parse JSON from response
        try:
            text = response.get("text", "")
            
            # Extract JSON from the text
            json_match = re.search(r'(\{[\s\S]*\})', text)
            
            if json_match:
                return json.loads(json_match.group(1))
            else:
                return {"error": "No JSON found in response"}
                
        except Exception as e:
            logger.error(f"Error parsing code quality analysis: {e}")
            return {"error": f"Error parsing response: {str(e)}"}


def get_llm_integration(provider: str = "ollama", config: Dict[str, Any] = None) -> LLMIntegration:
    """
    Factory function to get an LLM integration instance.
    
    Args:
        provider: Provider name
        config: Provider configuration
        
    Returns:
        LLMIntegration instance
    """
    return LLMIntegration(provider=provider, config=config)
