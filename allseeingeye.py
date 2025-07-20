#!/usr/bin/env python3
"""
AllSeeingEye - Directory analyzer optimized for LLM understanding
"""

import os
import re
import json
import subprocess
import argparse
import logging
import platform
import datetime
import mimetypes
import hashlib
from typing import List, Dict, Tuple, Optional, Set, Any, Union
from pathlib import Path

# Import LLM components
from src.llm.integration import get_llm_integration
from src.llm.prompt_formatter import PromptFormatter
from src.formatters.exporters.interactive_html_exporter import InteractiveHTMLExporter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AllSeeingEye")


class FileCategory:
    """File category definitions with associated extensions and processing rules"""

    # Category definitions with extensions and descriptions
    CATEGORIES = {
        "code": {
            "extensions": [
                # Programming languages
                ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".cs",
                ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".groovy",
                # Web development
                ".html", ".css", ".scss", ".less", ".vue", ".svelte",
                # Data processing
                ".sql", ".r", ".jl",
                # Shell scripts
                ".sh", ".bash", ".zsh", ".ps1", ".bat", ".cmd",
            ],
            "description": "Source code files"
        },
        "data": {
            "extensions": [
                # Structured data
                ".json", ".csv", ".tsv", ".xml", ".yaml", ".yml", ".toml",
                # Plain text data
                ".txt", ".log",
            ],
            "description": "Data files"
        },
        "documentation": {
            "extensions": [
                ".md", ".rst", ".adoc", ".org", ".wiki", ".tex",
                ".docx", ".pdf", ".epub",
            ],
            "description": "Documentation files"
        },
        "configuration": {
            "extensions": [
                ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
                ".env", ".properties", ".xml", ".gradle", ".sbt",
                ".gitignore", ".dockerignore", "Dockerfile", "Makefile",
            ],
            "description": "Configuration files"
        },
        "media": {
            "extensions": [
                # Images
                ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
                # Audio
                ".mp3", ".wav", ".ogg", ".flac",
                # Video
                ".mp4", ".webm", ".avi", ".mov",
            ],
            "description": "Media files (not included in content)"
        },
        "archive": {
            "extensions": [
                ".zip", ".tar", ".gz", ".tgz", ".7z", ".rar", ".bz2", ".xz",
            ],
            "description": "Archive files (not included in content)"
        },
        "binary": {
            "extensions": [
                ".exe", ".dll", ".so", ".dylib", ".bin", ".dat", ".pyc", ".class",
            ],
            "description": "Binary files (not included in content)"
        },
    }

    @classmethod
    def get_extensions_by_category(cls, category: str) -> List[str]:
        """Get all extensions for a given category"""
        if category in cls.CATEGORIES:
            return cls.CATEGORIES[category]["extensions"]
        return []

    @classmethod
    def get_category_for_extension(cls, extension: str) -> str:
        """Determine category for a given file extension"""
        for category, info in cls.CATEGORIES.items():
            if extension.lower() in info["extensions"]:
                return category
        return "other"

    @classmethod
    def is_binary_mimetype(cls, mime_type: str) -> bool:
        """Check if a mime type represents binary content"""
        if mime_type is None:
            return False
        return not (mime_type.startswith("text/") or
                    mime_type in ["application/json", "application/xml",
                                  "application/javascript", "application/x-yaml"])

    @classmethod
    def is_text_category(cls, category: str) -> bool:
        """Check if files in this category should be treated as text"""
        return category in ["code", "data", "documentation", "configuration"]


class OutputFormat:
    """Output formatters for different file types"""

    @staticmethod
    def format_markdown(directory_structure: str, files_content: Dict[str, Dict],
                        stats: Dict[str, Any], codebase_summary: str) -> str:
        """Format output as Markdown"""
        sections = []

        # Add title and summary
        sections.append("# Codebase Analysis\n")

        # Add statistics section
        sections.append("## Statistics\n")
        sections.append("```")
        sections.append(f"Files analyzed: {stats['total_files']}")
        sections.append(f"Directories: {stats['total_dirs']}")
        sections.append(f"Lines of code: {stats['total_lines']}")
        sections.append(f"Total size: {stats['total_size_formatted']}")
        sections.append("")
        sections.append("File types:")
        for category, count in stats['files_by_category'].items():
            sections.append(f"  - {category}: {count} files")
        sections.append("```\n")

        # Add codebase summary
        if codebase_summary:
            sections.append("## Codebase Summary\n")
            sections.append(codebase_summary + "\n")

        # Add directory structure
        sections.append("## Directory Structure\n")
        sections.append("```")
        sections.append(directory_structure)
        sections.append("```\n")

        # Add file contents by category
        for category in ["code", "documentation", "configuration", "data"]:
            if category in files_content and files_content[category]:
                sections.append(f"## {category.capitalize()} Files\n")

                for file_path, file_info in files_content[category].items():
                    sections.append(f"### {os.path.basename(file_path)}\n")
                    sections.append(f"**Path:** {file_path}  ")
                    sections.append(f"**Size:** {file_info.get('size_formatted', 'N/A')}  ")
                    sections.append(f"**Last modified:** {file_info.get('last_modified', 'N/A')}  \n")

                    if 'content' in file_info:
                        sections.append("```" + OutputFormat._get_language_for_file(file_path))
                        sections.append(file_info['content'])
                        sections.append("```\n")

        return "\n".join(sections)

    @staticmethod
    def format_json(directory_structure: str, files_content: Dict[str, Dict],
                    stats: Dict[str, Any], codebase_summary: str) -> str:
        """Format output as JSON"""
        # Create a serializable version of files_content
        serializable_files_content = {}
        for category, files in files_content.items():
            serializable_files_content[category] = {}
            for file_path, file_info in files.items():
                # Create a copy of file_info to avoid modifying the original
                info_copy = file_info.copy()
                # Add summary if it exists
                if "summary" in info_copy:
                    info_copy["summary"] = info_copy["summary"]
                serializable_files_content[category][file_path] = info_copy

        output = {
            "statistics": stats,
            "codebase_summary": codebase_summary,
            "directory_structure": directory_structure,
            "files_content": serializable_files_content
        }
        return json.dumps(output, indent=2)

    @staticmethod
    def format_text(directory_structure: str, files_content: Dict[str, Dict],
                    stats: Dict[str, Any], codebase_summary: str) -> str:
        """Format output as plain text"""
        sections = []

        # Add title and summary
        sections.append("CODEBASE ANALYSIS")
        sections.append("=" * 80)
        sections.append("")

        # Add statistics section
        sections.append("STATISTICS")
        sections.append("-" * 80)
        sections.append(f"Files analyzed: {stats['total_files']}")
        sections.append(f"Directories: {stats['total_dirs']}")
        sections.append(f"Lines of code: {stats['total_lines']}")
        sections.append(f"Total size: {stats['total_size_formatted']}")
        sections.append("")
        sections.append("File types:")
        for category, count in stats['files_by_category'].items():
            sections.append(f"  - {category}: {count} files")
        sections.append("")

        # Add codebase summary
        if codebase_summary:
            sections.append("CODEBASE SUMMARY")
            sections.append("-" * 80)
            sections.append(codebase_summary)
            sections.append("")

        # Add directory structure
        sections.append("DIRECTORY STRUCTURE")
        sections.append("-" * 80)
        sections.append(directory_structure)
        sections.append("")

        # Add file contents by category
        for category in ["code", "documentation", "configuration", "data"]:
            if category in files_content and files_content[category]:
                sections.append(f"{category.upper()} FILES")
                sections.append("-" * 80)

                for file_path, file_info in files_content[category].items():
                    sections.append(f"File: {file_path}")
                    sections.append(f"Size: {file_info.get('size_formatted', 'N/A')}")
                    sections.append(f"Last modified: {file_info.get('last_modified', 'N/A')}")
                    sections.append("-" * 40)

                    if 'content' in file_info:
                        sections.append(file_info['content'])

                    sections.append("")

        return "\n".join(sections)

    @staticmethod
    def _get_language_for_file(file_path: str) -> str:
        """Get language identifier for syntax highlighting in markdown code blocks"""
        ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "jsx",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".md": "markdown",
            ".sh": "bash",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".cs": "csharp",
            ".go": "go",
            ".rb": "ruby",
            ".rs": "rust",
            ".php": "php",
            ".sql": "sql",
            ".xml": "xml",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".toml": "toml",
        }
        return language_map.get(ext, "")


class AllSeeingEye:
    """Directory analysis tool optimized for LLM understanding."""

    def __init__(self,
                 directory: Optional[str] = None,
                 excluded_dirs: Optional[List[str]] = None,
                 excluded_files: Optional[List[str]] = None,
                 included_categories: Optional[List[str]] = None,
                 excluded_categories: Optional[List[str]] = None,
                 max_file_size: int = 1024 * 1024,  # 1MB default
                 max_files: int = 1000,
                 output_format: str = "markdown",
                 verbose: bool = False):
        """Initialize with configurable options."""
        self.directory = os.path.abspath(directory or os.getcwd())
        self.excluded_dirs = set(excluded_dirs or ['.git', 'node_modules', '.venv', '__pycache__', '.idea', '.vscode'])
        self.excluded_files = set(excluded_files or [])

        # Process included and excluded categories
        self.all_categories = set(FileCategory.CATEGORIES.keys())
        self.included_categories = set(included_categories or self.all_categories)
        self.excluded_categories = set(excluded_categories or [])
        self.active_categories = self.included_categories - self.excluded_categories

        # Size limits
        self.max_file_size = max_file_size
        self.max_files = max_files

        # Output format
        self.output_format = output_format

        # Configure logging
        if verbose:
            logger.setLevel(logging.DEBUG)

        # Statistics
        self.stats = {
            "total_files": 0,
            "total_dirs": 0,
            "total_size": 0,
            "total_lines": 0,
            "files_by_category": {},
            "start_time": datetime.datetime.now(),
        }

        # Initialize file type detection
        mimetypes.init()

    def get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get file metadata including size, modification time, and mime type."""
        file_stat = os.stat(file_path)
        size = file_stat.st_size
        modified_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)

        # Determine mime type
        mime_type, _ = mimetypes.guess_type(file_path)

        return {
            "size": size,
            "size_formatted": self._format_size(size),
            "last_modified": modified_time.strftime("%Y-%m-%d %H:%M:%S"),
            "mime_type": mime_type
        }

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024

    def should_process_file(self, file_path: str, metadata: Dict[str, Any]) -> bool:
        """Determine if a file should be processed based on rules."""
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
        """Determine the category for a file based on its extension."""
        _, ext = os.path.splitext(file_path)
        return FileCategory.get_category_for_extension(ext)

    def list_directory(self, directory: str) -> List[str]:
        """List directory contents in a cross-platform way."""
        try:
            return os.listdir(directory)
        except Exception as e:
            logger.error(f"Error listing directory {directory}: {e}")
            return []

    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process a single file and return its content and metadata."""
        result = {}

        try:
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
                        result['content'] = content
                        result['line_count'] = content.count('\n') + 1
                        self.stats["total_lines"] += result['line_count']
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {e}")
                    result['error'] = str(e)

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            result['error'] = str(e)

        return result

    def build_tree(self, output_dictionary: Dict = None) -> str:
        """Build a directory tree and collect file information."""
        if output_dictionary is None:
            output_dictionary = {}

        # Use custom implementation for building tree
        tree_output = []

        def _build_tree_recursive(dir_path: str, prefix: str = ''):
            entries = sorted(os.listdir(dir_path))
            dirs = [e for e in entries if os.path.isdir(os.path.join(dir_path, e))]
            files = [e for e in entries if os.path.isfile(os.path.join(dir_path, e))]

            # Process all files first
            for i, entry in enumerate(files):
                is_last = (i == len(files) - 1 and len(dirs) == 0)
                conn = '└── ' if is_last else '├── '

                file_path = os.path.join(dir_path, entry)
                rel_path = os.path.relpath(file_path, self.directory)

                # Skip excluded files
                if rel_path in self.excluded_files:
                    tree_output.append(f"{prefix}{conn}{entry} # Excluded")
                    continue

                # Process file
                self.stats["total_files"] += 1

                # Get file category
                category = self.get_file_category(file_path)
                self.stats["files_by_category"][category] = self.stats["files_by_category"].get(category, 0) + 1

                # Add to tree
                tree_output.append(f"{prefix}{conn}{entry}")

                # Check if we've hit the file limit
                if self.stats["total_files"] >= self.max_files:
                    tree_output.append(f"{prefix}    --- File limit reached ({self.max_files} files) ---")
                    return False

                # Process file content if needed
                file_info = self.process_file(file_path)

                # Update statistics
                self.stats["total_size"] += file_info.get("size", 0)

                # Add to output dictionary
                if category in self.active_categories:
                    if category not in output_dictionary:
                        output_dictionary[category] = {}
                    output_dictionary[category][rel_path] = file_info

            # Then process directories
            for i, entry in enumerate(dirs):
                is_last = (i == len(dirs) - 1)
                conn = '└── ' if is_last else '├── '
                new_prefix = prefix + ('    ' if is_last else '│   ')

                dir_path_full = os.path.join(dir_path, entry)
                rel_dir_path = os.path.relpath(dir_path_full, self.directory)

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
        _build_tree_recursive(self.directory)

        # Format statistics
        self.stats["total_size_formatted"] = self._format_size(self.stats["total_size"])
        self.stats["end_time"] = datetime.datetime.now()
        self.stats["duration"] = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        return '\n'.join(tree_output)

    def create_codebase_summary(self, files_content):
        """Create a summary of the codebase"""
        summary = []

        # Basic summary information
        summary.append("This codebase contains:")

        # Count files by type
        for category, count in self.stats['files_by_category'].items():
            if count > 0:
                description = FileCategory.CATEGORIES.get(category, {}).get("description", "files")
                summary.append(f"- {count} {description}")

        # Top-level directories
        top_dirs = [d for d in os.listdir(self.directory)
                    if os.path.isdir(os.path.join(self.directory, d))
                    and d not in self.excluded_dirs]

        if top_dirs:
            summary.append("\nMain directories:")
            for directory in sorted(top_dirs):
                dir_path = os.path.join(self.directory, directory)
                file_count = sum(len(files) for _, _, files in os.walk(dir_path))
                summary.append(f"- {directory}/: {file_count} files")

        return "\n".join(summary)

    def summarize_files(self, llm_provider="ollama", llm_model="gemma:7b"):
        """Summarize each file in the codebase using an LLM."""
        logger.info("Summarizing files...")
        llm = get_llm_integration(provider=llm_provider, config={"model": llm_model})
        if not llm.is_available():
            logger.warning(f"LLM provider '{llm_provider}' is not available. Skipping summarization.")
            return

        for category in self.files_content:
            for file_path, file_info in self.files_content[category].items():
                if "content" in file_info:
                    prompt = PromptFormatter.format_summarization_prompt(
                        code=file_info["content"],
                        filename=file_path
                    )
                    summary = llm.provider.generate(prompt)
                    file_info["summary"] = summary.get("text", "")

    def analyze(self, summarize=False, llm_provider="ollama", llm_model="gemma:7b"):
        """Analyze the codebase and return results.
        
        This method is used by the web interface and API to get analysis results.
        """
        logger.info(f"Analyzing directory: {self.directory}")
        
        # Dictionary to store processed files by category
        self.files_content = {}
        
        # Build tree and collect file information
        self.directory_structure = self.build_tree(self.files_content)
        
        # Create codebase summary
        self.codebase_summary = self.create_codebase_summary(self.files_content)
        
        # Summarize files if requested
        if summarize:
            self.summarize_files(llm_provider=llm_provider, llm_model=llm_model)

        # Store results for later use
        self.results = {
            'directory_structure': self.directory_structure,
            'files_content': self.files_content,
            'stats': self.stats,
            'codebase_summary': self.codebase_summary
        }
        
        logger.info(f"Analysis complete!")
        logger.info(f"Files processed: {self.stats['total_files']}")
        logger.info(f"Total size: {self.stats['total_size_formatted']}")
        logger.info(f"Time taken: {self.stats['duration']:.2f} seconds")
        
        return self.results
    
    def format_output(self, output_format):
        """Format the analysis results using the specified output format.
        
        Args:
            output_format: The output format to use as a string ("markdown", "json", "text", "html", "interactive_html")
            
        Returns:
            str: The formatted output
        """
        if not hasattr(self, 'results'):
            raise ValueError("Must run analyze() before formatting output")
            
        if output_format == "markdown":
            return OutputFormat.format_markdown(
                self.directory_structure, 
                self.files_content,
                self.stats, 
                self.codebase_summary
            )
        elif output_format == "json":
            return OutputFormat.format_json(
                self.directory_structure, 
                self.files_content,
                self.stats, 
                self.codebase_summary
            )
        elif output_format == "html":
            # For HTML format, use markdown format and let the Flask template handle it
            return OutputFormat.format_markdown(
                self.directory_structure, 
                self.files_content,
                self.stats, 
                self.codebase_summary
            )
        elif output_format == "interactive_html":
            exporter = InteractiveHTMLExporter()
            output_file = "interactive_report.html"
            exporter.export(self.results, output_file)
            return f"Interactive HTML report saved to {output_file}"
        else:  # Default to text
            return OutputFormat.format_text(
                self.directory_structure, 
                self.files_content,
                self.stats, 
                self.codebase_summary
            )
    
    def run(self, summarize=False):
        """Run the AllSeeingEye tool and generate output."""
        logger.info(f"Analyzing directory: {self.directory}")
        logger.info(f"Output format: {self.output_format}")

        # Analyze the codebase
        self.analyze(summarize=summarize)
        
        # Generate output based on format
        output = self.format_output(self.output_format)

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
        logger.info(f"Total size: {self.stats['total_size_formatted']}")
        logger.info(f"Time taken: {self.stats['duration']:.2f} seconds")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="AllSeeingEye - Codebase analysis tool optimized for LLMs")

    parser.add_argument("--directory", "-d", help="Directory to scan (default: current directory)")
    parser.add_argument("--exclude-dirs", "-ed", nargs="+", help="Directories to exclude")
    parser.add_argument("--exclude-files", "-ef", nargs="+", help="Files to exclude")
    parser.add_argument("--include-categories", "-ic", nargs="+",
                        choices=FileCategory.CATEGORIES.keys(),
                        help="File categories to include (default: all)")
    parser.add_argument("--exclude-categories", "-ec", nargs="+",
                        choices=FileCategory.CATEGORIES.keys(),
                        help="File categories to exclude")
    parser.add_argument("--max-file-size", "-ms", type=int, default=1024 * 1024,
                        help="Maximum file size in bytes to process (default: 1MB)")
    parser.add_argument("--max-files", "-mf", type=int, default=1000,
                        help="Maximum number of files to process (default: 1000)")
    parser.add_argument("--format", "-f", choices=["markdown", "json", "text", "interactive_html"],
                        default="markdown", help="Output format (default: markdown)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--summarize", "-s", action="store_true", help="Enable summarization of files using an LLM")

    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_arguments()

    # Initialize and run AllSeeingEye
    eye = AllSeeingEye(
        directory=args.directory,
        excluded_dirs=args.exclude_dirs,
        excluded_files=args.exclude_files,
        included_categories=args.include_categories,
        excluded_categories=args.exclude_categories,
        max_file_size=args.max_file_size,
        max_files=args.max_files,
        output_format=args.format,
        verbose=args.verbose
    )

    eye.run(summarize=args.summarize)


if __name__ == "__main__":
    main()