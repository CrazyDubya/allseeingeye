#!/usr/bin/env python3
"""
Asynchronous file processing for AllSeeingEye
"""

import os
import asyncio
import logging
import concurrent.futures
from typing import Dict, Any, List, Set, Optional, Callable, Coroutine

# Configure logging
logger = logging.getLogger("AsyncProcessor")


class AsyncProcessor:
    """Asynchronous file processing utilities"""
    
    def __init__(self, 
                max_workers: Optional[int] = None,
                chunk_size: int = 100,
                semaphore_limit: int = 20):
        """
        Initialize the async processor.
        
        Args:
            max_workers: Maximum number of worker threads (default: CPU count * 5)
            chunk_size: Number of files to process in a batch
            semaphore_limit: Maximum number of concurrent tasks
        """
        self.max_workers = max_workers or min(32, os.cpu_count() * 5)
        self.chunk_size = chunk_size
        self.semaphore = asyncio.Semaphore(semaphore_limit)
        self.loop = None
        self._executor = None
    
    @property
    def executor(self):
        """Get thread pool executor, creating it if needed"""
        if self._executor is None:
            self._executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix="AsyncProcessor"
            )
        return self._executor
    
    async def process_files(self, 
                           files: List[str], 
                           process_func: Callable[[str], Dict[str, Any]],
                           progress_callback: Optional[Callable[[int, int], None]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Process multiple files asynchronously.
        
        Args:
            files: List of file paths to process
            process_func: Function to process each file (must be thread-safe)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary mapping file paths to processing results
        """
        # Store the event loop for use in other methods
        self.loop = asyncio.get_running_loop()
        
        # Results dictionary
        results = {}
        
        # Track progress
        total_files = len(files)
        processed_files = 0
        
        # Process files in chunks
        for i in range(0, total_files, self.chunk_size):
            chunk = files[i:i + self.chunk_size]
            chunk_tasks = []
            
            # Create tasks for this chunk
            for file_path in chunk:
                task = self._process_file_task(file_path, process_func)
                chunk_tasks.append(task)
            
            # Process the chunk
            chunk_results = await asyncio.gather(*chunk_tasks)
            
            # Update results
            for file_path, result in chunk_results:
                results[file_path] = result
            
            # Update progress
            processed_files += len(chunk)
            if progress_callback:
                progress_callback(processed_files, total_files)
        
        return results
    
    async def _process_file_task(self, file_path: str, process_func: Callable[[str], Dict[str, Any]]) -> tuple:
        """
        Process a single file as an async task.
        
        Args:
            file_path: Path to the file
            process_func: Function to process the file
            
        Returns:
            Tuple of (file_path, result)
        """
        async with self.semaphore:
            # Run CPU-bound processing in a thread pool
            try:
                result = await self.loop.run_in_executor(
                    self.executor, process_func, file_path
                )
                return (file_path, result)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                return (file_path, {"error": str(e)})
    
    async def scan_directory(self, 
                           directory: str,
                           include_patterns: Optional[List[str]] = None,
                           exclude_patterns: Optional[List[str]] = None,
                           max_depth: Optional[int] = None) -> List[str]:
        """
        Scan a directory asynchronously to find files.
        
        Args:
            directory: Directory to scan
            include_patterns: List of file patterns to include
            exclude_patterns: List of file patterns to exclude
            max_depth: Maximum directory depth
            
        Returns:
            List of file paths
        """
        loop = asyncio.get_running_loop()
        
        # Run the directory scan in a thread pool to avoid blocking the event loop
        result = await loop.run_in_executor(
            self.executor,
            self._scan_directory_sync,
            directory,
            include_patterns,
            exclude_patterns,
            max_depth
        )
        
        return result
    
    def _scan_directory_sync(self,
                           directory: str,
                           include_patterns: Optional[List[str]] = None,
                           exclude_patterns: Optional[List[str]] = None,
                           max_depth: Optional[int] = None) -> List[str]:
        """
        Synchronous implementation of directory scanning.
        
        Args:
            directory: Directory to scan
            include_patterns: List of file patterns to include
            exclude_patterns: List of file patterns to exclude
            max_depth: Maximum directory depth
            
        Returns:
            List of file paths
        """
        import fnmatch
        
        files = []
        
        # Convert to absolute path
        directory = os.path.abspath(directory)
        
        def should_include(path):
            """Check if a path should be included based on patterns"""
            # Check exclude patterns
            if exclude_patterns:
                for pattern in exclude_patterns:
                    if fnmatch.fnmatch(path, pattern):
                        return False
            
            # Check include patterns
            if include_patterns:
                for pattern in include_patterns:
                    if fnmatch.fnmatch(path, pattern):
                        return True
                return False
            
            return True
        
        # Walk the directory tree
        for root, dirs, filenames in os.walk(directory):
            # Check depth if specified
            if max_depth is not None:
                rel_path = os.path.relpath(root, directory)
                depth = rel_path.count(os.sep) + (0 if rel_path == '.' else 1)
                if depth > max_depth:
                    dirs.clear()  # Don't descend any deeper
                    continue
            
            # Filter and add files
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if should_include(file_path):
                    files.append(file_path)
        
        return files
    
    def shutdown(self):
        """Shut down the executor"""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
