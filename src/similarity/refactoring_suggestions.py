#!/usr/bin/env python3
"""
Refactoring suggestion generator for AllSeeingEye.

This module analyzes code similarity results and generates
actionable refactoring suggestions to reduce code duplication.
"""

import os
import re
import logging
import json
from typing import List, Dict, Tuple, Set, Any, Optional, Union
from collections import defaultdict
from pathlib import Path

from .code_similarity import CodeSimilarityAnalyzer, CloneGroup, CodeFragment

# Configure logging
logger = logging.getLogger(__name__)

class RefactoringSuggestion:
    """
    Represents a refactoring suggestion for duplicated code.
    """
    
    def __init__(self,
                 title: str,
                 refactoring_type: str,
                 description: str,
                 fragments: List[Dict[str, Any]],
                 affected_files: List[str],
                 complexity: str,
                 benefit: str,
                 implementation_steps: List[str],
                 extracted_code: Optional[str] = None):
        """Initialize refactoring suggestion."""
        self.title = title
        self.refactoring_type = refactoring_type
        self.description = description
        self.fragments = fragments
        self.affected_files = affected_files
        self.complexity = complexity
        self.benefit = benefit
        self.implementation_steps = implementation_steps
        self.extracted_code = extracted_code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'title': self.title,
            'refactoring_type': self.refactoring_type,
            'description': self.description,
            'fragments': self.fragments,
            'affected_files': self.affected_files,
            'complexity': self.complexity,
            'benefit': self.benefit,
            'implementation_steps': self.implementation_steps,
            'extracted_code': self.extracted_code
        }


class RefactoringSuggestionGenerator:
    """
    Generates refactoring suggestions based on code similarity analysis.
    
    This class analyzes clone groups detected by the CodeSimilarityAnalyzer
    and generates specific, actionable refactoring suggestions.
    """
    
    def __init__(self, 
                 base_directory: str,
                 min_fragment_count: int = 2,
                 min_token_count: int = 20,
                 min_lines: int = 5,
                 max_lines: int = 200):
        """Initialize with configurable options."""
        self.base_directory = os.path.abspath(base_directory)
        self.min_fragment_count = min_fragment_count
        self.min_token_count = min_token_count
        self.min_lines = min_lines
        self.max_lines = max_lines
        self.similarity_analyzer = None
        self.suggestions = []
    
    def generate_suggestions(self, 
                           similarity_results: Optional[Dict[str, Any]] = None,
                           analyzer: Optional[CodeSimilarityAnalyzer] = None) -> List[Dict[str, Any]]:
        """
        Generate refactoring suggestions from similarity analysis results.
        
        Args:
            similarity_results: Optional pre-computed similarity results
            analyzer: Optional CodeSimilarityAnalyzer instance
            
        Returns:
            List[Dict[str, Any]]: List of refactoring suggestions
        """
        # Store analyzer for later use
        self.similarity_analyzer = analyzer
        
        # Clear previous suggestions
        self.suggestions = []
        
        # Get similarity results if not provided
        if not similarity_results:
            if not analyzer:
                logger.error("Either similarity_results or analyzer must be provided")
                return []
            
            similarity_results = analyzer.analyze_codebase()
        
        # Process clone groups
        for clone_group in similarity_results['clone_groups']:
            self._analyze_clone_group(clone_group)
        
        # Process directory-level duplication
        self._analyze_directory_duplication(similarity_results['file_statistics'])
        
        # Convert suggestions to dictionary format
        return [suggestion.to_dict() for suggestion in self.suggestions]
    
    def _analyze_clone_group(self, clone_group: Dict[str, Any]) -> None:
        """
        Analyze a clone group and generate appropriate refactoring suggestions.
        
        Args:
            clone_group: Clone group information
        """
        # Skip groups that don't meet minimum criteria
        if (len(clone_group['fragments']) < self.min_fragment_count or
            clone_group.get('token_count', 0) < self.min_token_count or
            clone_group.get('average_lines', 0) < self.min_lines or
            clone_group.get('average_lines', 0) > self.max_lines):
            return
        
        # Determine refactoring type based on clone characteristics
        clone_type = clone_group.get('clone_type', 'Unknown')
        
        # Get affected files
        affected_files = [f['file_path'] for f in clone_group['fragments']]
        unique_files = list(set(affected_files))
        
        # Determine if duplication is within the same file or across files
        duplication_scope = 'file' if len(unique_files) == 1 else 'cross-file'
        
        # Extract sample code if available
        sample_fragment = clone_group['fragments'][0] if clone_group['fragments'] else None
        
        # Generate appropriate refactoring suggestion
        if duplication_scope == 'file':
            # Duplication within the same file
            self._suggest_extract_method(clone_group, unique_files[0], clone_type)
        else:
            # Duplication across files
            self._suggest_extract_utility(clone_group, unique_files, clone_type)
    
    def _suggest_extract_method(self, 
                              clone_group: Dict[str, Any], 
                              file_path: str, 
                              clone_type: str) -> None:
        """
        Generate an 'Extract Method' refactoring suggestion.
        
        Args:
            clone_group: Clone group information
            file_path: Path to the file with duplication
            clone_type: Type of clone (Type 1, Type 2, or Type 3)
        """
        # Get file extension to determine language
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # Determine language-specific refactoring details
        language, method_keyword = self._get_language_info(ext)
        
        # Generate method name suggestion
        method_name = self._suggest_method_name(clone_group['fragments'][0], language)
        
        # Calculate potential lines saved
        fragments_count = len(clone_group['fragments'])
        avg_lines = clone_group.get('average_lines', 0)
        lines_saved = (fragments_count - 1) * avg_lines
        
        # Determine complexity and benefit
        complexity = self._determine_complexity(clone_type, fragments_count)
        benefit = self._determine_benefit(lines_saved, fragments_count)
        
        # Generate implementation steps
        implementation_steps = self._generate_implementation_steps_extract_method(
            language, method_keyword, method_name, file_path, fragments_count)
        
        # Generate extracted code template if available
        extracted_code = self._generate_extracted_code(clone_group['fragments'][0], 
                                                     language, method_keyword, method_name)
        
        # Create suggestion
        suggestion = RefactoringSuggestion(
            title=f"Extract '{method_name}' method in {os.path.basename(file_path)}",
            refactoring_type="Extract Method",
            description=f"Eliminate {fragments_count} duplicated code fragments in {file_path} "
                       f"by extracting a reusable method. This refactoring will save approximately "
                       f"{lines_saved} lines of code.",
            fragments=clone_group['fragments'],
            affected_files=[file_path],
            complexity=complexity,
            benefit=benefit,
            implementation_steps=implementation_steps,
            extracted_code=extracted_code
        )
        
        self.suggestions.append(suggestion)
    
    def _suggest_extract_utility(self, 
                               clone_group: Dict[str, Any], 
                               affected_files: List[str], 
                               clone_type: str) -> None:
        """
        Generate an 'Extract Utility' refactoring suggestion.
        
        Args:
            clone_group: Clone group information
            affected_files: List of affected file paths
            clone_type: Type of clone (Type 1, Type 2, or Type 3)
        """
        # Determine common language among affected files
        file_extensions = [os.path.splitext(f)[1].lower() for f in affected_files]
        
        # Filter to extensions we know
        known_extensions = [ext for ext in file_extensions if self._get_language_info(ext)[0]]
        
        if not known_extensions:
            # Skip if we can't determine language
            return
        
        primary_ext = max(set(known_extensions), key=known_extensions.count)
        language, method_keyword = self._get_language_info(primary_ext)
        
        # Determine if files are in the same directory
        directories = set(os.path.dirname(f) for f in affected_files)
        common_prefix = os.path.commonpath(affected_files)
        
        # Suggest module name and location
        if len(directories) == 1:
            # All files in the same directory
            module_location = os.path.dirname(affected_files[0])
            module_name = "utilities" + primary_ext
        else:
            # Files in different directories
            module_location = common_prefix
            module_name = "common_utilities" + primary_ext
        
        # Generate utility name
        utility_name = self._suggest_method_name(clone_group['fragments'][0], language)
        
        # Calculate potential lines saved
        fragments_count = len(clone_group['fragments'])
        avg_lines = clone_group.get('average_lines', 0)
        lines_saved = (fragments_count - 1) * avg_lines
        
        # Determine complexity and benefit
        complexity = self._determine_complexity(clone_type, fragments_count, is_cross_file=True)
        benefit = self._determine_benefit(lines_saved, fragments_count)
        
        # Generate implementation steps
        implementation_steps = self._generate_implementation_steps_extract_utility(
            language, method_keyword, utility_name, module_location, module_name, 
            affected_files, fragments_count)
        
        # Generate extracted code template if available
        extracted_code = self._generate_extracted_code(clone_group['fragments'][0], 
                                                     language, method_keyword, utility_name,
                                                     is_utility=True)
        
        # Create suggestion
        suggestion = RefactoringSuggestion(
            title=f"Extract '{utility_name}' utility function across {len(affected_files)} files",
            refactoring_type="Extract Utility Function",
            description=f"Eliminate duplicated code across {len(affected_files)} files "
                       f"by extracting a utility function to {module_name}. This refactoring "
                       f"will save approximately {lines_saved} lines of code and improve maintainability.",
            fragments=clone_group['fragments'],
            affected_files=affected_files,
            complexity=complexity,
            benefit=benefit,
            implementation_steps=implementation_steps,
            extracted_code=extracted_code
        )
        
        self.suggestions.append(suggestion)
    
    def _analyze_directory_duplication(self, file_statistics: List[Dict[str, Any]]) -> None:
        """
        Analyze directory-level duplication patterns for structural refactoring.
        
        Args:
            file_statistics: File duplication statistics
        """
        # Group files by directory
        dir_stats = defaultdict(lambda: {
            'total_lines': 0,
            'duplicated_lines': 0,
            'files': []
        })
        
        for file_info in file_statistics:
            if file_info['duplication_percentage'] > 0:
                dir_path = os.path.dirname(file_info['file_path'])
                dir_stats[dir_path]['files'].append(file_info)
                dir_stats[dir_path]['total_lines'] += file_info['total_lines']
                dir_stats[dir_path]['duplicated_lines'] += file_info['duplicated_lines']
        
        # Find directories with significant duplication
        for dir_path, stats in dir_stats.items():
            if len(stats['files']) < 3:
                continue
            
            # Calculate directory duplication percentage
            if stats['total_lines'] > 0:
                duplication_percentage = stats['duplicated_lines'] / stats['total_lines'] * 100
            else:
                duplication_percentage = 0
            
            # Only consider directories with significant duplication
            if duplication_percentage >= 15 and stats['duplicated_lines'] >= 100:
                self._suggest_directory_refactoring(dir_path, stats, duplication_percentage)
    
    def _suggest_directory_refactoring(self, 
                                     dir_path: str, 
                                     stats: Dict[str, Any], 
                                     duplication_percentage: float) -> None:
        """
        Generate a directory-level refactoring suggestion.
        
        Args:
            dir_path: Directory path
            stats: Directory statistics
            duplication_percentage: Percentage of duplicated code
        """
        # Determine common file extensions in the directory
        file_extensions = [os.path.splitext(f['file_path'])[1].lower() for f in stats['files']]
        common_exts = [ext for ext, count in Counter(file_extensions).items() if count >= 2]
        
        if not common_exts:
            return
        
        # Determine primary language
        primary_ext = max(set(common_exts), key=common_exts.count)
        language, _ = self._get_language_info(primary_ext)
        
        if not language:
            return
        
        # Generate refactoring title and type based on directory contents
        if 'test' in dir_path.lower() or 'spec' in dir_path.lower():
            title = f"Refactor test utilities in {os.path.basename(dir_path)}"
            refactoring_type = "Extract Test Utilities"
            description = f"Create a common test utilities module for the {len(stats['files'])} test files " \
                         f"in {dir_path}. Approximately {stats['duplicated_lines']} duplicated lines " \
                         f"({duplication_percentage:.1f}%) can be eliminated."
        elif 'model' in dir_path.lower() or 'entity' in dir_path.lower() or 'schema' in dir_path.lower():
            title = f"Create base model class in {os.path.basename(dir_path)}"
            refactoring_type = "Extract Base Class"
            description = f"Create a base class for the {len(stats['files'])} model files " \
                         f"in {dir_path}. Approximately {stats['duplicated_lines']} duplicated lines " \
                         f"({duplication_percentage:.1f}%) can be eliminated."
        else:
            title = f"Extract common utilities in {os.path.basename(dir_path)}"
            refactoring_type = "Extract Module Utilities"
            description = f"Create a utilities module for the {len(stats['files'])} files " \
                         f"in {dir_path}. Approximately {stats['duplicated_lines']} duplicated lines " \
                         f"({duplication_percentage:.1f}%) can be eliminated."
        
        # Implementation steps
        implementation_steps = [
            f"1. Create a new file '{os.path.basename(dir_path).lower()}_common{primary_ext}' in {dir_path}",
            "2. Identify common patterns and functionality across the files",
            f"3. Extract common code into appropriate functions/classes in the new file",
            "4. Update each original file to use the common utilities",
            "5. Test thoroughly to ensure behavior is preserved"
        ]
        
        # Determine complexity and benefit
        complexity = "High"
        benefit = "High" if duplication_percentage > 25 else "Medium"
        
        # Create suggestion
        suggestion = RefactoringSuggestion(
            title=title,
            refactoring_type=refactoring_type,
            description=description,
            fragments=[],  # No specific fragments for directory-level suggestion
            affected_files=[f['file_path'] for f in stats['files']],
            complexity=complexity,
            benefit=benefit,
            implementation_steps=implementation_steps,
            extracted_code=None
        )
        
        self.suggestions.append(suggestion)
    
    def _get_language_info(self, extension: str) -> Tuple[str, str]:
        """
        Get language info based on file extension.
        
        Args:
            extension: File extension
            
        Returns:
            Tuple[str, str]: (language_name, method_keyword)
        """
        extension = extension.lower()
        language_map = {
            '.py': ('python', 'def'),
            '.js': ('javascript', 'function'),
            '.jsx': ('javascript', 'function'),
            '.ts': ('typescript', 'function'),
            '.tsx': ('typescript', 'function'),
            '.java': ('java', 'public'),
            '.c': ('c', 'void'),
            '.cpp': ('cpp', 'void'),
            '.cs': ('csharp', 'public'),
            '.go': ('go', 'func'),
            '.rb': ('ruby', 'def'),
            '.php': ('php', 'function')
        }
        
        return language_map.get(extension, ('', ''))
    
    def _suggest_method_name(self, fragment: Dict[str, Any], language: str) -> str:
        """
        Suggest a meaningful method name based on fragment content.
        
        Args:
            fragment: Code fragment information
            language: Programming language
            
        Returns:
            str: Suggested method name
        """
        # Default name if we can't generate something more meaningful
        default_name = "extractedMethod"
        
        # If no fragment content available, return default
        if not fragment:
            return default_name
        
        file_path = fragment.get('file_path', '')
        
        # Try to extract some meaningful context from the file path
        path_parts = file_path.split(os.sep)
        context_words = []
        
        for part in path_parts:
            # Skip common directory names
            if part.lower() in ('src', 'lib', 'app', 'test', 'tests'):
                continue
            
            # Extract words from camelCase or snake_case
            words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', part)
            words.extend(part.split('_'))
            
            for word in words:
                if len(word) > 2 and word.lower() not in context_words:
                    context_words.append(word.lower())
        
        # Use filename without extension as additional context
        if file_path:
            filename = os.path.basename(file_path)
            filename = os.path.splitext(filename)[0]
            
            # Extract words from camelCase or snake_case
            words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', filename)
            words.extend(filename.split('_'))
            
            for word in words:
                if len(word) > 2 and word.lower() not in context_words:
                    context_words.append(word.lower())
        
        # Generate a name from context
        if context_words:
            method_name = 'common'
            if len(context_words) > 1:
                method_name += ''.join(word.capitalize() for word in context_words[:2])
            else:
                method_name += context_words[0].capitalize()
        else:
            method_name = default_name
        
        # Format according to language convention
        if language in ('python', 'ruby'):
            method_name = re.sub(r'(?<!^)(?=[A-Z])', '_', method_name).lower()
        elif language in ('javascript', 'typescript', 'java', 'csharp'):
            if not method_name[0].islower() and method_name[0].isalpha():
                method_name = method_name[0].lower() + method_name[1:]
        
        return method_name
    
    def _determine_complexity(self, clone_type: str, fragment_count: int, is_cross_file: bool = False) -> str:
        """
        Determine refactoring complexity.
        
        Args:
            clone_type: Type of clone
            fragment_count: Number of duplicated fragments
            is_cross_file: Whether duplication is across files
            
        Returns:
            str: Complexity level (Low, Medium, High)
        """
        if is_cross_file:
            # Cross-file refactoring is more complex
            if clone_type == "Type 1":
                return "Medium"
            else:
                return "High"
        else:
            # Same-file refactoring
            if clone_type == "Type 1" and fragment_count <= 3:
                return "Low"
            elif clone_type == "Type 1":
                return "Medium"
            else:
                return "Medium"
    
    def _determine_benefit(self, lines_saved: int, fragment_count: int) -> str:
        """
        Determine refactoring benefit.
        
        Args:
            lines_saved: Number of lines that will be saved
            fragment_count: Number of duplicated fragments
            
        Returns:
            str: Benefit level (Low, Medium, High)
        """
        if lines_saved >= 100 or fragment_count >= 5:
            return "High"
        elif lines_saved >= 30 or fragment_count >= 3:
            return "Medium"
        else:
            return "Low"
    
    def _generate_implementation_steps_extract_method(self,
                                                    language: str,
                                                    method_keyword: str,
                                                    method_name: str,
                                                    file_path: str,
                                                    fragment_count: int) -> List[str]:
        """
        Generate implementation steps for Extract Method refactoring.
        
        Args:
            language: Programming language
            method_keyword: Method declaration keyword
            method_name: Suggested method name
            file_path: File path
            fragment_count: Number of duplicated fragments
            
        Returns:
            List[str]: Implementation steps
        """
        steps = [
            f"1. Create a new {method_keyword} {method_name} in {os.path.basename(file_path)}",
            "2. Identify parameters by analyzing variables used but not defined in the duplicated code",
            "3. Identify return values by analyzing variables modified in the duplicated code",
            f"4. Replace each of the {fragment_count} duplicated code fragments with a call to {method_name}",
            "5. Test to verify that the behavior is preserved"
        ]
        
        # Add language-specific steps
        if language == 'python':
            steps.insert(3, "4. Add docstring to describe the method's purpose, parameters, and return value")
        elif language in ('java', 'csharp'):
            steps.insert(1, "2. Determine appropriate access modifier (private/protected/public)")
        elif language in ('javascript', 'typescript'):
            steps.insert(3, "4. Consider adding JSDoc comments to document the function")
        
        return steps
    
    def _generate_implementation_steps_extract_utility(self,
                                                     language: str,
                                                     method_keyword: str,
                                                     utility_name: str,
                                                     module_location: str,
                                                     module_name: str,
                                                     affected_files: List[str],
                                                     fragment_count: int) -> List[str]:
        """
        Generate implementation steps for Extract Utility refactoring.
        
        Args:
            language: Programming language
            method_keyword: Method declaration keyword
            utility_name: Suggested utility name
            module_location: Location for new utility module
            module_name: Name for new utility module
            affected_files: List of affected files
            fragment_count: Number of duplicated fragments
            
        Returns:
            List[str]: Implementation steps
        """
        steps = [
            f"1. Create a new utility file {module_name} in {module_location}",
            f"2. Create a {method_keyword} {utility_name} in the utility file",
            "3. Identify parameters by analyzing variables used but not defined in the duplicated code",
            "4. Identify return values by analyzing variables modified in the duplicated code",
            f"5. Replace each of the {fragment_count} duplicated code fragments with an import and call to {utility_name}",
            "6. Test to verify that the behavior is preserved"
        ]
        
        # Add language-specific steps
        if language == 'python':
            steps.insert(1, "2. Add an __init__.py file if needed to make it a proper package")
            steps.insert(4, "5. Add docstring to describe the function's purpose, parameters, and return value")
        elif language in ('javascript', 'typescript'):
            steps.insert(1, "2. Set up proper module exports")
            steps.insert(4, "5. Consider adding JSDoc comments to document the function")
        elif language == 'java':
            steps.insert(1, "2. Create a proper package structure")
            steps.insert(2, "3. Determine appropriate access modifier (public/package-private)")
        
        return steps
    
    def _generate_extracted_code(self,
                               fragment: Dict[str, Any],
                               language: str,
                               method_keyword: str,
                               method_name: str,
                               is_utility: bool = False) -> Optional[str]:
        """
        Generate a template for the extracted code.
        
        This is a simplified template - actual implementation would require
        more advanced code analysis.
        
        Args:
            fragment: Code fragment information
            language: Programming language
            method_keyword: Method declaration keyword
            method_name: Suggested method name
            is_utility: Whether this is a utility function
            
        Returns:
            Optional[str]: Template for extracted code or None
        """
        # If no fragment available, return None
        if not fragment:
            return None
        
        # Get file path to access content if needed
        file_path = fragment.get('file_path', '')
        if not file_path:
            return None
        
        absolute_path = os.path.join(self.base_directory, file_path)
        if not os.path.exists(absolute_path):
            return None
        
        # Language-specific templates
        if language == 'python':
            template = f"""def {method_name}(param1, param2):
    \"\"\"
    [Description of what this function does]
    
    Args:
        param1: [Description]
        param2: [Description]
        
    Returns:
        [Description of return value]
    \"\"\"
    # TODO: Replace parameters with actual parameters needed
    # TODO: Add implementation based on duplicated code
    
    # Placeholder for extracted code
    result = None
    
    return result
"""
        elif language in ('javascript', 'typescript'):
            template = f"""/**
 * [Description of what this function does]
 * 
 * @param {{any}} param1 - [Description]
 * @param {{any}} param2 - [Description]
 * @returns {{any}} [Description of return value]
 */
{method_keyword} {method_name}(param1, param2) {{
    // TODO: Replace parameters with actual parameters needed
    // TODO: Add implementation based on duplicated code
    
    // Placeholder for extracted code
    let result = null;
    
    return result;
}}
"""
            if is_utility:
                template += "\nexport { " + method_name + " };\n"
                
        elif language == 'java':
            access_modifier = "public" if is_utility else "private"
            template = f"""{access_modifier} static Object {method_name}(Object param1, Object param2) {{
    // TODO: Replace parameters and return type with actual types needed
    // TODO: Add implementation based on duplicated code
    
    // Placeholder for extracted code
    Object result = null;
    
    return result;
}}
"""
        elif language == 'cpp':
            template = f"""{method_keyword} {method_name}(void* param1, void* param2) {{
    // TODO: Replace parameters and return type with actual types needed
    // TODO: Add implementation based on duplicated code
    
    // Placeholder for extracted code
    void* result = nullptr;
    
    return result;
}}
"""
        else:
            # Generic template for unsupported languages
            template = f"""{method_keyword} {method_name}:
    # TODO: Replace with appropriate parameters
    # TODO: Add implementation based on duplicated code
    # Extracted from {file_path}
"""
        
        return template
