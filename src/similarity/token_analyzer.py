#!/usr/bin/env python3
"""
Token analyzer for code similarity detection.

This module provides functionality to tokenize code files in various
programming languages for similarity analysis.
"""

import re
import os
import logging
import tokenize
import io
from typing import List, Dict, Tuple, Set, Optional, Any, Union, Callable
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class TokenType(Enum):
    """Token type enumeration."""
    KEYWORD = 1
    IDENTIFIER = 2
    LITERAL = 3
    OPERATOR = 4
    PUNCTUATION = 5
    COMMENT = 6
    OTHER = 7


class Token:
    """Represents a code token with type information."""
    
    def __init__(self, value: str, token_type: TokenType, line: int, position: int):
        """Initialize token with value and metadata."""
        self.value = value
        self.normalized_value = self._normalize_value(value, token_type)
        self.token_type = token_type
        self.line = line
        self.position = position
    
    def _normalize_value(self, value: str, token_type: TokenType) -> str:
        """
        Normalize token value based on its type.
        
        For similarity detection, identifiers, literal values, etc., are
        normalized to reduce false negatives in clone detection.
        """
        if token_type == TokenType.IDENTIFIER:
            return 'ID'
        elif token_type == TokenType.LITERAL:
            # Normalize different types of literals
            if value.startswith(("'", '"')):
                return 'STR'
            elif value.isdigit() or (value and value[0] == '-' and value[1:].isdigit()):
                return 'NUM'
            elif value in ('True', 'False', 'true', 'false'):
                return 'BOOL'
            elif value in ('null', 'None', 'nil'):
                return 'NULL'
            return 'LIT'
        elif token_type == TokenType.COMMENT:
            return 'COMMENT'
        
        # For keywords, operators, and punctuation, keep the original value
        return value
    
    def __eq__(self, other):
        """Compare tokens for equality based on normalized value and type."""
        if not isinstance(other, Token):
            return False
        return (self.normalized_value == other.normalized_value and 
                self.token_type == other.token_type)
    
    def __hash__(self):
        """Hash based on normalized value and type."""
        return hash((self.normalized_value, self.token_type))
    
    def __str__(self):
        """String representation of token."""
        return f"Token({self.value}, {self.token_type}, line={self.line}, pos={self.position})"
    
    def __repr__(self):
        """Detailed representation of token."""
        return str(self)


class TokenAnalyzer:
    """
    Analyzes and tokenizes code files in various programming languages.
    
    This class provides methods to tokenize code files, generate token
    sequences, and calculate token-based metrics for similarity detection.
    """
    
    # Language-specific tokenizer functions
    _TOKENIZERS = {}
    
    # Keywords for different languages
    _KEYWORDS = {
        'python': {
            'and', 'as', 'assert', 'async', 'await', 'break', 'class', 'continue',
            'def', 'del', 'elif', 'else', 'except', 'False', 'finally', 'for',
            'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None',
            'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 'True', 'try',
            'while', 'with', 'yield'
        },
        'javascript': {
            'await', 'break', 'case', 'catch', 'class', 'const', 'continue',
            'debugger', 'default', 'delete', 'do', 'else', 'enum', 'export',
            'extends', 'false', 'finally', 'for', 'function', 'if', 'implements',
            'import', 'in', 'instanceof', 'interface', 'let', 'new', 'null',
            'package', 'private', 'protected', 'public', 'return', 'static',
            'super', 'switch', 'this', 'throw', 'true', 'try', 'typeof', 'var',
            'void', 'while', 'with', 'yield'
        },
        'typescript': {
            'abstract', 'any', 'as', 'asserts', 'async', 'await', 'boolean', 'break',
            'case', 'catch', 'class', 'const', 'constructor', 'continue', 'debugger',
            'declare', 'default', 'delete', 'do', 'else', 'enum', 'export', 'extends',
            'false', 'finally', 'for', 'from', 'function', 'get', 'if', 'implements',
            'import', 'in', 'infer', 'instanceof', 'interface', 'is', 'keyof', 'let',
            'module', 'namespace', 'never', 'new', 'null', 'number', 'object', 'of',
            'package', 'private', 'protected', 'public', 'readonly', 'require', 'return',
            'set', 'static', 'string', 'super', 'switch', 'symbol', 'this', 'throw',
            'true', 'try', 'type', 'typeof', 'undefined', 'unique', 'unknown', 'var',
            'void', 'while', 'with', 'yield'
        },
        'java': {
            'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char',
            'class', 'const', 'continue', 'default', 'do', 'double', 'else', 'enum',
            'extends', 'final', 'finally', 'float', 'for', 'goto', 'if', 'implements',
            'import', 'instanceof', 'int', 'interface', 'long', 'native', 'new',
            'package', 'private', 'protected', 'public', 'return', 'short', 'static',
            'strictfp', 'super', 'switch', 'synchronized', 'this', 'throw', 'throws',
            'transient', 'try', 'void', 'volatile', 'while', 'true', 'false', 'null'
        },
        'cpp': {
            'alignas', 'alignof', 'and', 'and_eq', 'asm', 'atomic_cancel',
            'atomic_commit', 'atomic_noexcept', 'auto', 'bitand', 'bitor', 'bool',
            'break', 'case', 'catch', 'char', 'char16_t', 'char32_t', 'class',
            'compl', 'concept', 'const', 'constexpr', 'const_cast', 'continue',
            'co_await', 'co_return', 'co_yield', 'decltype', 'default', 'delete',
            'do', 'double', 'dynamic_cast', 'else', 'enum', 'explicit', 'export',
            'extern', 'false', 'float', 'for', 'friend', 'goto', 'if', 'import',
            'inline', 'int', 'long', 'module', 'mutable', 'namespace', 'new',
            'noexcept', 'not', 'not_eq', 'nullptr', 'operator', 'or', 'or_eq',
            'private', 'protected', 'public', 'register', 'reinterpret_cast',
            'requires', 'return', 'short', 'signed', 'sizeof', 'static',
            'static_assert', 'static_cast', 'struct', 'switch', 'synchronized',
            'template', 'this', 'thread_local', 'throw', 'true', 'try', 'typedef',
            'typeid', 'typename', 'union', 'unsigned', 'using', 'virtual', 'void',
            'volatile', 'wchar_t', 'while', 'xor', 'xor_eq'
        },
    }
    
    # Operators for different languages
    _OPERATORS = {
        'python': {
            '+', '-', '*', '/', '//', '%', '**', '=', '+=', '-=', '*=', '/=',
            '//=', '%=', '**=', '&=', '|=', '^=', '>>=', '<<=', '==', '!=',
            '>', '<', '>=', '<=', 'and', 'or', 'not', 'is', 'is not', 'in',
            'not in', '&', '|', '^', '~', '<<', '>>'
        },
        'javascript': {
            '+', '-', '*', '/', '%', '**', '=', '+=', '-=', '*=', '/=', '%=',
            '**=', '&=', '|=', '^=', '>>=', '<<=', '>>>=', '==', '===', '!=',
            '!==', '>', '<', '>=', '<=', '&&', '||', '!', '&', '|', '^', '~',
            '<<', '>>', '>>>', '++', '--', '?', ':', '??', '?.'
        },
        'java': {
            '+', '-', '*', '/', '%', '=', '+=', '-=', '*=', '/=', '%=', '&=',
            '|=', '^=', '>>=', '<<=', '>>>=', '==', '!=', '>', '<', '>=', '<=',
            '&&', '||', '!', '&', '|', '^', '~', '<<', '>>', '>>>', '++', '--',
            '?', ':', 'instanceof'
        },
        'cpp': {
            '+', '-', '*', '/', '%', '=', '+=', '-=', '*=', '/=', '%=', '&=',
            '|=', '^=', '>>=', '<<=', '==', '!=', '>', '<', '>=', '<=', '&&',
            '||', '!', '&', '|', '^', '~', '<<', '>>', '++', '--', '?', ':',
            '::', '->', '.', '.*', '->*', ',', 'and', 'or', 'not', 'xor',
            'bitand', 'bitor', 'compl'
        },
    }
    
    def __init__(self):
        """Initialize the token analyzer."""
        # Register language-specific tokenizers
        self._TOKENIZERS = {
            '.py': self._tokenize_python,
            '.js': self._tokenize_javascript,
            '.jsx': self._tokenize_javascript,
            '.ts': self._tokenize_typescript,
            '.tsx': self._tokenize_typescript,
            '.java': self._tokenize_java,
            '.c': self._tokenize_cpp,
            '.cpp': self._tokenize_cpp,
            '.h': self._tokenize_cpp,
            '.hpp': self._tokenize_cpp,
        }
    
    def tokenize_file(self, file_path: str) -> List[Token]:
        """
        Tokenize a file based on its extension.
        
        Args:
            file_path: Path to the file to tokenize
            
        Returns:
            List[Token]: List of extracted tokens
        """
        try:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # Check if we have a specific tokenizer for this extension
            tokenizer = self._TOKENIZERS.get(ext)
            
            if tokenizer:
                # Read file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Apply language-specific tokenizer
                return tokenizer(content)
            else:
                # Use generic tokenizer for unsupported languages
                return self._tokenize_generic(file_path)
        
        except Exception as e:
            logger.error(f"Error tokenizing file {file_path}: {e}")
            return []
    
    def tokenize_content(self, content: str, language: str) -> List[Token]:
        """
        Tokenize content with a specified language.
        
        Args:
            content: Code content to tokenize
            language: Programming language of the content
            
        Returns:
            List[Token]: List of extracted tokens
        """
        try:
            # Map language name to extension
            language_to_ext = {
                'python': '.py',
                'javascript': '.js',
                'typescript': '.ts',
                'java': '.java',
                'cpp': '.cpp',
                'c': '.c'
            }
            
            ext = language_to_ext.get(language.lower(), '.txt')
            tokenizer = self._TOKENIZERS.get(ext)
            
            if tokenizer:
                return tokenizer(content)
            else:
                # Create temporary file for generic tokenizer
                with tempfile.NamedTemporaryFile(suffix=ext, mode='w', encoding='utf-8') as temp_file:
                    temp_file.write(content)
                    temp_file.flush()
                    return self._tokenize_generic(temp_file.name)
        
        except Exception as e:
            logger.error(f"Error tokenizing content: {e}")
            return []
    
    def _tokenize_python(self, content: str) -> List[Token]:
        """
        Tokenize Python code using the built-in tokenize module.
        
        Args:
            content: Python code content
            
        Returns:
            List[Token]: List of extracted tokens
        """
        tokens = []
        
        try:
            # Convert content to bytes for the tokenize module
            content_bytes = io.BytesIO(content.encode('utf-8'))
            
            # Tokenize the content
            for tok in tokenize.tokenize(content_bytes.readline):
                token_type = TokenType.OTHER
                
                # Map token types
                if tok.type == tokenize.NAME:
                    if tok.string in self._KEYWORDS['python']:
                        token_type = TokenType.KEYWORD
                    else:
                        token_type = TokenType.IDENTIFIER
                elif tok.type == tokenize.STRING or tok.type == tokenize.NUMBER:
                    token_type = TokenType.LITERAL
                elif tok.type == tokenize.OP:
                    token_type = TokenType.OPERATOR if tok.string in self._OPERATORS['python'] else TokenType.PUNCTUATION
                elif tok.type == tokenize.COMMENT:
                    token_type = TokenType.COMMENT
                
                # Skip newlines, indentation, etc.
                if tok.type not in (tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER, tokenize.NL):
                    tokens.append(Token(tok.string, token_type, tok.start[0], tok.start[1]))
        
        except Exception as e:
            logger.debug(f"Error in Python tokenization: {e}")
        
        return tokens
    
    def _tokenize_javascript(self, content: str) -> List[Token]:
        """
        Tokenize JavaScript code using regular expressions.
        
        Args:
            content: JavaScript code content
            
        Returns:
            List[Token]: List of extracted tokens
        """
        # Define token patterns
        patterns = [
            # Comments
            (r'//.*?$', TokenType.COMMENT),                 # Single-line comment
            (r'/\*.*?\*/', TokenType.COMMENT),              # Multi-line comment
            # Strings
            (r'"(?:\\.|[^"\\])*"', TokenType.LITERAL),      # Double-quoted string
            (r"'(?:\\.|[^'\\])*'", TokenType.LITERAL),      # Single-quoted string
            (r"`(?:\\.|[^`\\])*`", TokenType.LITERAL),      # Template string
            # Numbers
            (r'\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b', TokenType.LITERAL),  # Numbers
            # Keywords and identifiers
            (r'\b([A-Za-z_$][\w$]*)\b', None),              # Identifiers and keywords (type determined later)
            # Operators and punctuation
            (r'[\+\-\*/%=&\|\^~<>!?:]+', None),             # Operators (type determined later)
            (r'[;,.()\[\]{}]', TokenType.PUNCTUATION),      # Punctuation
        ]
        
        tokens = []
        line_number = 1
        
        # Process content line by line to track line numbers
        for line in content.split('\n'):
            position = 0
            remaining = line
            
            while remaining:
                match = None
                match_type = None
                
                # Try each pattern
                for pattern, token_type in patterns:
                    regex_match = re.match(pattern, remaining, re.DOTALL)
                    if regex_match:
                        match = regex_match.group(0)
                        match_type = token_type
                        break
                
                if match:
                    # Determine token type for identifiers and keywords
                    if match_type is None:
                        if re.match(r'\b([A-Za-z_$][\w$]*)\b', match):
                            match_type = TokenType.KEYWORD if match in self._KEYWORDS['javascript'] else TokenType.IDENTIFIER
                        elif re.match(r'[\+\-\*/%=&\|\^~<>!?:]+', match):
                            match_type = TokenType.OPERATOR if match in self._OPERATORS['javascript'] else TokenType.PUNCTUATION
                    
                    # Add token if not whitespace
                    if not match.isspace():
                        tokens.append(Token(match, match_type, line_number, position))
                    
                    # Update position and remaining text
                    position += len(match)
                    remaining = remaining[len(match):]
                else:
                    # Skip character if no match (typically whitespace)
                    position += 1
                    remaining = remaining[1:]
            
            line_number += 1
        
        return tokens
    
    def _tokenize_typescript(self, content: str) -> List[Token]:
        """
        Tokenize TypeScript code (extends JavaScript tokenizer with TypeScript specifics).
        
        Args:
            content: TypeScript code content
            
        Returns:
            List[Token]: List of extracted tokens
        """
        # TypeScript tokenization is mostly the same as JavaScript
        # Just use JavaScript tokenizer and then adjust keyword recognition
        tokens = self._tokenize_javascript(content)
        
        # Update keywords to TypeScript-specific ones
        for i, token in enumerate(tokens):
            if token.token_type == TokenType.IDENTIFIER and token.value in self._KEYWORDS['typescript']:
                tokens[i] = Token(token.value, TokenType.KEYWORD, token.line, token.position)
        
        return tokens
    
    def _tokenize_java(self, content: str) -> List[Token]:
        """
        Tokenize Java code using regular expressions.
        
        Args:
            content: Java code content
            
        Returns:
            List[Token]: List of extracted tokens
        """
        # Define token patterns
        patterns = [
            # Comments
            (r'//.*?$', TokenType.COMMENT),                 # Single-line comment
            (r'/\*.*?\*/', TokenType.COMMENT),              # Multi-line comment
            # Strings
            (r'"(?:\\.|[^"\\])*"', TokenType.LITERAL),      # Double-quoted string
            (r"'(?:\\.|[^'\\])*'", TokenType.LITERAL),      # Character literal
            # Numbers
            (r'\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?[fFdDlL]?\b', TokenType.LITERAL),  # Numbers
            # Keywords and identifiers
            (r'\b([A-Za-z_$][\w$]*)\b', None),              # Identifiers and keywords (type determined later)
            # Operators and punctuation
            (r'[\+\-\*/%=&\|\^~<>!?:]+', None),             # Operators (type determined later)
            (r'[;,.()\[\]{}]', TokenType.PUNCTUATION),      # Punctuation
        ]
        
        tokens = []
        line_number = 1
        
        # Process content line by line to track line numbers
        for line in content.split('\n'):
            position = 0
            remaining = line
            
            while remaining:
                match = None
                match_type = None
                
                # Try each pattern
                for pattern, token_type in patterns:
                    regex_match = re.match(pattern, remaining, re.DOTALL)
                    if regex_match:
                        match = regex_match.group(0)
                        match_type = token_type
                        break
                
                if match:
                    # Determine token type for identifiers and keywords
                    if match_type is None:
                        if re.match(r'\b([A-Za-z_$][\w$]*)\b', match):
                            match_type = TokenType.KEYWORD if match in self._KEYWORDS['java'] else TokenType.IDENTIFIER
                        elif re.match(r'[\+\-\*/%=&\|\^~<>!?:]+', match):
                            match_type = TokenType.OPERATOR if match in self._OPERATORS['java'] else TokenType.PUNCTUATION
                    
                    # Add token if not whitespace
                    if not match.isspace():
                        tokens.append(Token(match, match_type, line_number, position))
                    
                    # Update position and remaining text
                    position += len(match)
                    remaining = remaining[len(match):]
                else:
                    # Skip character if no match (typically whitespace)
                    position += 1
                    remaining = remaining[1:]
            
            line_number += 1
        
        return tokens
    
    def _tokenize_cpp(self, content: str) -> List[Token]:
        """
        Tokenize C/C++ code using regular expressions.
        
        Args:
            content: C/C++ code content
            
        Returns:
            List[Token]: List of extracted tokens
        """
        # Define token patterns
        patterns = [
            # Comments
            (r'//.*?$', TokenType.COMMENT),                 # Single-line comment
            (r'/\*.*?\*/', TokenType.COMMENT),              # Multi-line comment
            # Preprocessor directives
            (r'#\s*\w+(?:\s+[^\n]*)?', TokenType.KEYWORD),  # Preprocessor directives
            # Strings
            (r'"(?:\\.|[^"\\])*"', TokenType.LITERAL),      # Double-quoted string
            (r"'(?:\\.|[^'\\])*'", TokenType.LITERAL),      # Character literal
            # Numbers
            (r'\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?[fFuUlL]*\b', TokenType.LITERAL),  # Numbers
            # Keywords and identifiers
            (r'\b([A-Za-z_][\w]*)\b', None),                # Identifiers and keywords (type determined later)
            # Operators and punctuation
            (r'[\+\-\*/%=&\|\^~<>!?:]+', None),             # Operators (type determined later)
            (r'[;,.()\[\]{}]', TokenType.PUNCTUATION),      # Punctuation
        ]
        
        tokens = []
        line_number = 1
        
        # Process content line by line to track line numbers
        for line in content.split('\n'):
            position = 0
            remaining = line
            
            while remaining:
                match = None
                match_type = None
                
                # Try each pattern
                for pattern, token_type in patterns:
                    regex_match = re.match(pattern, remaining, re.DOTALL)
                    if regex_match:
                        match = regex_match.group(0)
                        match_type = token_type
                        break
                
                if match:
                    # Determine token type for identifiers and keywords
                    if match_type is None:
                        if re.match(r'\b([A-Za-z_][\w]*)\b', match):
                            match_type = TokenType.KEYWORD if match in self._KEYWORDS['cpp'] else TokenType.IDENTIFIER
                        elif re.match(r'[\+\-\*/%=&\|\^~<>!?:]+', match):
                            match_type = TokenType.OPERATOR if match in self._OPERATORS['cpp'] else TokenType.PUNCTUATION
                    
                    # Add token if not whitespace
                    if not match.isspace():
                        tokens.append(Token(match, match_type, line_number, position))
                    
                    # Update position and remaining text
                    position += len(match)
                    remaining = remaining[len(match):]
                else:
                    # Skip character if no match (typically whitespace)
                    position += 1
                    remaining = remaining[1:]
            
            line_number += 1
        
        return tokens
    
    def _tokenize_generic(self, file_path: str) -> List[Token]:
        """
        Generic tokenizer for unsupported languages.
        
        This is a simplified tokenizer that splits content into words
        and punctuation without language-specific knowledge.
        
        Args:
            file_path: Path to the file to tokenize
            
        Returns:
            List[Token]: List of extracted tokens
        """
        tokens = []
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Simple pattern to split into words and punctuation
            pattern = r'[A-Za-z_][\w]*|[0-9]+(?:\.[0-9]+)?|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[^\w\s]+'
            
            line_number = 1
            position = 0
            
            for match in re.finditer(pattern, content):
                value = match.group(0)
                
                # Update line number and position
                line_delta = content[position:match.start()].count('\n')
                line_number += line_delta
                if line_delta > 0:
                    position = content.rfind('\n', position, match.start()) + 1
                
                # Determine token type (simplistic)
                if re.match(r'[A-Za-z_][\w]*', value):
                    token_type = TokenType.IDENTIFIER
                elif re.match(r'[0-9]+(?:\.[0-9]+)?', value):
                    token_type = TokenType.LITERAL
                elif re.match(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', value):
                    token_type = TokenType.LITERAL
                else:
                    token_type = TokenType.PUNCTUATION
                
                tokens.append(Token(value, token_type, line_number, match.start() - position))
                position = match.end()
        
        except Exception as e:
            logger.error(f"Error in generic tokenization for {file_path}: {e}")
        
        return tokens
    
    def get_token_sequence(self, tokens: List[Token], normalize: bool = True) -> List[str]:
        """
        Generate a sequence of token strings from a list of tokens.
        
        Args:
            tokens: List of tokens
            normalize: Whether to use normalized token values
            
        Returns:
            List[str]: List of token values
        """
        if normalize:
            return [token.normalized_value for token in tokens]
        else:
            return [token.value for token in tokens]
    
    def generate_ngrams(self, tokens: List[Token], n: int, 
                      skip_comments: bool = True, normalize: bool = True) -> List[Tuple[str, ...]]:
        """
        Generate n-grams from a token sequence.
        
        Args:
            tokens: List of tokens
            n: Size of each n-gram
            skip_comments: Whether to ignore comment tokens
            normalize: Whether to use normalized token values
            
        Returns:
            List[Tuple[str, ...]]: List of token n-grams
        """
        # Filter out comments if requested
        if skip_comments:
            filtered_tokens = [t for t in tokens if t.token_type != TokenType.COMMENT]
        else:
            filtered_tokens = tokens
        
        # Get token values (normalized or original)
        if normalize:
            token_values = [t.normalized_value for t in filtered_tokens]
        else:
            token_values = [t.value for t in filtered_tokens]
        
        # Generate n-grams
        ngrams = []
        for i in range(len(token_values) - n + 1):
            ngrams.append(tuple(token_values[i:i+n]))
        
        return ngrams
    
    def get_token_statistics(self, tokens: List[Token]) -> Dict[str, Any]:
        """
        Calculate statistics about tokens.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Dict[str, Any]: Token statistics
        """
        stats = {
            'total_tokens': len(tokens),
            'tokens_by_type': {},
            'unique_tokens': 0,
            'unique_normalized_tokens': 0,
            'token_distribution': {},
            'normalized_token_distribution': {}
        }
        
        # Count tokens by type
        type_counts = {}
        for token in tokens:
            type_name = token.token_type.name
            type_counts[type_name] = type_counts.get(type_name, 0) + 1
        
        stats['tokens_by_type'] = type_counts
        
        # Count unique tokens
        unique_tokens = set(token.value for token in tokens)
        unique_normalized = set(token.normalized_value for token in tokens)
        
        stats['unique_tokens'] = len(unique_tokens)
        stats['unique_normalized_tokens'] = len(unique_normalized)
        
        # Token distribution
        token_distribution = {}
        normalized_distribution = {}
        
        for token in tokens:
            token_distribution[token.value] = token_distribution.get(token.value, 0) + 1
            normalized_distribution[token.normalized_value] = normalized_distribution.get(token.normalized_value, 0) + 1
        
        stats['token_distribution'] = token_distribution
        stats['normalized_token_distribution'] = normalized_distribution
        
        return stats
