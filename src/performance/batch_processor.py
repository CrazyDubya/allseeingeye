#!/usr/bin/env python3
"""
Batch processing utilities for AllSeeingEye
"""

import os
import time
import logging
import multiprocessing
from typing import Dict, Any, List, Set, Optional, Callable, Generator, Tuple

# Configure logging
logger = logging.getLogger("BatchProcessor")


class BatchProcessor:
    """Process files in batches for better performance"""
    
    def __init__(self, 
                chunk_size: int = 100,
                max_workers: Optional[int] = None,
                progress_callback: Optional[Callable[[int, int], None]] = None):
        """
        Initialize the batch processor.
        
        Args:
            chunk_size: Number of files to process in a batch
            max_workers: Maximum number of worker processes (default: CPU count)
            progress_callback: Optional callback for progress updates
        """
        self.chunk_size = chunk_size
        self.max_workers = max_workers or max(1, multiprocessing.cpu_count())
        self.progress_callback = progress_callback
    
    def process_files(self, 
                     files: List[str],
                     process_func: Callable[[str], Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Process files in batches.
        
        Args:
            files: List of file paths to process
            process_func: Function to process each file
            
        Returns:
            Dictionary mapping file paths to processing results
        """
        total_files = len(files)
        results = {}
        processed_files = 0
        start_time = time.time()
        
        # Process in chunks to reduce memory usage
        for i in range(0, total_files, self.chunk_size):
            chunk = files[i:i + self.chunk_size]
            chunk_results = self._process_chunk(chunk, process_func)
            
            # Add chunk results to overall results
            results.update(chunk_results)
            
            # Update progress
            processed_files += len(chunk)
            if self.progress_callback:
                self.progress_callback(processed_files, total_files)
            
            # Log progress
            elapsed = time.time() - start_time
            files_per_second = processed_files / elapsed if elapsed > 0 else 0
            logger.info(f"Processed {processed_files}/{total_files} files "
                        f"({processed_files/total_files*100:.1f}%) - "
                        f"{files_per_second:.1f} files/sec")
        
        return results
    
    def _process_chunk(self, 
                      files: List[str],
                      process_func: Callable[[str], Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Process a chunk of files.
        
        Args:
            files: List of file paths in this chunk
            process_func: Function to process each file
            
        Returns:
            Dictionary mapping file paths to processing results
        """
        results = {}
        
        # If only one worker or very few files, process serially
        if self.max_workers == 1 or len(files) <= 5:
            for file_path in files:
                try:
                    results[file_path] = process_func(file_path)
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    results[file_path] = {"error": str(e)}
            
            return results
        
        # Process in parallel using a process pool
        with multiprocessing.Pool(self.max_workers) as pool:
            # Wrap the process function to handle exceptions
            def safe_process(file_path):
                try:
                    return (file_path, process_func(file_path))
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    return (file_path, {"error": str(e)})
            
            # Process files in parallel
            for file_path, result in pool.imap_unordered(safe_process, files):
                results[file_path] = result
        
        return results


class StreamingBatchProcessor:
    """Process files in batches and stream results"""
    
    def __init__(self, 
                chunk_size: int = 100,
                max_workers: Optional[int] = None):
        """
        Initialize the streaming batch processor.
        
        Args:
            chunk_size: Number of files to process in a batch
            max_workers: Maximum number of worker processes (default: CPU count)
        """
        self.chunk_size = chunk_size
        self.max_workers = max_workers or max(1, multiprocessing.cpu_count())
    
    def stream_process(self, 
                      files: List[str],
                      process_func: Callable[[str], Dict[str, Any]]) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
        """
        Process files in batches and stream results as they become available.
        
        Args:
            files: List of file paths to process
            process_func: Function to process each file
            
        Yields:
            Tuples of (file_path, result) as they are processed
        """
        total_files = len(files)
        processed_files = 0
        start_time = time.time()
        
        # Process in chunks to reduce memory usage
        for i in range(0, total_files, self.chunk_size):
            chunk = files[i:i + self.chunk_size]
            
            # Process this chunk
            for file_path, result in self._stream_chunk(chunk, process_func):
                yield (file_path, result)
                
                # Update processed count
                processed_files += 1
                
                # Log progress periodically
                if processed_files % 100 == 0 or processed_files == total_files:
                    elapsed = time.time() - start_time
                    files_per_second = processed_files / elapsed if elapsed > 0 else 0
                    logger.info(f"Processed {processed_files}/{total_files} files "
                                f"({processed_files/total_files*100:.1f}%) - "
                                f"{files_per_second:.1f} files/sec")
    
    def _stream_chunk(self, 
                     files: List[str],
                     process_func: Callable[[str], Dict[str, Any]]) -> Generator[Tuple[str, Dict[str, Any]], None, None]:
        """
        Process a chunk of files and stream results.
        
        Args:
            files: List of file paths in this chunk
            process_func: Function to process each file
            
        Yields:
            Tuples of (file_path, result) as they are processed
        """
        # If only one worker or very few files, process serially
        if self.max_workers == 1 or len(files) <= 5:
            for file_path in files:
                try:
                    result = process_func(file_path)
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    result = {"error": str(e)}
                
                yield (file_path, result)
            
            return
        
        # Process in parallel using a process pool
        with multiprocessing.Pool(self.max_workers) as pool:
            # Wrap the process function to handle exceptions
            def safe_process(file_path):
                try:
                    return (file_path, process_func(file_path))
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    return (file_path, {"error": str(e)})
            
            # Process files in parallel and yield results as they become available
            for result in pool.imap_unordered(safe_process, files):
                yield result


class FileTypeDispatcher:
    """Dispatch files to different processors based on file type"""
    
    def __init__(self, 
                file_type_func: Callable[[str], str],
                processors: Dict[str, Callable[[str], Dict[str, Any]]],
                default_processor: Optional[Callable[[str], Dict[str, Any]]] = None,
                max_workers: Optional[int] = None,
                chunk_size: int = 100):
        """
        Initialize the file type dispatcher.
        
        Args:
            file_type_func: Function to determine file type
            processors: Dictionary mapping file types to processor functions
            default_processor: Optional default processor for unknown types
            max_workers: Maximum number of worker processes per type
            chunk_size: Number of files to process in a batch
        """
        self.file_type_func = file_type_func
        self.processors = processors
        self.default_processor = default_processor
        self.max_workers = max_workers
        self.chunk_size = chunk_size
    
    def process_files(self, files: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Process files by dispatching to type-specific processors.
        
        Args:
            files: List of file paths to process
            
        Returns:
            Dictionary mapping file paths to processing results
        """
        # Group files by type
        files_by_type = {}
        
        for file_path in files:
            file_type = self.file_type_func(file_path)
            if file_type not in files_by_type:
                files_by_type[file_type] = []
            files_by_type[file_type].append(file_path)
        
        # Process each file type in parallel
        results = {}
        
        # Create workers for each file type
        for file_type, type_files in files_by_type.items():
            processor = self.processors.get(file_type, self.default_processor)
            if processor is None:
                logger.warning(f"No processor for file type '{file_type}', skipping {len(type_files)} files")
                continue
            
            # Create a batch processor for this file type
            batch_processor = BatchProcessor(
                chunk_size=self.chunk_size,
                max_workers=self.max_workers
            )
            
            # Process files of this type
            type_results = batch_processor.process_files(type_files, processor)
            results.update(type_results)
        
        return results


class DiskIOLimiter:
    """Limit disk I/O operations to prevent overwhelming the system"""
    
    def __init__(self, 
                max_concurrent_reads: int = 10,
                read_delay: float = 0.01,
                max_read_size_mb: float = 10.0):
        """
        Initialize the disk I/O limiter.
        
        Args:
            max_concurrent_reads: Maximum number of concurrent read operations
            read_delay: Delay between reads in seconds
            max_read_size_mb: Maximum size to read at once in MB
        """
        self.max_concurrent_reads = max_concurrent_reads
        self.read_delay = read_delay
        self.max_read_size_bytes = int(max_read_size_mb * 1024 * 1024)
        self._semaphore = multiprocessing.Semaphore(max_concurrent_reads)
    
    def read_file(self, file_path: str) -> str:
        """
        Read a file with I/O limiting.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content
        """
        # Check file size first
        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.max_read_size_bytes:
                return f"File too large ({file_size} bytes, max {self.max_read_size_bytes})"
        except (OSError, IOError) as e:
            return f"Error getting file size: {e}"
        
        # Acquire semaphore to limit concurrent reads
        with self._semaphore:
            try:
                # Read the file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Add delay to prevent overwhelming the disk
                time.sleep(self.read_delay)
                
                return content
            except Exception as e:
                return f"Error reading file: {e}"
    
    def read_binary_file(self, file_path: str) -> bytes:
        """
        Read a binary file with I/O limiting.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File content as bytes
        """
        # Check file size first
        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.max_read_size_bytes:
                return f"File too large ({file_size} bytes, max {self.max_read_size_bytes})".encode()
        except (OSError, IOError) as e:
            return f"Error getting file size: {e}".encode()
        
        # Acquire semaphore to limit concurrent reads
        with self._semaphore:
            try:
                # Read the file
                with open(file_path, 'rb') as f:
                    content = f.read()
                
                # Add delay to prevent overwhelming the disk
                time.sleep(self.read_delay)
                
                return content
            except Exception as e:
                return f"Error reading file: {e}".encode()
