#!/usr/bin/env python3
"""
Prompt optimization utilities for AllSeeingEye
"""

import logging
from typing import Dict, Any, Optional, List

# Configure logging
logger = logging.getLogger("PromptOptimizer")


class PromptOptimizer:
    """Utility for optimizing prompts for different LLM providers"""
    
    @staticmethod
    def optimize_for_ollama(prompt: str, model: str = "gemma:7b") -> str:
        """
        Optimize a prompt for Ollama models.
        
        Args:
            prompt: The prompt to optimize
            model: The specific Ollama model
            
        Returns:
            Optimized prompt string
        """
        # Add model-specific optimizations
        if "gemma" in model.lower():
            # Gemma models work well with concise, clear instructions
            # Add a clear delimiter for the prompt
            optimized = "<prompt>\n" + prompt.strip() + "\n</prompt>"
            
        elif "llama" in model.lower():
            # Llama models work well with role-based prompting
            # Ensure role is clearly defined
            if "You are an expert" not in prompt:
                optimized = "You are an expert AI assistant. " + prompt
            else:
                optimized = prompt
                
        elif "mistral" in model.lower():
            # Mistral models work well with specific instruction formatting
            optimized = "<instruction>\n" + prompt.strip() + "\n</instruction>"
            
        else:
            # Default optimization
            optimized = prompt
        
        return optimized
    
    @staticmethod
    def optimize_for_openai(prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Optimize a prompt for OpenAI models.
        
        Args:
            prompt: The prompt to optimize
            model: The specific OpenAI model
            
        Returns:
            Optimized prompt string
        """
        # Add model-specific optimizations
        if "gpt-4" in model.lower():
            # GPT-4 works well with detailed, structured instructions
            optimized = prompt
            
        elif "gpt-3.5" in model.lower():
            # GPT-3.5 benefits from more explicit instructions
            # Enhance clarity by adding line breaks between sections
            optimized = prompt.replace("\n\n", "\n\n\n")
            
        else:
            # Default optimization
            optimized = prompt
        
        return optimized
    
    @staticmethod
    def optimize_for_model(prompt: str, provider: str, model: str = None) -> str:
        """
        Optimize a prompt for a specific model provider.
        
        Args:
            prompt: The prompt to optimize
            provider: The LLM provider (e.g., "ollama", "openai")
            model: The specific model (optional)
            
        Returns:
            Optimized prompt string
        """
        if provider.lower() == "ollama":
            return PromptOptimizer.optimize_for_ollama(prompt, model or "gemma:7b")
        elif provider.lower() == "openai":
            return PromptOptimizer.optimize_for_openai(prompt, model or "gpt-3.5-turbo")
        else:
            # No specific optimization for other providers
            return prompt
    
    @staticmethod
    def add_system_context(prompt: str, context: str) -> str:
        """
        Add system context to a prompt.
        
        Args:
            prompt: The prompt to enhance
            context: The system context to add
            
        Returns:
            Enhanced prompt string
        """
        return f"System: {context}\n\nUser: {prompt}"
    
    @staticmethod
    def limit_prompt_size(prompt: str, max_tokens: int = 4000, truncation_point: str = "```") -> str:
        """
        Limit the size of a prompt by intelligent truncation.
        
        Args:
            prompt: The prompt to limit
            max_tokens: Maximum number of tokens (approximate)
            truncation_point: String marker for preferred truncation point
            
        Returns:
            Truncated prompt string
        """
        # Approximate token count as 4 chars per token
        approximate_token_count = len(prompt) / 4
        
        if approximate_token_count <= max_tokens:
            return prompt
        
        # Find truncation point
        if truncation_point in prompt:
            parts = prompt.split(truncation_point)
            
            # Preserve the first part and a meaningful suffix
            result = parts[0] + truncation_point
            
            # Add notice about truncation
            result += "\n\n[Note: The content has been truncated due to length limitations.]"
            
            return result
        
        # If no truncation point, simply truncate to approximate max tokens
        # Leave some room for the truncation notice
        chars_to_keep = int((max_tokens - 20) * 4)
        truncated = prompt[:chars_to_keep]
        
        return truncated + "\n\n[Content truncated due to length]"
    
    @staticmethod
    def enhance_with_examples(prompt: str, examples: List[Dict[str, str]]) -> str:
        """
        Enhance a prompt with few-shot examples.
        
        Args:
            prompt: The base prompt
            examples: List of example dictionaries with "input" and "output" keys
            
        Returns:
            Enhanced prompt with examples
        """
        enhanced = prompt + "\n\nHere are some examples to guide your response:\n"
        
        for i, example in enumerate(examples):
            enhanced += f"\nExample {i+1}:\nInput: {example['input']}\nOutput: {example['output']}\n"
        
        enhanced += "\nNow, please respond to the original request following these examples."
        
        return enhanced
