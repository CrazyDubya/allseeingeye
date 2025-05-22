#!/usr/bin/env python3
"""
Memory-efficient tree building for AllSeeingEye
"""

import os
import logging
from typing import Dict, Any, List, Set, Optional, Callable, Generator, Tuple

# Configure logging
logger = logging.getLogger("EfficientTree")


class StreamingTreeBuilder:
    """Memory-efficient directory tree builder that streams results"""
    
    def __init__(self, 
                base_directory: str,
                excluded_dirs: Optional[Set[str]] = None,
                excluded_files: Optional[Set[str]] = None,
                max_depth: Optional[int] = None):
        """
        Initialize the streaming tree builder.
        
        Args:
            base_directory: Root directory to analyze
            excluded_dirs: Set of directories to exclude
            excluded_files: Set of files to exclude
            max_depth: Maximum directory depth
        """
        self.base_directory = os.path.abspath(base_directory)
        self.excluded_dirs = excluded_dirs or set(['.git', 'node_modules', '.venv', '__pycache__', '.idea', '.vscode'])
        self.excluded_files = excluded_files or set()
        self.max_depth = max_depth
        
        # Initialize statistics
        self.stats = {
            "total_files": 0,
            "total_dirs": 0,
            "total_size": 0,
            "files_by_category": {},
        }
    
    def stream_tree(self, category_func: Optional[Callable[[str], str]] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Stream the directory tree, yielding entries as they are processed.
        
        Args:
            category_func: Function to determine file category
            
        Yields:
            Directory and file entries
        """
        # Track current prefix for tree lines
        prefix_stack = []
        
        # Walk the directory starting from base
        for root, dirs, files in self._walk_with_depth():
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs and 
                      os.path.relpath(os.path.join(root, d), self.base_directory) not in self.excluded_dirs]
            
            # Get current directory information
            rel_path = os.path.relpath(root, self.base_directory)
            depth = 0 if rel_path == '.' else rel_path.count(os.sep) + 1
            
            # Update directory count
            if root != self.base_directory:
                self.stats["total_dirs"] += 1
                
                # Calculate directory prefix
                if depth > len(prefix_stack):
                    # New directory level
                    prefix_stack.append('│   ')
                elif depth < len(prefix_stack):
                    # Going back up, pop prefix levels
                    prefix_stack = prefix_stack[:depth]
                
                # Adjust last prefix for last directory at this level
                if prefix_stack and dirs == []:
                    prefix_stack[-1] = '    '
                
                # Build current prefix
                current_prefix = ''.join(prefix_stack[:-1])
                
                # Yield directory entry
                dir_name = os.path.basename(root)
                yield {
                    "type": "directory",
                    "name": dir_name,
                    "path": rel_path,
                    "prefix": current_prefix,
                    "is_last": False  # Will be adjusted by caller
                }
            
            # Process all files
            for i, filename in enumerate(sorted(files)):
                file_path = os.path.join(root, filename)
                rel_file_path = os.path.relpath(file_path, self.base_directory)
                
                # Skip excluded files
                if rel_file_path in self.excluded_files:
                    continue
                
                # Update file count
                self.stats["total_files"] += 1
                
                # Get file size
                try:
                    file_size = os.path.getsize(file_path)
                    self.stats["total_size"] += file_size
                except (OSError, IOError):
                    file_size = 0
                
                # Determine category if function provided
                category = category_func(file_path) if category_func else None
                
                if category:
                    self.stats["files_by_category"][category] = self.stats["files_by_category"].get(category, 0) + 1
                
                # Calculate file prefix
                is_last_file = (i == len(files) - 1)
                file_prefix = ''.join(prefix_stack) if depth > 0 else ''
                
                # Yield file entry
                yield {
                    "type": "file",
                    "name": filename,
                    "path": rel_file_path,
                    "size": file_size,
                    "category": category,
                    "prefix": file_prefix,
                    "is_last": is_last_file
                }
    
    def build_tree_text(self, category_func: Optional[Callable[[str], str]] = None) -> str:
        """
        Build a text representation of the directory tree.
        
        Args:
            category_func: Function to determine file category
            
        Returns:
            Text representation of the tree
        """
        lines = []
        
        # Iterate through file entries
        for entry in self.stream_tree(category_func):
            if entry["type"] == "directory":
                # Directory entry
                prefix = entry["prefix"]
                conn = '└── ' if entry.get("is_last", False) else '├── '
                lines.append(f"{prefix}{conn}{entry['name']}/")
            else:
                # File entry
                prefix = entry["prefix"]
                conn = '└── ' if entry.get("is_last", False) else '├── '
                lines.append(f"{prefix}{conn}{entry['name']}")
        
        return '\n'.join(lines)
    
    def _walk_with_depth(self) -> Generator[Tuple[str, List[str], List[str]], None, None]:
        """
        Walk the directory tree with depth control.
        
        Yields:
            Tuples of (dirpath, dirnames, filenames) similar to os.walk
        """
        for root, dirs, files in os.walk(self.base_directory, topdown=True):
            # Calculate depth
            rel_path = os.path.relpath(root, self.base_directory)
            depth = 0 if rel_path == '.' else rel_path.count(os.sep) + 1
            
            # Check if we've reached max depth
            if self.max_depth is not None and depth > self.max_depth:
                dirs.clear()  # Don't descend further
            
            # Yield current directory info
            yield root, dirs, files


class ChunkedFileReader:
    """Memory-efficient file reader for large files"""
    
    @staticmethod
    def read_file(file_path: str, chunk_size: int = 4096, max_size: Optional[int] = None) -> Generator[str, None, None]:
        """
        Read a file in chunks to avoid loading it all into memory.
        
        Args:
            file_path: Path to the file
            chunk_size: Size of each chunk in bytes
            max_size: Maximum file size to read (None for no limit)
            
        Yields:
            File content chunks
        """
        # Check if file exceeds max size
        if max_size is not None:
            try:
                file_size = os.path.getsize(file_path)
                if file_size > max_size:
                    yield f"File too large ({file_size} bytes, max {max_size})"
                    return
            except (OSError, IOError) as e:
                yield f"Error getting file size: {e}"
                return
        
        # Read the file in chunks
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            yield f"Error reading file: {e}"
    
    @staticmethod
    def read_binary_file(file_path: str, chunk_size: int = 4096, max_size: Optional[int] = None) -> Generator[bytes, None, None]:
        """
        Read a binary file in chunks.
        
        Args:
            file_path: Path to the file
            chunk_size: Size of each chunk in bytes
            max_size: Maximum file size to read (None for no limit)
            
        Yields:
            File content chunks as bytes
        """
        # Check if file exceeds max size
        if max_size is not None:
            try:
                file_size = os.path.getsize(file_path)
                if file_size > max_size:
                    yield f"File too large ({file_size} bytes, max {max_size})".encode()
                    return
            except (OSError, IOError) as e:
                yield f"Error getting file size: {e}".encode()
                return
        
        # Read the file in chunks
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            yield f"Error reading file: {e}".encode()
