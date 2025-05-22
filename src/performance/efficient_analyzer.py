#!/usr/bin/env python3
"""
Memory and performance efficient analyzer for AllSeeingEye
"""

import os
import time
import asyncio
import logging
import datetime
from typing import Dict, Any, List, Set, Optional, Callable, Generator, Tuple, Union

# Import core components
from src.core.file_category import FileCategory
from src.formatters.output_format import OutputFormat

# Import performance utilities
from src.performance.profiler import Profiler
from src.performance.async_processor import AsyncProcessor
from src.performance.efficient_tree import StreamingTreeBuilder, ChunkedFileReader
from src.performance.batch_processor import BatchProcessor, DiskIOLimiter

# Import security utilities
from src.security.security_utils import SecurityUtils

# Configure logging
logger = logging.getLogger("EfficientAnalyzer")


class ProgressTracker:
    """Simple progress tracking utility"""
    
    def __init__(self, total: int = 100, update_interval: float = 0.5):
        """
        Initialize the progress tracker.
        
        Args:
            total: Total number of items
            update_interval: Minimum time between progress updates in seconds
        """
        self.total = total
        self.current = 0
        self.start_time = time.time()
        self.update_interval = update_interval
        self.last_update_time = 0
        self.callbacks = []
    
    def update(self, current: int, force: bool = False) -> None:
        """
        Update progress.
        
        Args:
            current: Current progress value
            force: Force update even if interval hasn't elapsed
        """
        self.current = current
        
        # Check if we should send an update
        now = time.time()
        if force or (now - self.last_update_time) >= self.update_interval:
            self.last_update_time = now
            
            # Calculate progress percentage and estimated time remaining
            progress = self.current / self.total if self.total > 0 else 0
            elapsed = now - self.start_time
            
            # Calculate rate and ETA
            rate = self.current / elapsed if elapsed > 0 else 0
            eta = (self.total - self.current) / rate if rate > 0 else 0
            
            # Call all registered callbacks
            progress_data = {
                "current": self.current,
                "total": self.total,
                "progress": progress,
                "elapsed": elapsed,
                "eta": eta,
                "rate": rate
            }
            
            for callback in self.callbacks:
                try:
                    callback(progress_data)
                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")
    
    def add_callback(self, callback: Callable[[Dict[str, float]], None]) -> None:
        """
        Add a progress callback.
        
        Args:
            callback: Function that takes a progress data dictionary
        """
        self.callbacks.append(callback)
    
    def reset(self, total: Optional[int] = None) -> None:
        """
        Reset progress.
        
        Args:
            total: New total value (optional)
        """
        if total is not None:
            self.total = total
        
        self.current = 0
        self.start_time = time.time()
        self.last_update_time = 0


class EfficientAnalyzer:
    """Memory and performance efficient analyzer"""
    
    def __init__(self,
                 directory: Optional[str] = None,
                 excluded_dirs: Optional[List[str]] = None,
                 excluded_files: Optional[List[str]] = None,
                 included_categories: Optional[List[str]] = None,
                 excluded_categories: Optional[List[str]] = None,
                 max_file_size: int = 1024 * 1024,  # 1MB default
                 max_files: int = 1000,
                 output_format: str = "markdown",
                 security_checks: bool = True,
                 max_workers: Optional[int] = None,
                 chunk_size: int = 100,
                 progress_callback: Optional[Callable[[Dict[str, float]], None]] = None,
                 verbose: bool = False):
        """
        Initialize the efficient analyzer.
        
        Args:
            directory: Directory to analyze (default: current directory)
            excluded_dirs: Directories to exclude
            excluded_files: Files to exclude
            included_categories: File categories to include
            excluded_categories: File categories to exclude
            max_file_size: Maximum file size to process in bytes
            max_files: Maximum number of files to process
            output_format: Output format (markdown, json, text)
            security_checks: Whether to perform security checks
            max_workers: Maximum number of worker processes
            chunk_size: Number of files to process in a batch
            progress_callback: Optional callback for progress updates
            verbose: Whether to enable verbose logging
        """
        # Configure logging
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Set base directory
        self.directory = os.path.abspath(directory or os.getcwd())
        
        # Process exclusions
        self.excluded_dirs = set(excluded_dirs or [])
        self.excluded_files = set(excluded_files or [])
        
        # Process included and excluded categories
        self.all_categories = set(FileCategory.CATEGORIES.keys())
        self.included_categories = set(included_categories or self.all_categories)
        self.excluded_categories = set(excluded_categories or [])
        self.active_categories = self.included_categories - self.excluded_categories
        
        # Set other parameters
        self.max_file_size = max_file_size
        self.max_files = max_files
        self.output_format = output_format
        self.security_checks = security_checks
        self.max_workers = max_workers or max(1, os.cpu_count())
        self.chunk_size = chunk_size
        
        # Create progress tracker
        self.progress = ProgressTracker()
        if progress_callback:
            self.progress.add_callback(progress_callback)
        
        # Add default progress logger
        def log_progress(data):
            if data["current"] % 100 == 0 or data["current"] == data["total"]:
                logger.info(f"Progress: {data['current']}/{data['total']} "
                            f"({data['progress']*100:.1f}%) - "
                            f"ETA: {data['eta']:.1f}s")
        
        self.progress.add_callback(log_progress)
        
        # Create performance profiler
        self.profiler = Profiler(enabled=verbose)
        
        # Initialize statistics
        self.stats = {
            "start_time": datetime.datetime.now()
        }
        
        # Create utilities
        self.io_limiter = DiskIOLimiter(
            max_concurrent_reads=min(20, self.max_workers * 2),
            read_delay=0.01
        )
    
    def _get_category_for_file(self, file_path: str) -> str:
        """
        Get category for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Category string
        """
        _, ext = os.path.splitext(file_path)
        return FileCategory.get_category_for_extension(ext)
    
    def _should_process_file(self, file_path: str) -> bool:
        """
        Check if a file should be processed.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be processed, False otherwise
        """
        # Check if it matches excluded patterns
        rel_path = os.path.relpath(file_path, self.directory)
        if rel_path in self.excluded_files:
            return False
        
        # Check file size
        try:
            size = os.path.getsize(file_path)
            if size > self.max_file_size:
                logger.debug(f"Skipping {file_path} due to size: {size}")
                return False
        except (OSError, IOError):
            logger.debug(f"Skipping {file_path} due to error getting file size")
            return False
        
        # Check file category
        category = self._get_category_for_file(file_path)
        if category not in self.active_categories:
            logger.debug(f"Skipping {file_path} due to category: {category}")
            return False
        
        # Check if it's a binary file
        try:
            if category in ["binary", "archive", "media"]:
                return False
            
            # Quick check for binary content
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                if b'\x00' in chunk:
                    logger.debug(f"Skipping {file_path} as it appears to be binary")
                    return False
        except Exception:
            return False
        
        return True
    
    def _process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a single file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        result = {}
        
        try:
            # Check security if enabled
            if self.security_checks:
                is_valid, error = SecurityUtils.validate_path(file_path)
                if not is_valid:
                    logger.warning(f"Security validation failed for {file_path}: {error}")
                    return {"error": f"Security validation failed: {error}"}
            
            # Get file metadata
            file_stat = os.stat(file_path)
            size = file_stat.st_size
            modified_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
            
            result = {
                "size": size,
                "size_formatted": self._format_size(size),
                "last_modified": modified_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            # Get file category
            category = self._get_category_for_file(file_path)
            result["category"] = category
            
            # Read file content for text categories
            if FileCategory.is_text_category(category):
                # Read content with I/O limiting
                content = self.io_limiter.read_file(file_path)
                
                # Perform security checks if enabled
                if self.security_checks and content:
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
                
                # Count lines
                result['line_count'] = content.count('\n') + 1
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            result['error'] = str(e)
        
        return result
    
    def _format_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
    
    async def run_async(self) -> str:
        """
        Run the analysis asynchronously.
        
        Returns:
            Path to the output file
        """
        # Start profiling
        self.profiler.start()
        self.profiler.add_event("analysis_start")
        
        # Start timing
        start_time = time.time()
        
        logger.info(f"Analyzing directory: {self.directory}")
        logger.info(f"Output format: {self.output_format}")
        
        # First, scan the directory to find files
        self.profiler.add_event("scanning_start")
        logger.info("Scanning directory...")
        
        # Create async processor
        processor = AsyncProcessor(
            max_workers=self.max_workers,
            chunk_size=self.chunk_size
        )
        
        # Get all files recursively
        all_files = []
        for root, _, files in os.walk(self.directory):
            # Skip excluded directories
            rel_path = os.path.relpath(root, self.directory)
            if rel_path in self.excluded_dirs or any(d in rel_path.split(os.sep) for d in self.excluded_dirs):
                continue
            
            # Add files
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
        
        self.profiler.add_event("scanning_complete", {"file_count": len(all_files)})
        logger.info(f"Found {len(all_files)} files.")
        
        # Filter files that should be processed
        self.profiler.add_event("filtering_start")
        
        # Filter in chunks to avoid memory spikes
        processable_files = []
        
        # Use executor for file filtering (CPU bound)
        loop = asyncio.get_running_loop()
        
        # Filter files in chunks
        for i in range(0, len(all_files), self.chunk_size):
            chunk = all_files[i:i+self.chunk_size]
            
            # Filter this chunk
            filtered_chunk = await loop.run_in_executor(
                None,  # Use default executor
                lambda files: [f for f in files if self._should_process_file(f)],
                chunk
            )
            
            processable_files.extend(filtered_chunk)
            
            # Stop if we hit the file limit
            if len(processable_files) >= self.max_files:
                processable_files = processable_files[:self.max_files]
                logger.info(f"Reached file limit of {self.max_files} files")
                break
        
        self.profiler.add_event("filtering_complete", {"processable_count": len(processable_files)})
        logger.info(f"Selected {len(processable_files)} files for processing.")
        
        # Set up progress tracking
        self.progress.reset(len(processable_files))
        
        # Process files
        self.profiler.add_event("processing_start")
        logger.info("Processing files...")
        
        # Dictionary to store processed files by category
        files_content = {}
        
        # Update progress as files are processed
        def update_progress(current, total):
            self.progress.update(current)
        
        # Process files asynchronously
        results = await processor.process_files(
            processable_files,
            self._process_file,
            update_progress
        )
        
        # Organize results by category
        for file_path, result in results.items():
            category = result.get("category", "other")
            
            if category not in files_content:
                files_content[category] = {}
            
            # Store using relative path
            rel_path = os.path.relpath(file_path, self.directory)
            files_content[category][rel_path] = result
            
            # Update stats
            self.stats["total_files"] = self.stats.get("total_files", 0) + 1
            self.stats["total_size"] = self.stats.get("total_size", 0) + result.get("size", 0)
            self.stats["total_lines"] = self.stats.get("total_lines", 0) + result.get("line_count", 0)
            
            # Update category stats
            if "files_by_category" not in self.stats:
                self.stats["files_by_category"] = {}
            
            self.stats["files_by_category"][category] = self.stats["files_by_category"].get(category, 0) + 1
        
        self.profiler.add_event("processing_complete")
        
        # Build directory tree
        self.profiler.add_event("tree_building_start")
        logger.info("Building directory tree...")
        
        # Use streaming tree builder for memory efficiency
        tree_builder = StreamingTreeBuilder(
            base_directory=self.directory,
            excluded_dirs=self.excluded_dirs,
            excluded_files=self.excluded_files
        )
        
        # Build the tree
        directory_structure = tree_builder.build_tree_text(self._get_category_for_file)
        
        # Update stats from tree builder
        self.stats["total_dirs"] = tree_builder.stats["total_dirs"]
        
        self.profiler.add_event("tree_building_complete")
        
        # Create codebase summary
        self.profiler.add_event("summary_creation_start")
        logger.info("Creating codebase summary...")
        
        summary = []
        
        # Basic summary information
        summary.append("This codebase contains:")
        
        # Count files by type
        for category, count in self.stats.get('files_by_category', {}).items():
            if count > 0:
                description = FileCategory.get_description(category)
                summary.append(f"- {count} {description}")
        
        # Top-level directories
        top_dirs = [d for d in os.listdir(self.directory)
                    if os.path.isdir(os.path.join(self.directory, d))
                    and d not in self.excluded_dirs]
        
        if top_dirs:
            summary.append("\nMain directories:")
            for directory in sorted(top_dirs):
                dir_path = os.path.join(self.directory, directory)
                try:
                    file_count = sum(len(files) for _, _, files in os.walk(dir_path))
                    summary.append(f"- {directory}/: {file_count} files")
                except Exception as e:
                    logger.error(f"Error counting files in {dir_path}: {e}")
                    summary.append(f"- {directory}/: Error counting files")
        
        codebase_summary = "\n".join(summary)
        self.profiler.add_event("summary_creation_complete")
        
        # Format size in stats
        self.stats["total_size_formatted"] = self._format_size(self.stats.get("total_size", 0))
        
        # Add end time and duration
        self.stats["end_time"] = datetime.datetime.now()
        self.stats["duration"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        # Generate output
        self.profiler.add_event("output_generation_start")
        logger.info(f"Generating {self.output_format} output...")
        
        # Generate output based on format
        if self.output_format == "markdown":
            output = OutputFormat.format_markdown(directory_structure, files_content,
                                                 self.stats, codebase_summary)
        elif self.output_format == "json":
            output = OutputFormat.format_json(directory_structure, files_content,
                                             self.stats, codebase_summary)
        else:  # Default to text
            output = OutputFormat.format_text(directory_structure, files_content,
                                             self.stats, codebase_summary)
        
        self.profiler.add_event("output_generation_complete")
        
        # Determine output filename based on format
        output_filename = f"codebase_analysis.{self.output_format}"
        if self.output_format == "markdown":
            output_filename = "codebase_analysis.md"
        elif self.output_format == "json":
            output_filename = "codebase_analysis.json"
        else:
            output_filename = "codebase_analysis.txt"
        
        # Write output to file
        self.profiler.add_event("file_writing_start")
        logger.info(f"Writing output to {output_filename}...")
        
        with open(output_filename, "w", encoding="utf-8") as output_file:
            output_file.write(output)
        
        self.profiler.add_event("file_writing_complete")
        
        # Stop profiling and log results
        perf_stats = self.profiler.stop()
        total_time = time.time() - start_time
        
        logger.info(f"Analysis complete! Output written to {output_filename}")
        logger.info(f"Files processed: {self.stats.get('total_files', 0)}")
        logger.info(f"Total size: {self.stats.get('total_size_formatted', 'unknown')}")
        logger.info(f"Time taken: {total_time:.2f} seconds")
        
        if perf_stats:
            logger.debug(f"Performance stats: {perf_stats}")
            
            # Log top functions if verbose
            top_funcs = self.profiler.get_profile_stats(top_n=5)
            if top_funcs:
                logger.debug("Top 5 functions by cumulative time:")
                for i, func in enumerate(top_funcs, 1):
                    logger.debug(f"{i}. {func['function']} - {func['cumtime']:.4f}s")
        
        return output_filename
    
    def run(self) -> str:
        """
        Run the analysis.
        
        Returns:
            Path to the output file
        """
        try:
            # Create event loop
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create a new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            # Run the async analysis
            return loop.run_until_complete(self.run_async())
        finally:
            # Clean up (don't close the loop if it was externally created)
            pass
