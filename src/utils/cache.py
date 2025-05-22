#!/usr/bin/env python3
"""
Caching utilities for AllSeeingEye
"""

import os
import json
import time
import hashlib
import logging
import tempfile
from typing import Dict, Any, Optional, List, Union, Tuple, Callable

# Configure logging
logger = logging.getLogger("Cache")


class Cache:
    """Base cache implementation"""
    
    def __init__(self, cache_dir: Optional[str] = None, max_age: int = 86400):
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory to store cached data (default: temp directory)
            max_age: Maximum age of cached items in seconds (default: 24 hours)
        """
        if cache_dir:
            self.cache_dir = cache_dir
        else:
            self.cache_dir = os.path.join(
                tempfile.gettempdir(),
                "allseeingeye_cache"
            )
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.max_age = max_age
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get an item from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            # Check if cache is expired
            file_age = time.time() - os.path.getmtime(cache_file)
            if file_age > self.max_age:
                logger.debug(f"Cache expired for key {key}")
                return None
            
            # Read cache file
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
            
            return cache_data.get("value")
            
        except Exception as e:
            logger.warning(f"Error reading cache for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set an item in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            
        Returns:
            True if successful, False otherwise
        """
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        try:
            # Create cache data
            cache_data = {
                "timestamp": time.time(),
                "value": value
            }
            
            # Write to cache file
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)
            
            return True
            
        except Exception as e:
            logger.warning(f"Error writing cache for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete an item from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        
        if not os.path.exists(cache_file):
            return True
        
        try:
            os.remove(cache_file)
            return True
            
        except Exception as e:
            logger.warning(f"Error deleting cache for key {key}: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all items from the cache.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".json"):
                    os.remove(os.path.join(self.cache_dir, filename))
            return True
            
        except Exception as e:
            logger.warning(f"Error clearing cache: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "cache_dir": self.cache_dir,
            "max_age": self.max_age,
            "total_items": 0,
            "total_size_bytes": 0,
            "expired_items": 0,
            "item_ages": []
        }
        
        try:
            now = time.time()
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.cache_dir, filename)
                    
                    # Count item
                    stats["total_items"] += 1
                    
                    # Get file size
                    file_size = os.path.getsize(filepath)
                    stats["total_size_bytes"] += file_size
                    
                    # Get file age
                    file_age = now - os.path.getmtime(filepath)
                    stats["item_ages"].append(file_age)
                    
                    # Check if expired
                    if file_age > self.max_age:
                        stats["expired_items"] += 1
            
            # Calculate average age
            if stats["item_ages"]:
                stats["average_age"] = sum(stats["item_ages"]) / len(stats["item_ages"])
            else:
                stats["average_age"] = 0
            
            # Format total size
            stats["total_size_formatted"] = self._format_size(stats["total_size_bytes"])
            
            return stats
            
        except Exception as e:
            logger.warning(f"Error getting cache stats: {e}")
            return stats
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024


class MemoryCache:
    """In-memory cache implementation"""
    
    def __init__(self, max_items: int = 1000, max_age: int = 86400):
        """
        Initialize the memory cache.
        
        Args:
            max_items: Maximum number of items to store
            max_age: Maximum age of cached items in seconds (default: 24 hours)
        """
        self.cache = {}
        self.max_items = max_items
        self.max_age = max_age
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get an item from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found or expired
        """
        if key not in self.cache:
            return None
        
        item = self.cache[key]
        
        # Check if expired
        if time.time() - item["timestamp"] > self.max_age:
            # Remove expired item
            del self.cache[key]
            return None
        
        return item["value"]
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set an item in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            
        Returns:
            True if successful, False otherwise
        """
        # Check if we need to evict items
        if len(self.cache) >= self.max_items and key not in self.cache:
            # Remove the oldest item
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k]["timestamp"])
            del self.cache[oldest_key]
        
        # Store the item
        self.cache[key] = {
            "timestamp": time.time(),
            "value": value
        }
        
        return True
    
    def delete(self, key: str) -> bool:
        """
        Delete an item from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        if key in self.cache:
            del self.cache[key]
        
        return True
    
    def clear(self) -> bool:
        """
        Clear all items from the cache.
        
        Returns:
            True if successful, False otherwise
        """
        self.cache = {}
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        now = time.time()
        
        stats = {
            "type": "memory",
            "max_items": self.max_items,
            "max_age": self.max_age,
            "total_items": len(self.cache),
            "expired_items": 0,
            "item_ages": []
        }
        
        # Calculate items and ages
        for key, item in self.cache.items():
            age = now - item["timestamp"]
            stats["item_ages"].append(age)
            
            if age > self.max_age:
                stats["expired_items"] += 1
        
        # Calculate average age
        if stats["item_ages"]:
            stats["average_age"] = sum(stats["item_ages"]) / len(stats["item_ages"])
        else:
            stats["average_age"] = 0
        
        return stats


def cached(cache: Optional[Union[Cache, MemoryCache]] = None, key_fn: Optional[Callable] = None):
    """
    Decorator for caching function results.
    
    Args:
        cache: Cache instance to use (creates a new one if None)
        key_fn: Function to generate cache keys (default: based on args and kwargs)
        
    Returns:
        Decorated function
    """
    # Create default cache if none provided
    if cache is None:
        cache = MemoryCache()
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_fn:
                key = key_fn(*args, **kwargs)
            else:
                # Default key generation based on function name, args, and kwargs
                key_parts = [func.__name__]
                
                # Add args
                for arg in args:
                    key_parts.append(str(arg))
                
                # Add kwargs
                for k, v in sorted(kwargs.items()):
                    key_parts.append(f"{k}={v}")
                
                # Create key string and hash it
                key_str = ":".join(key_parts)
                key = hashlib.md5(key_str.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Cache miss, call function
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(key, result)
            
            return result
        
        return wrapper
    
    return decorator
