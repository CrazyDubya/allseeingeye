#!/usr/bin/env python3
"""
Directory tree building functionality for AllSeeingEye
"""

import os
import logging
from typing import Dict, Any, Set, List, Optional, Callable

# Import core modules
from src.core.file_processor import FileProcessor

# Configure logging
logger = logging.getLogger("TreeBuilder")


class TreeBuilder:
    """Builds directory trees and processes files"""
    
    def __init__(self, 
                base_directory: str,
                file_processor: FileProcessor,
                excluded_dirs: Optional[Set[str]] = None,
                excluded_files: Optional[Set[str]] = None,
                max_files: int = 1000):
        """
        Initialize the tree builder.
        
        Args:
            base_directory: Root directory to analyze
            file_processor: FileProcessor instance to use
            excluded_dirs: Set of directories to exclude
            excluded_files: Set of files to exclude
            max_files: Maximum number of files to process
        """
        self.base_directory = os.path.abspath(base_directory)
        self.file_processor = file_processor
        self.excluded_dirs = excluded_dirs or set(['.git', 'node_modules', '.venv', '__pycache__', '.idea', '.vscode'])
        self.excluded_files = excluded_files or set()
        self.max_files = max_files
        
        # Initialize statistics
        self.stats = {
            "total_files": 0,
            "total_dirs": 0,
            "total_size": 0,
            "total_lines": 0,
            "files_by_category": {},
        }
    
    def build_tree(self, output_dictionary: Optional[Dict[str, Dict]] = None) -> str:
        """
        Build a directory tree and collect file information.
        
        Args:
            output_dictionary: Optional dictionary to store file content by category
            
        Returns:
            String representation of the directory tree
        """
        if output_dictionary is None:
            output_dictionary = {}
        
        # Use custom implementation for building tree
        tree_output = []
        
        def _build_tree_recursive(dir_path: str, prefix: str = '') -> bool:
            """
            Recursively build tree for a directory.
            
            Args:
                dir_path: Directory path
                prefix: String prefix for formatting
                
            Returns:
                True if processing should continue, False if file limit reached
            """
            entries = self.file_processor.list_directory(dir_path)
            
            # Sort entries
            entries = sorted(entries)
            
            # Separate directories and files
            dirs = [e for e in entries if os.path.isdir(os.path.join(dir_path, e))]
            files = [e for e in entries if os.path.isfile(os.path.join(dir_path, e))]
            
            # Process all files first
            for i, entry in enumerate(files):
                is_last = (i == len(files) - 1 and len(dirs) == 0)
                conn = '└── ' if is_last else '├── '
                
                file_path = os.path.join(dir_path, entry)
                rel_path = os.path.relpath(file_path, self.base_directory)
                
                # Skip excluded files
                if rel_path in self.excluded_files:
                    tree_output.append(f"{prefix}{conn}{entry} # Excluded")
                    continue
                
                # Process file
                self.stats["total_files"] += 1
                
                # Get file category
                category = self.file_processor.get_file_category(file_path)
                self.stats["files_by_category"][category] = self.stats["files_by_category"].get(category, 0) + 1
                
                # Add to tree
                tree_output.append(f"{prefix}{conn}{entry}")
                
                # Check if we've hit the file limit
                if self.stats["total_files"] >= self.max_files:
                    tree_output.append(f"{prefix}    --- File limit reached ({self.max_files} files) ---")
                    return False
                
                # Process file content if needed
                file_info = self.file_processor.process_file(file_path)
                
                # Update statistics
                self.stats["total_size"] += file_info.get("size", 0)
                self.stats["total_lines"] += file_info.get("line_count", 0) if "line_count" in file_info else 0
                
                # Add to output dictionary
                if category in self.file_processor.active_categories:
                    if category not in output_dictionary:
                        output_dictionary[category] = {}
                    output_dictionary[category][rel_path] = file_info
            
            # Then process directories
            for i, entry in enumerate(dirs):
                is_last = (i == len(dirs) - 1)
                conn = '└── ' if is_last else '├── '
                new_prefix = prefix + ('    ' if is_last else '│   ')
                
                dir_path_full = os.path.join(dir_path, entry)
                rel_dir_path = os.path.relpath(dir_path_full, self.base_directory)
                
                # Skip excluded directories
                if entry in self.excluded_dirs or rel_dir_path in self.excluded_dirs:
                    tree_output.append(f"{prefix}{conn}{entry}/ # Excluded")
                    continue
                
                # Add directory to tree
                tree_output.append(f"{prefix}{conn}{entry}/")
                self.stats["total_dirs"] += 1
                
                # Recursively process subdirectories
                if not _build_tree_recursive(dir_path_full, new_prefix):
                    return False  # Stop if file limit reached
            
            return True
        
        # Start the recursive tree building
        _build_tree_recursive(self.base_directory)
        
        # Format size in stats
        self.stats["total_size_formatted"] = self.file_processor.format_size(self.stats["total_size"])
        
        return '\n'.join(tree_output)
    
    def create_codebase_summary(self) -> str:
        """
        Create a summary of the codebase.
        
        Returns:
            Summary text
        """
        summary = []
        
        # Basic summary information
        summary.append("This codebase contains:")
        
        # Count files by type
        for category, count in self.stats['files_by_category'].items():
            if count > 0:
                from src.core.file_category import FileCategory
                description = FileCategory.get_description(category)
                summary.append(f"- {count} {description}")
        
        # Top-level directories
        top_dirs = [d for d in os.listdir(self.base_directory)
                    if os.path.isdir(os.path.join(self.base_directory, d))
                    and d not in self.excluded_dirs]
        
        if top_dirs:
            summary.append("\nMain directories:")
            for directory in sorted(top_dirs):
                dir_path = os.path.join(self.base_directory, directory)
                try:
                    file_count = sum(len(files) for _, _, files in os.walk(dir_path))
                    summary.append(f"- {directory}/: {file_count} files")
                except Exception as e:
                    logger.error(f"Error counting files in {dir_path}: {e}")
                    summary.append(f"- {directory}/: Error counting files")
        
        # Add language stats if available
        languages = {}
        for category, count in self.stats['files_by_category'].items():
            # Skip attempting to iterate over count, which is an integer
            continue
        
        if languages:
            summary.append("\nProgramming languages:")
            language_map = {
                ".py": "Python",
                ".js": "JavaScript",
                ".jsx": "React JSX",
                ".ts": "TypeScript",
                ".tsx": "React TSX",
                ".html": "HTML",
                ".css": "CSS",
                ".java": "Java",
                ".c": "C",
                ".cpp": "C++",
                ".cs": "C#",
                ".go": "Go",
                ".rb": "Ruby",
                ".php": "PHP",
                ".swift": "Swift",
                ".kt": "Kotlin",
                ".rs": "Rust"
            }
            
            # Get top 5 languages
            top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
            for ext, count in top_languages:
                lang_name = language_map.get(ext, ext)
                summary.append(f"- {lang_name}: {count} files")
        
        return "\n".join(summary)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get the current statistics.
        
        Returns:
            Statistics dictionary
        """
        return self.stats
