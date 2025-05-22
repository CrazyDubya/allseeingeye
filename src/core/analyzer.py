#!/usr/bin/env python3
"""
Main analyzer for AllSeeingEye
"""

import os
import logging
import datetime
from typing import Dict, Any, Set, List, Optional

# Import core modules
from src.core.file_processor import FileProcessor
from src.core.tree_builder import TreeBuilder
from src.core.file_category import FileCategory

# Import formatters
from src.formatters.output_format import OutputFormat

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Analyzer")


class Analyzer:
    """Main analyzer class for AllSeeingEye"""
    
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
                 verbose: bool = False):
        """
        Initialize the analyzer.
        
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
        
        # Initialize statistics
        self.stats = {
            "start_time": datetime.datetime.now()
        }
        
        # Initialize components
        self.file_processor = FileProcessor(
            max_file_size=self.max_file_size,
            active_categories=self.active_categories,
            security_checks=self.security_checks
        )
        
        self.tree_builder = TreeBuilder(
            base_directory=self.directory,
            file_processor=self.file_processor,
            excluded_dirs=self.excluded_dirs,
            excluded_files=self.excluded_files,
            max_files=self.max_files
        )
    
    def run(self) -> str:
        """
        Run the analysis.
        
        Returns:
            Path to the output file
        """
        logger.info(f"Analyzing directory: {self.directory}")
        logger.info(f"Output format: {self.output_format}")
        
        # Dictionary to store processed files by category
        files_content = {}
        
        # Build tree and collect file information
        logger.info("Building directory tree...")
        directory_structure = self.tree_builder.build_tree(files_content)
        
        # Get tree builder statistics
        tree_stats = self.tree_builder.get_stats()
        self.stats.update(tree_stats)
        
        # Create codebase summary
        logger.info("Creating codebase summary...")
        codebase_summary = self.tree_builder.create_codebase_summary()
        
        # Update statistics
        self.stats["end_time"] = datetime.datetime.now()
        self.stats["duration"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
        
        # Generate output based on format
        logger.info(f"Generating {self.output_format} output...")
        if self.output_format == "markdown":
            output = OutputFormat.format_markdown(directory_structure, files_content,
                                                  self.stats, codebase_summary)
        elif self.output_format == "json":
            output = OutputFormat.format_json(directory_structure, files_content,
                                              self.stats, codebase_summary)
        else:  # Default to text
            output = OutputFormat.format_text(directory_structure, files_content,
                                              self.stats, codebase_summary)
        
        # Determine output filename based on format
        output_filename = f"codebase_analysis.{self.output_format}"
        if self.output_format == "markdown":
            output_filename = "codebase_analysis.md"
        elif self.output_format == "json":
            output_filename = "codebase_analysis.json"
        else:
            output_filename = "codebase_analysis.txt"
        
        # Write output to file
        with open(output_filename, "w", encoding="utf-8") as output_file:
            output_file.write(output)
        
        logger.info(f"Analysis complete! Output written to {output_filename}")
        logger.info(f"Files processed: {self.stats['total_files']}")
        logger.info(f"Total size: {self.stats.get('total_size_formatted', 'unknown')}")
        logger.info(f"Time taken: {self.stats['duration']:.2f} seconds")
        
        return output_filename
