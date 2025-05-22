#!/usr/bin/env python3
"""
Output formatters for AllSeeingEye
"""

import os
import json
from typing import Dict, Any


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
        output = {
            "statistics": stats,
            "codebase_summary": codebase_summary,
            "directory_structure": directory_structure,
            "files_content": files_content
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
