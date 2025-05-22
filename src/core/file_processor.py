#!/usr/bin/env python3
"""
File processing functionality for AllSeeingEye
"""

import os
import datetime
import mimetypes
import logging
from typing import Dict, Any, Optional, List, Set

# Import security utilities
from src.security.security_utils import SecurityUtils

# Import file category utils
from src.core.file_category import FileCategory

# Configure logging
logger = logging.getLogger("FileProcessor")


class FileProcessor:
    """Handles file processing operations for AllSeeingEye"""
    
    def __init__(self, 
                max_file_size: int = 1024 * 1024,  # 1MB default
                active_categories: Optional[Set[str]] = None,
                security_checks: bool = True):
        """
        Initialize the file processor.
        
        Args:
            max_file_size: Maximum file size to process in bytes
            active_categories: Set of categories to process
            security_checks: Whether to perform security checks
        """
        self.max_file_size = max_file_size
        self.active_categories = active_categories or set(FileCategory.CATEGORIES.keys())
        self.security_checks = security_checks
        
        # Initialize file type detection
        mimetypes.init()
    
    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get file metadata including size, modification time, and mime type.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file metadata
        """
        file_stat = os.stat(file_path)
        size = file_stat.st_size
        modified_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
        
        # Determine mime type
        mime_type, _ = mimetypes.guess_type(file_path)
        
        return {
            "size": size,
            "size_formatted": self.format_size(size),
            "last_modified": modified_time.strftime("%Y-%m-%d %H:%M:%S"),
            "mime_type": mime_type
        }
    
    def format_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Human-readable size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
    
    def should_process_file(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Determine if a file should be processed based on rules.
        
        Args:
            file_path: Path to the file
            metadata: File metadata
            
        Returns:
            True if the file should be processed, False otherwise
        """
        # Check if exceeds size limit
        if metadata["size"] > self.max_file_size:
            logger.debug(f"Skipping {file_path} due to size: {metadata['size_formatted']}")
            return False
        
        # Check if it's a binary file
        if metadata["mime_type"] and FileCategory.is_binary_mimetype(metadata["mime_type"]):
            logger.debug(f"Skipping binary file {file_path} with mime type {metadata['mime_type']}")
            return False
        
        # Check file extension and category
        _, ext = os.path.splitext(file_path)
        category = FileCategory.get_category_for_extension(ext)
        
        # Check if category should be included
        if category not in self.active_categories:
            logger.debug(f"Skipping {file_path} due to category: {category}")
            return False
        
        return True
    
    def get_file_category(self, file_path: str) -> str:
        """
        Determine the category for a file based on its extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Category string
        """
        _, ext = os.path.splitext(file_path)
        return FileCategory.get_category_for_extension(ext)
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single file and return its content and metadata.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file content and metadata
        """
        result = {}
        
        try:
            # Check path safety if security checks are enabled
            if self.security_checks:
                is_valid, error = SecurityUtils.validate_path(file_path)
                if not is_valid:
                    logger.error(f"Security validation failed for {file_path}: {error}")
                    result['error'] = f"Security validation failed: {error}"
                    return result
            
            # Get file metadata
            metadata = self.get_file_metadata(file_path)
            result.update(metadata)
            
            # Check if file should be processed
            if not self.should_process_file(file_path, metadata):
                return result
            
            # Get file category
            category = self.get_file_category(file_path)
            
            # If it's a text category, read the content
            if FileCategory.is_text_category(category):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        content = file.read()
                        
                        # Perform security checks on content if enabled
                        if self.security_checks:
                            is_safe, reason = SecurityUtils.is_safe_file_content(content)
                            if not is_safe:
                                logger.warning(f"Security check flagged content in {file_path}: {reason}")
                                result['security_warning'] = reason
                            
                            # Sanitize content if emojis are detected
                            sanitized_content, emoji_count = SecurityUtils.sanitize_emojis(content)
                            if emoji_count > 0:
                                logger.info(f"Sanitized {emoji_count} emojis in {file_path}")
                                content = sanitized_content
                        
                        result['content'] = content
                        result['line_count'] = content.count('\n') + 1
                        
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {e}")
                    result['error'] = str(e)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            result['error'] = str(e)
        
        return result
    
    def list_directory(self, directory: str) -> List[str]:
        """
        List directory contents in a cross-platform way.
        
        Args:
            directory: Directory path to list
            
        Returns:
            List of directory entries
        """
        try:
            # Check directory safety if security checks are enabled
            if self.security_checks:
                is_safe, reason = SecurityUtils.ensure_directory_is_safe(directory)
                if not is_safe:
                    logger.error(f"Security check failed for directory {directory}: {reason}")
                    return []
            
            return os.listdir(directory)
        except Exception as e:
            logger.error(f"Error listing directory {directory}: {e}")
            return []
