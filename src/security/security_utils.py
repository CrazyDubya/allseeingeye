#!/usr/bin/env python3
"""
Security utilities for AllSeeingEye
"""

import os
import re
import pathlib
import unicodedata
import binascii
import hashlib
import math
from typing import Optional, List, Set, Tuple, Dict, Any


class SecurityUtils:
    """Security utilities for file system operations"""
    
    @staticmethod
    def validate_path(path: str, base_dir: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate that a path is safe to access.
        
        Args:
            path: The path to validate
            base_dir: Optional base directory that the path must be contained within
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for None or empty path
        if not path:
            return False, "Path cannot be empty"
        
        # Normalize path
        try:
            normalized_path = os.path.normpath(os.path.abspath(path))
        except Exception as e:
            return False, f"Invalid path: {e}"
        
        # Check if path exists
        if not os.path.exists(normalized_path):
            return False, f"Path does not exist: {normalized_path}"
        
        # If base directory is specified, ensure path is within it
        if base_dir:
            base_dir = os.path.normpath(os.path.abspath(base_dir))
            if not normalized_path.startswith(base_dir):
                return False, f"Path {normalized_path} is outside the base directory {base_dir}"
        
        # Check for suspicious path components
        suspicious_patterns = [
            r'/proc/',
            r'/sys/',
            r'/dev/',
            r'/etc/passwd',
            r'/etc/shadow',
            r'/root/',
            r'/home/[^/]+/\.ssh/',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, normalized_path):
                return False, f"Path contains suspicious component matching pattern: {pattern}"
        
        return True, ""
    
    @staticmethod
    def sanitize_emojis(text: str) -> Tuple[str, int]:
        """
        Sanitize text by removing emojis and any associated hidden data.
        
        Args:
            text: The text to sanitize
            
        Returns:
            Tuple of (sanitized_text, emoji_count)
        """
        # Regular expression to match emoji patterns
        # This covers basic emojis, emoji sequences, ZWJ sequences, and variation selectors
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F700-\U0001F77F"  # alchemical symbols
            "\U0001F780-\U0001F7FF"  # geometric shapes
            "\U0001F800-\U0001F8FF"  # supplemental arrows
            "\U0001F900-\U0001F9FF"  # supplemental symbols & pictographs
            "\U0001FA00-\U0001FA6F"  # chess symbols
            "\U0001FA70-\U0001FAFF"  # symbols & pictographs extended-A
            "\U00002702-\U000027B0"  # dingbats
            "\U000024C2-\U0000257F"  # enclosed characters
            "\U00002580-\U000025FF"  # block elements
            "\U00002600-\U000026FF"  # miscellaneous symbols
            "\U00002700-\U000027BF"  # dingbats
            "\U0000FE00-\U0000FE0F"  # variation selectors
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "]+"
            "|"
            "\u200d|\u200c|\u200b|\ufe0f|\u20e3"  # zero-width joiners and variation selectors
            "|"
            "[\u0023-\u0039]\ufe0f?\u20e3"  # keycap sequences
            "|"
            "\u3299|\u3297|\u303d|\u3030|\u24c2|\ud83c[\udffb-\udfff]"  # additional symbols
        )
        
        # Count original emoji matches
        emoji_matches = re.findall(emoji_pattern, text)
        emoji_count = len(emoji_matches)
        
        # Replace emojis with a placeholder
        sanitized = re.sub(emoji_pattern, '[EMOJI]', text)
        
        return sanitized, emoji_count
    
    @staticmethod
    def _detect_obfuscation(content: str) -> bool:
        """
        Detect potentially obfuscated content using various heuristics.
        
        Args:
            content: The content to analyze
            
        Returns:
            True if content appears to be obfuscated, False otherwise
        """
        # Check for high entropy (potentially encrypted or compressed content)
        if len(content) > 100:
            try:
                # Calculate Shannon entropy
                char_counts = {}
                for char in content:
                    char_counts[char] = char_counts.get(char, 0) + 1
                
                entropy = 0
                for count in char_counts.values():
                    freq = count / len(content)
                    entropy -= freq * (math.log(freq, 2) if freq > 0 else 0)
                
                # Typical English text has entropy around 4.5-5.0
                # Higher values might indicate encryption or compression
                if entropy > 6.5:
                    return True
            except Exception:
                # If entropy calculation fails, continue with other checks
                pass
        
        # Check for very long lines (potential obfuscated code)
        lines = content.split('\n')
        for line in lines:
            if len(line.strip()) > 500:  # Arbitrarily long line
                return True
        
        # Check for suspicious character distributions
        alphanum_count = sum(1 for c in content if c.isalnum())
        if len(content) > 100 and alphanum_count / len(content) > 0.9:
            # Most normal text has punctuation, spaces, etc.
            # Very high ratio of alphanumeric chars might be obfuscated
            return True
        
        # Check for repetitive patterns
        if len(content) > 100:
            chunks = [content[i:i+3] for i in range(0, len(content)-3)]
            unique_chunks = set(chunks)
            uniqueness_ratio = len(unique_chunks) / len(chunks)
            
            # Very low uniqueness ratio suggests potential obfuscation
            if uniqueness_ratio < 0.1:
                return True
        
        return False
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Perform comprehensive text sanitization to remove potential security threats.
        
        Args:
            text: The text to sanitize
            
        Returns:
            Sanitized text
        """
        # Strip control characters
        text = ''.join(c for c in text if unicodedata.category(c)[0] != 'C' or c in ('\n', '\t', '\r'))
        
        # Sanitize emojis
        text, _ = SecurityUtils.sanitize_emojis(text)
        
        # Remove potentially dangerous Unicode homoglyphs
        homoglyph_map = {
            '\u0430': 'a',  # Cyrillic 'а'
            '\u0435': 'e',  # Cyrillic 'е'
            '\u043e': 'o',  # Cyrillic 'о'
            '\u0440': 'p',  # Cyrillic 'р'
            '\u0441': 'c',  # Cyrillic 'с'
            '\u0445': 'x',  # Cyrillic 'х'
            '\u0455': 's',  # Cyrillic 'ѕ'
            '\u04ae': 'Y',  # Cyrillic 'Ү'
            '\u2010': '-',  # Different types of hyphens/dashes
            '\u2011': '-',
            '\u2012': '-',
            '\u2013': '-',
            '\u2014': '-',
            '\u2015': '-',
            '\u2019': "'",  # Right single quotation mark
            '\u201c': '"',  # Left double quotation mark
            '\u201d': '"',  # Right double quotation mark
        }
        
        for char, replacement in homoglyph_map.items():
            text = text.replace(char, replacement)
        
        # Remove unusual Unicode characters while preserving common ones
        text = ''.join(c if ord(c) < 0x7F or c in '€£¥©®™°±²³¼½¾×÷áéíóúñ' else '_' for c in text)
        
        return text
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize a filename to remove potentially dangerous characters.
        
        Args:
            filename: The filename to sanitize
            
        Returns:
            Sanitized filename
        """
        # Replace potentially dangerous characters
        sanitized = re.sub(r'[^\w\.\-]', '_', filename)
        
        # Ensure the filename doesn't start with a dash (could be interpreted as a command option)
        if sanitized.startswith('-'):
            sanitized = '_' + sanitized[1:]
        
        # Ensure it's not a reserved name on Windows
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
            'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3', 
            'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        name_without_ext = os.path.splitext(sanitized)[0].upper()
        if name_without_ext in reserved_names:
            sanitized = '_' + sanitized
        
        return sanitized
    
    @staticmethod
    def is_safe_file_content(content: str) -> Tuple[bool, str]:
        """
        Check if file content appears to be safe.
        
        Args:
            content: The file content to check
            
        Returns:
            Tuple of (is_safe, reason)
        """
        # Check for very large content
        if len(content) > 10 * 1024 * 1024:  # 10MB
            return False, "File content is too large"
        
        # Check for potentially malicious patterns
        malicious_patterns = [
            # Shell commands that might be used in code injection
            r'`.*?`',
            r'system\s*\(',
            r'exec\s*\(',
            r'eval\s*\(',
            r'os\.system',
            r'subprocess\.call',
            r'subprocess\.Popen',
            # Additional dangerous patterns
            r'__import__\s*\(',
            r'globals\s*\(\)',
            r'locals\s*\(\)',
            r'getattr\s*\(',
            r'setattr\s*\(',
            r'\beval\b',
            r'\bexec\b',
            r'\bcompile\b',
            r'base64\.b64decode',
            r'pickle\.loads',
            r'marshal\.loads',
            r'codecs\.escape_decode',
            r'\bchr\(', 
            r'\bord\(',
            # Potential SQL injection
            r'DROP\s+TABLE',
            r'DELETE\s+FROM',
            r'UPDATE\s+.*?\s+SET',
            r'INSERT\s+INTO',
            # Potential file system access
            r'open\s*\(',
            r'file\s*\(',
            r'os\.unlink',
            r'os\.remove',
            r'shutil\.rmtree',
            # Potential hidden scripts
            r'<script[\s\S]*?>[\s\S]*?</script>',
            r'javascript:',
            r'data:text/html',
            r'\bonload=',
            r'\bonerror=',
            # Potential binary data masquerading as text
            r'\\x[0-9a-fA-F]{2}',
            r'\\u[0-9a-fA-F]{4}',
            r'\\U[0-9a-fA-F]{8}'
        ]
        
        # Check for high concentration of unusual Unicode characters
        unusual_char_count = sum(1 for c in content if ord(c) > 0x7F)
        if len(content) > 0 and unusual_char_count / len(content) > 0.3:
            return False, "Content contains high concentration of unusual Unicode characters"
        
        # Check for potentially obfuscated content
        if SecurityUtils._detect_obfuscation(content):
            return False, "Content appears to be obfuscated"
        
        # Search for malicious patterns
        for pattern in malicious_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # This is a simple check - in a real system, you'd want more context
                # and possibly a whitelist approach for trusted patterns
                return True, f"Found potentially unsafe pattern: {match.group(0)}"
        
        # Check for emojis with hidden data
        sanitized_content, emoji_count = SecurityUtils.sanitize_emojis(content)
        if emoji_count > 0:
            return True, f"Found and sanitized {emoji_count} emojis that might contain hidden data"
        
        return True, ""
    
    @staticmethod
    def ensure_directory_is_safe(directory: str) -> Tuple[bool, str]:
        """
        Ensure a directory is safe to read from/write to.
        
        Args:
            directory: The directory path to check
            
        Returns:
            Tuple of (is_safe, reason)
        """
        # Validate path
        is_valid, error = SecurityUtils.validate_path(directory)
        if not is_valid:
            return False, error
        
        # Ensure it's a directory
        if not os.path.isdir(directory):
            return False, f"Not a directory: {directory}"
        
        # Check permissions
        try:
            # Check if we can list the directory
            os.listdir(directory)
            
            # Check if we can create a temporary file
            test_file = os.path.join(directory, '.ase_security_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            return True, ""
        except PermissionError:
            return False, f"Insufficient permissions for directory: {directory}"
        except Exception as e:
            return False, f"Error checking directory safety: {e}"
            
    @staticmethod
    def check_file_integrity(file_path: str, expected_hash: Optional[str] = None) -> Tuple[bool, str]:
        """
        Check the integrity of a file by comparing its hash.
        
        Args:
            file_path: Path to the file
            expected_hash: Expected SHA-256 hash (if None, just compute and return the hash)
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Compute file hash
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            file_hash = sha256_hash.hexdigest()
            
            # If no expected hash provided, just return the computed hash
            if expected_hash is None:
                return True, f"File hash: {file_hash}"
            
            # Compare with expected hash
            if file_hash == expected_hash:
                return True, "File integrity verified"
            else:
                return False, f"File integrity check failed. Expected: {expected_hash}, Got: {file_hash}"
                
        except Exception as e:
            return False, f"Error checking file integrity: {e}"
