#!/usr/bin/env python3
"""
File categorization functionality for AllSeeingEye
"""

from typing import List, Dict, Any


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

    @classmethod
    def get_description(cls, category: str) -> str:
        """Get the description for a category"""
        if category in cls.CATEGORIES:
            return cls.CATEGORIES[category]["description"]
        return "Other files"
