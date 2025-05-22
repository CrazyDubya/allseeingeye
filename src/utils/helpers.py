#!/usr/bin/env python3
"""
Helper utilities for AllSeeingEye
"""

import os
import re
import hashlib
import platform
import logging
from typing import Dict, Any, Optional, List, Set, Tuple

# Configure logging
logger = logging.getLogger("Helpers")


def get_platform_info() -> Dict[str, str]:
    """
    Get platform information.
    
    Returns:
        Dictionary with platform info
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }


def compute_file_hash(file_path: str, algorithm: str = "sha256") -> Optional[str]:
    """
    Compute hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (md5, sha1, sha256)
        
    Returns:
        Hash string or None if error
    """
    if not os.path.isfile(file_path):
        logger.error(f"File not found: {file_path}")
        return None
    
    try:
        hash_obj = None
        if algorithm == "md5":
            hash_obj = hashlib.md5()
        elif algorithm == "sha1":
            hash_obj = hashlib.sha1()
        else:  # Default to sha256
            hash_obj = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # Read and update hash in chunks to save memory
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return None


def is_binary_file(file_path: str) -> bool:
    """
    Check if a file is binary.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if binary, False otherwise
    """
    # Check if file exists
    if not os.path.isfile(file_path):
        logger.error(f"File not found: {file_path}")
        return False
    
    # Check file extension first
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    # Known binary extensions
    binary_extensions = {
        '.exe', '.dll', '.so', '.dylib', '.bin', '.dat', '.pyc', '.class',
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.tif', '.tiff',
        '.mp3', '.mp4', '.avi', '.mov', '.mkv', '.wav', '.flac', '.ogg',
        '.zip', '.tar', '.gz', '.tgz', '.7z', '.rar', '.bz2', '.xz',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'
    }
    
    if ext in binary_extensions:
        return True
    
    # Try to read the first 8KB of the file
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(8 * 1024)
        
        # Empty files are considered text
        if not chunk:
            return False
        
        # Check for null bytes (a strong indicator of binary content)
        if b'\x00' in chunk:
            return True
        
        # Try to decode as text
        try:
            chunk.decode('utf-8')
            return False  # Successfully decoded as text
        except UnicodeDecodeError:
            try:
                chunk.decode('latin-1')  # Try another common encoding
                return False
            except UnicodeDecodeError:
                return True  # Could not decode, likely binary
        
    except Exception as e:
        logger.error(f"Error checking if {file_path} is binary: {e}")
        return True  # Assume binary on error
    
    return False


def find_similar_files(directory: str,
                       min_similarity: float = 0.8,
                       file_extensions: Optional[List[str]] = None) -> List[Tuple[str, str, float]]:
    """
    Find similar files in a directory.
    
    Args:
        directory: Directory to search
        min_similarity: Minimum similarity threshold (0.0 to 1.0)
        file_extensions: List of file extensions to consider
        
    Returns:
        List of tuples (file1, file2, similarity)
    """
    similar_files = []
    
    # Filter files
    all_files = []
    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            
            # Skip binary files
            if is_binary_file(file_path):
                continue
            
            # Check extension
            if file_extensions:
                _, ext = os.path.splitext(file_path)
                if ext.lower() not in file_extensions:
                    continue
            
            all_files.append(file_path)
    
    # Compare files
    for i, file1 in enumerate(all_files):
        for file2 in all_files[i+1:]:
            similarity = calculate_file_similarity(file1, file2)
            if similarity >= min_similarity:
                similar_files.append((file1, file2, similarity))
    
    # Sort by similarity (highest first)
    similar_files.sort(key=lambda x: x[2], reverse=True)
    
    return similar_files


def calculate_file_similarity(file1: str, file2: str) -> float:
    """
    Calculate similarity between two text files.
    
    Args:
        file1: Path to first file
        file2: Path to second file
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    try:
        # Read files
        with open(file1, 'r', encoding='utf-8', errors='ignore') as f:
            content1 = f.read()
        
        with open(file2, 'r', encoding='utf-8', errors='ignore') as f:
            content2 = f.read()
        
        # Simple token-based comparison
        tokens1 = set(re.findall(r'\w+', content1.lower()))
        tokens2 = set(re.findall(r'\w+', content2.lower()))
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        return intersection / union
    
    except Exception as e:
        logger.error(f"Error calculating similarity between {file1} and {file2}: {e}")
        return 0.0


def normalize_path(path: str) -> str:
    """
    Normalize a file path.
    
    Args:
        path: Path to normalize
        
    Returns:
        Normalized path
    """
    return os.path.normpath(os.path.abspath(path))


def is_subpath(path: str, base_path: str) -> bool:
    """
    Check if a path is a subpath of another path.
    
    Args:
        path: Path to check
        base_path: Base path
        
    Returns:
        True if path is a subpath of base_path, False otherwise
    """
    path = normalize_path(path)
    base_path = normalize_path(base_path)
    
    # On Windows, convert both paths to lowercase for case-insensitive comparison
    if os.name == 'nt':
        path = path.lower()
        base_path = base_path.lower()
    
    return path.startswith(base_path)
