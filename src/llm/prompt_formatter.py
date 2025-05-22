#!/usr/bin/env python3
"""
Prompt formatting utilities for AllSeeingEye
"""

import os
import re
import json
from typing import Dict, Any, List, Optional, Union

# Import prompt templates
from src.llm.prompt_templates import PromptTemplates


class PromptFormatter:
    """Utility for formatting and optimizing prompts"""
    
    @staticmethod
    def format_prompt(template: str, variables: Dict[str, Any]) -> str:
        """
        Format a prompt template with provided variables.
        
        Args:
            template: The prompt template string
            variables: Dictionary of variables to insert
            
        Returns:
            Formatted prompt string
        """
        # Apply formatting with variable substitution
        formatted = template.format(**variables)
        
        # Clean up the formatting (remove excessive whitespace)
        formatted = re.sub(r'\n\s*\n+', '\n\n', formatted)
        
        # Ensure the prompt ends with a newline
        if not formatted.endswith('\n'):
            formatted += '\n'
        
        return formatted
    
    @staticmethod
    def format_code_analysis_prompt(
        code: str, 
        filename: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """
        Format a code analysis prompt.
        
        Args:
            code: The code to analyze
            filename: Optional filename
            language: Optional language identifier
            
        Returns:
            Formatted prompt string
        """
        # Determine language from filename if not specified
        if language is None and filename is not None:
            ext = os.path.splitext(filename)[1].lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.jsx': 'jsx',
                '.ts': 'typescript',
                '.tsx': 'tsx',
                '.java': 'java',
                '.c': 'c',
                '.cpp': 'cpp',
                '.cs': 'csharp',
                '.go': 'go',
                '.rb': 'ruby',
                '.php': 'php',
                '.html': 'html',
                '.css': 'css',
                '.sql': 'sql',
                '.sh': 'bash',
            }
            language = language_map.get(ext, 'text')
        
        # Use default values if still not specified
        filename = filename or "unknown_file"
        language = language or "text"
        
        # Format the prompt
        variables = {
            'code': code,
            'filename': filename,
            'language': language
        }
        
        return PromptFormatter.format_prompt(PromptTemplates.CODE_ANALYSIS, variables)
    
    @staticmethod
    def format_code_review_prompt(
        code: str, 
        filename: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """
        Format a code review prompt.
        
        Args:
            code: The code to review
            filename: Optional filename
            language: Optional language identifier
            
        Returns:
            Formatted prompt string
        """
        # Determine language from filename if not specified
        if language is None and filename is not None:
            ext = os.path.splitext(filename)[1].lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.jsx': 'jsx',
                '.ts': 'typescript',
                '.tsx': 'tsx',
                '.java': 'java',
                '.c': 'c',
                '.cpp': 'cpp',
                '.cs': 'csharp',
                '.go': 'go',
                '.rb': 'ruby',
                '.php': 'php',
                '.html': 'html',
                '.css': 'css',
                '.sql': 'sql',
                '.sh': 'bash',
            }
            language = language_map.get(ext, 'text')
        
        # Use default values if still not specified
        filename = filename or "unknown_file"
        language = language or "text"
        
        # Format the prompt
        variables = {
            'code': code,
            'filename': filename,
            'language': language
        }
        
        return PromptFormatter.format_prompt(PromptTemplates.CODE_REVIEW, variables)
    
    @staticmethod
    def format_structure_analysis_prompt(structure: str) -> str:
        """
        Format a codebase structure analysis prompt.
        
        Args:
            structure: The codebase structure representation
            
        Returns:
            Formatted prompt string
        """
        variables = {
            'structure': structure
        }
        
        return PromptFormatter.format_prompt(PromptTemplates.CODEBASE_STRUCTURE, variables)
    
    @staticmethod
    def format_recommendations_prompt(
        file_count: int,
        file_categories: Dict[str, int],
        line_count: int,
        languages: List[str],
        context: str,
        recommendation_count: int = 5
    ) -> str:
        """
        Format a recommendations prompt.
        
        Args:
            file_count: Number of files in the codebase
            file_categories: Dictionary mapping categories to file counts
            line_count: Total lines of code
            languages: List of programming languages used
            context: Additional context about the codebase
            recommendation_count: Number of recommendations to request
            
        Returns:
            Formatted prompt string
        """
        variables = {
            'file_count': file_count,
            'file_categories': json.dumps(file_categories, indent=2),
            'line_count': line_count,
            'languages': ', '.join(languages),
            'context': context,
            'recommendation_count': recommendation_count
        }
        
        return PromptFormatter.format_prompt(PromptTemplates.IMPROVEMENT_RECOMMENDATIONS, variables)
    
    @staticmethod
    def format_documentation_prompt(
        code: str, 
        filename: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """
        Format a documentation generation prompt.
        
        Args:
            code: The code to document
            filename: Optional filename
            language: Optional language identifier
            
        Returns:
            Formatted prompt string
        """
        # Determine language from filename if not specified
        if language is None and filename is not None:
            ext = os.path.splitext(filename)[1].lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.jsx': 'jsx',
                '.ts': 'typescript',
                '.tsx': 'tsx',
                '.java': 'java',
                '.c': 'c',
                '.cpp': 'cpp',
                '.cs': 'csharp',
                '.go': 'go',
                '.rb': 'ruby',
                '.php': 'php',
                '.html': 'html',
                '.css': 'css',
                '.sql': 'sql',
                '.sh': 'bash',
            }
            language = language_map.get(ext, 'text')
        
        # Use default values if still not specified
        filename = filename or "unknown_file"
        language = language or "text"
        
        # Format the prompt
        variables = {
            'code': code,
            'filename': filename,
            'language': language
        }
        
        return PromptFormatter.format_prompt(PromptTemplates.DOCUMENTATION, variables)
    
    @staticmethod
    def format_bug_analysis_prompt(
        code: str,
        issue_description: str,
        filename: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """
        Format a bug analysis prompt.
        
        Args:
            code: The code to analyze
            issue_description: Description of the bug or issue
            filename: Optional filename
            language: Optional language identifier
            
        Returns:
            Formatted prompt string
        """
        # Determine language from filename if not specified
        if language is None and filename is not None:
            ext = os.path.splitext(filename)[1].lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.jsx': 'jsx',
                '.ts': 'typescript',
                '.tsx': 'tsx',
                '.java': 'java',
                '.c': 'c',
                '.cpp': 'cpp',
                '.cs': 'csharp',
                '.go': 'go',
                '.rb': 'ruby',
                '.php': 'php',
                '.html': 'html',
                '.css': 'css',
                '.sql': 'sql',
                '.sh': 'bash',
            }
            language = language_map.get(ext, 'text')
        
        # Use default values if still not specified
        filename = filename or "unknown_file"
        language = language or "text"
        
        # Format the prompt
        variables = {
            'code': code,
            'filename': filename,
            'language': language,
            'issue_description': issue_description
        }
        
        return PromptFormatter.format_prompt(PromptTemplates.BUG_ANALYSIS, variables)
    
    @staticmethod
    def format_security_audit_prompt(
        code: str, 
        filename: Optional[str] = None,
        language: Optional[str] = None
    ) -> str:
        """
        Format a security audit prompt.
        
        Args:
            code: The code to audit
            filename: Optional filename
            language: Optional language identifier
            
        Returns:
            Formatted prompt string
        """
        # Determine language from filename if not specified
        if language is None and filename is not None:
            ext = os.path.splitext(filename)[1].lower()
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.jsx': 'jsx',
                '.ts': 'typescript',
                '.tsx': 'tsx',
                '.java': 'java',
                '.c': 'c',
                '.cpp': 'cpp',
                '.cs': 'csharp',
                '.go': 'go',
                '.rb': 'ruby',
                '.php': 'php',
                '.html': 'html',
                '.css': 'css',
                '.sql': 'sql',
                '.sh': 'bash',
            }
            language = language_map.get(ext, 'text')
        
        # Use default values if still not specified
        filename = filename or "unknown_file"
        language = language or "text"
        
        # Format the prompt
        variables = {
            'code': code,
            'filename': filename,
            'language': language
        }
        
        return PromptFormatter.format_prompt(PromptTemplates.SECURITY_AUDIT, variables)
