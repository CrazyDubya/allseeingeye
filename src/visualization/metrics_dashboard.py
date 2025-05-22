#!/usr/bin/env python3
"""
Metrics dashboard visualization for AllSeeingEye.

This module creates interactive dashboards of codebase metrics.
"""

import os
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from pathlib import Path
from collections import defaultdict, Counter
import datetime

# Configure logging
logger = logging.getLogger(__name__)

class MetricsDashboard:
    """
    Creates interactive dashboard visualizations of codebase metrics.
    
    This class calculates various metrics about a codebase and generates
    visualizations to help understand code quality, complexity, and structure.
    """
    
    def __init__(self, results=None, base_directory=None, excluded_dirs=None, excluded_files=None, 
                 max_file_size=1024*1024, metrics=None, cache_dir=None):
        """
        Initialize with either analysis results or directory to analyze.
        
        Args:
            results: Analysis results from AllSeeingEye.analyze()
            base_directory: Directory to analyze (alternative to results)
            excluded_dirs: Directories to exclude
            excluded_files: Files to exclude
            max_file_size: Maximum file size to process
            metrics: Metrics to calculate
            cache_dir: Directory for caching results
        """
        self.results = results
        
        if base_directory:
            self.base_directory = os.path.abspath(base_directory)
        elif results and isinstance(results, dict) and 'directory' in results:
            self.base_directory = results['directory']
        else:
            self.base_directory = os.getcwd()
            
        self.excluded_dirs = set(excluded_dirs or ['.git', 'node_modules', '.venv', '__pycache__', '.idea', '.vscode'])
        self.excluded_files = set(excluded_files or [])
        self.max_file_size = max_file_size
        
        # Default metrics to calculate
        self.metrics = metrics or [
            'file_counts', 'language_stats', 'complexity',
            'directory_size', 'file_size_distribution', 'code_to_comment_ratio'
        ]
        
        self.metrics_data = {}
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'metrics_dashboard.json') if cache_dir else None
        
    def generate(self):
        """Generate metrics dashboard visualization HTML."""
        # Extract metrics from results if available
        stats = {}
        if self.results and isinstance(self.results, dict):
            if 'stats' in self.results:
                stats = self.results['stats']
            elif 'statistics' in self.results:
                stats = self.results['statistics']
        
        # Create a simple dashboard HTML template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Codebase Metrics Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .dashboard {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
                .card {{ background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .card h3 {{ margin-top: 0; color: #6a5acd; }}
                .metric {{ font-size: 24px; font-weight: bold; color: #333; margin: 10px 0; }}
                .metric-label {{ color: #666; font-size: 14px; }}
                .chart-container {{ height: 300px; }}
            </style>
        </head>
        <body>
            <h1>Codebase Metrics Dashboard</h1>
            
            <div class="dashboard">
                <div class="card">
                    <h3>Files Overview</h3>
                    <div class="metric">{stats.get('total_files', 'N/A')}</div>
                    <div class="metric-label">Total Files</div>
                    <div class="metric">{stats.get('total_dirs', 'N/A')}</div>
                    <div class="metric-label">Directories</div>
                    <div class="metric">{stats.get('total_lines', 'N/A')}</div>
                    <div class="metric-label">Lines of Code</div>
                </div>
                
                <div class="card">
                    <h3>Size Analysis</h3>
                    <div class="metric">{stats.get('total_size_formatted', 'N/A')}</div>
                    <div class="metric-label">Total Size</div>
                    <div class="chart-container">
                        <canvas id="sizeChart"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <h3>File Types</h3>
                    <div class="chart-container">
                        <canvas id="fileTypesChart"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <h3>Analysis Metrics</h3>
                    <div class="metric">{stats.get('duration', 'N/A')} seconds</div>
                    <div class="metric-label">Analysis Time</div>
                    <div class="metric">{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                    <div class="metric-label">Generated At</div>
                </div>
            </div>
            
            <script>
                // Extract file category data from stats
                const fileCategories = {
                    labels: ['Code', 'Documentation', 'Configuration', 'Data', 'Media', 'Other'],
                    data: [
                        {stats.get('files_by_category', {}).get('code', 0)},
                        {stats.get('files_by_category', {}).get('documentation', 0)},
                        {stats.get('files_by_category', {}).get('configuration', 0)},
                        {stats.get('files_by_category', {}).get('data', 0)},
                        {stats.get('files_by_category', {}).get('media', 0)},
                        {stats.get('files_by_category', {}).get('other', 0)}
                    ]
                };
                
                // Sample size distribution for demonstration
                const sizeDistribution = {{
                    labels: ['<10KB', '10-100KB', '100KB-1MB', '>1MB'],
                    data: [65, 25, 8, 2]
                }};
                
                // Create charts
                const ctxFileTypes = document.getElementById('fileTypesChart').getContext('2d');
                new Chart(ctxFileTypes, {{
                    type: 'pie',
                    data: {{
                        labels: fileCategories.labels,
                        datasets: [{{
                            data: fileCategories.data,
                            backgroundColor: [
                                '#6a5acd',
                                '#2ecc71',
                                '#9b59b6',
                                '#f1c40f',
                                '#e74c3c',
                                '#95a5a6'
                            ]
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'right'
                            }}
                        }}
                    }}
                }});
                
                const ctxSize = document.getElementById('sizeChart').getContext('2d');
                new Chart(ctxSize, {{
                    type: 'bar',
                    data: {{
                        labels: sizeDistribution.labels,
                        datasets: [{{
                            label: 'File Size Distribution',
                            data: sizeDistribution.data,
                            backgroundColor: '#9370db'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                title: {{
                                    display: true,
                                    text: 'Number of Files'
                                }}
                            }},
                            x: {{
                                title: {{
                                    display: true,
                                    text: 'File Size Range'
                                }}
                            }}
                        }}
                    }}
                }});
            </script>
        </body>
        </html>
        """
        return html
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """
        Calculate all configured metrics for the codebase.
        
        Returns:
            Dict[str, Any]: Dictionary of calculated metrics
        """
        # Try to load from cache first
        if self.cache_file and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.metrics_data = json.load(f)
                    logger.info(f"Loaded metrics data from cache: {self.cache_file}")
                    return self.metrics_data
            except Exception as e:
                logger.warning(f"Failed to load from cache: {e}")
        
        # Initialize metrics dictionary
        self.metrics_data = {
            'general': {
                'total_files': 0,
                'total_directories': 0,
                'total_lines_of_code': 0,
                'total_size_bytes': 0,
                'analyzed_at': datetime.datetime.now().isoformat(),
                'base_directory': self.base_directory
            }
        }
        
        # File type stats
        file_types: Dict[str, Dict[str, Union[int, float]]] = {}
        
        # Language stats
        language_stats: Dict[str, Dict[str, Union[int, float]]] = {}
        
        # File sizes
        file_sizes = []
        
        # Directory sizes
        directory_sizes: Dict[str, int] = {}
        
        # Track file paths by extension
        files_by_extension: Dict[str, List[str]] = defaultdict(list)
        
        # Process all files
        for root, dirs, files in os.walk(self.base_directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs and 
                      os.path.relpath(os.path.join(root, d), self.base_directory) not in self.excluded_dirs]
            
            rel_dir = os.path.relpath(root, self.base_directory)
            self.metrics_data['general']['total_directories'] += 1
            
            # Initialize directory size
            directory_sizes[rel_dir] = 0
            
            # Process each file
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.base_directory)
                
                # Skip excluded files
                if file in self.excluded_files or rel_path in self.excluded_files:
                    continue
                
                # Get file size
                try:
                    file_size = os.path.getsize(file_path)
                except Exception as e:
                    logger.debug(f"Error getting size for {file_path}: {e}")
                    continue
                
                # Skip large files
                if file_size > self.max_file_size:
                    continue
                
                # Get file extension and determine type
                _, ext = os.path.splitext(file_path)
                ext = ext.lower()
                file_type = self._get_file_type(ext)
                language = self._get_language(ext)
                
                # Update general stats
                self.metrics_data['general']['total_files'] += 1
                self.metrics_data['general']['total_size_bytes'] += file_size
                
                # Update file type stats
                if file_type not in file_types:
                    file_types[file_type] = {'count': 0, 'total_size': 0}
                file_types[file_type]['count'] += 1
                file_types[file_type]['total_size'] += file_size
                
                # Update language stats if applicable
                if language:
                    if language not in language_stats:
                        language_stats[language] = {
                            'count': 0, 
                            'total_size': 0, 
                            'lines_of_code': 0,
                            'comment_lines': 0,
                            'blank_lines': 0
                        }
                    language_stats[language]['count'] += 1
                    language_stats[language]['total_size'] += file_size
                
                # Add to files by extension
                files_by_extension[ext].append(file_path)
                
                # Update file size list
                file_sizes.append({'path': rel_path, 'size': file_size, 'type': file_type})
                
                # Update directory size
                directory_sizes[rel_dir] += file_size
        
        # Calculate additional metrics based on configuration
        if 'file_counts' in self.metrics:
            self.metrics_data['file_types'] = file_types
        
        if 'language_stats' in self.metrics:
            # Calculate code lines for supported languages
            self._calculate_language_stats(language_stats, files_by_extension)
            self.metrics_data['languages'] = language_stats
        
        if 'file_size_distribution' in self.metrics:
            # Calculate file size distribution
            size_distribution = self._calculate_size_distribution(file_sizes)
            self.metrics_data['file_size_distribution'] = size_distribution
        
        if 'directory_size' in self.metrics:
            # Convert directory sizes to sorted list
            dir_size_list = [
                {'path': path, 'size': size} 
                for path, size in directory_sizes.items()
            ]
            dir_size_list.sort(key=lambda x: x['size'], reverse=True)
            self.metrics_data['directory_sizes'] = dir_size_list[:20]  # Top 20 directories
        
        if 'complexity' in self.metrics:
            # Calculate complexity metrics
            self.metrics_data['complexity'] = self._calculate_complexity_metrics(files_by_extension)
        
        # Format size values
        self.metrics_data['general']['total_size_formatted'] = self._format_size(
            self.metrics_data['general']['total_size_bytes']
        )
        
        # Save to cache if enabled
        if self.cache_file:
            try:
                os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
                with open(self.cache_file, 'w') as f:
                    json.dump(self.metrics_data, f)
                logger.info(f"Saved metrics data to cache: {self.cache_file}")
            except Exception as e:
                logger.warning(f"Failed to save to cache: {e}")
        
        return self.metrics_data
    
    def _calculate_language_stats(self, language_stats: Dict[str, Dict[str, Union[int, float]]], 
                                 files_by_extension: Dict[str, List[str]]) -> None:
        """
        Calculate language-specific statistics like lines of code and comments.
        
        Args:
            language_stats: Dictionary to update with stats
            files_by_extension: Dictionary of file paths by extension
        """
        # Define comment patterns by language
        comment_patterns = {
            'python': [r'^\s*#.*$', r'^\s*""".*?"""$', r'^\s*\'\'\'.*?\'\'\'$'],
            'javascript': [r'^\s*\/\/.*$', r'^\s*\/\*.*?\*\/$'],
            'typescript': [r'^\s*\/\/.*$', r'^\s*\/\*.*?\*\/$'],
            'java': [r'^\s*\/\/.*$', r'^\s*\/\*.*?\*\/$'],
            'cpp': [r'^\s*\/\/.*$', r'^\s*\/\*.*?\*\/$'],
            'go': [r'^\s*\/\/.*$', r'^\s*\/\*.*?\*\/$'],
            'ruby': [r'^\s*#.*$', r'^\s*=begin.*?=end$'],
            'html': [r'^\s*<!--.*?-->$'],
            'css': [r'^\s*\/\*.*?\*\/$'],
            'php': [r'^\s*\/\/.*$', r'^\s*\/\*.*?\*\/$', r'^\s*#.*$'],
            'shell': [r'^\s*#.*$']
        }
        
        # Extension to language mapping
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'cpp',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.h': 'cpp',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rb': 'ruby',
            '.html': 'html',
            '.css': 'css',
            '.php': 'php',
            '.sh': 'shell',
            '.bash': 'shell'
        }
        
        total_lines = 0
        
        # Process each extension type
        for ext, files in files_by_extension.items():
            lang = ext_to_lang.get(ext)
            if not lang or lang not in language_stats:
                continue
            
            patterns = comment_patterns.get(lang, [])
            
            # Process files for this language
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        total_lines += len(lines)
                        language_stats[lang]['lines_of_code'] += len(lines)
                        
                        for line in lines:
                            line = line.strip()
                            if not line:
                                language_stats[lang]['blank_lines'] += 1
                                language_stats[lang]['lines_of_code'] -= 1
                                continue
                            
                            is_comment = False
                            for pattern in patterns:
                                if re.match(pattern, line):
                                    language_stats[lang]['comment_lines'] += 1
                                    language_stats[lang]['lines_of_code'] -= 1
                                    is_comment = True
                                    break
                except Exception as e:
                    logger.debug(f"Error processing {file_path} for language stats: {e}")
        
        # Calculate comment ratios
        for lang, stats in language_stats.items():
            if stats['lines_of_code'] > 0:
                stats['comment_ratio'] = round(stats['comment_lines'] / (stats['lines_of_code'] + stats['comment_lines']), 2)
            else:
                stats['comment_ratio'] = 0
        
        # Update general stats
        self.metrics_data['general']['total_lines_of_code'] = total_lines
    
    def _calculate_size_distribution(self, file_sizes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate file size distribution statistics.
        
        Args:
            file_sizes: List of file size information
            
        Returns:
            Dict[str, Any]: Size distribution statistics
        """
        # Sort files by size
        file_sizes.sort(key=lambda x: x['size'], reverse=True)
        
        # Calculate distribution
        distribution = {
            'largest_files': file_sizes[:20],  # Top 20 largest files
            'size_ranges': {
                '0-1KB': 0,
                '1KB-10KB': 0,
                '10KB-100KB': 0,
                '100KB-1MB': 0,
                '1MB+': 0
            },
            'type_distribution': defaultdict(int)
        }
        
        # Calculate size ranges
        for file in file_sizes:
            size = file['size']
            
            if size < 1024:
                distribution['size_ranges']['0-1KB'] += 1
            elif size < 10 * 1024:
                distribution['size_ranges']['1KB-10KB'] += 1
            elif size < 100 * 1024:
                distribution['size_ranges']['10KB-100KB'] += 1
            elif size < 1024 * 1024:
                distribution['size_ranges']['100KB-1MB'] += 1
            else:
                distribution['size_ranges']['1MB+'] += 1
            
            # Add to type distribution
            file_type = file['type']
            distribution['type_distribution'][file_type] += file['size']
        
        # Format sizes for largest files
        for file in distribution['largest_files']:
            file['size_formatted'] = self._format_size(file['size'])
        
        # Convert type distribution to sorted list
        distribution['type_distribution'] = [
            {'type': k, 'size': v, 'size_formatted': self._format_size(v)}
            for k, v in distribution['type_distribution'].items()
        ]
        distribution['type_distribution'].sort(key=lambda x: x['size'], reverse=True)
        
        return distribution
    
    def _calculate_complexity_metrics(self, files_by_extension: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Calculate code complexity metrics.
        
        Args:
            files_by_extension: Dictionary of file paths by extension
            
        Returns:
            Dict[str, Any]: Complexity metrics
        """
        # Initialize complexity metrics
        complexity = {
            'cyclomatic_complexity': {},
            'max_complexity_files': [],
            'avg_complexity_by_language': {},
            'long_functions': []
        }
        
        # Function to estimate cyclomatic complexity
        def estimate_complexity(code: str, language: str) -> int:
            complexity = 1  # Base complexity
            
            # Different conditional patterns based on language
            if language == 'python':
                complexity += code.count('if ') + code.count('elif ') + code.count('for ') + code.count('while ')
                complexity += code.count('except:') + code.count('except ') + code.count(' and ') + code.count(' or ')
            elif language in ['javascript', 'typescript']:
                complexity += code.count('if(') + code.count('if (') + code.count('for(') + code.count('for (')
                complexity += code.count('while(') + code.count('while (') + code.count('case ') 
                complexity += code.count('&&') + code.count('||') + code.count('?')
            elif language in ['java', 'cpp']:
                complexity += code.count('if(') + code.count('if (') + code.count('for(') + code.count('for (')
                complexity += code.count('while(') + code.count('while (') + code.count('case ') 
                complexity += code.count('&&') + code.count('||') + code.count('?')
                complexity += code.count('catch(') + code.count('catch (')
            
            return complexity
        
        # Extensions to analyze
        extensions_to_analyze = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'cpp',
            '.cpp': 'cpp'
        }
        
        # Complexity by language
        complexity_by_lang = defaultdict(list)
        
        # Analyze files for complexity
        for ext, files in files_by_extension.items():
            if ext not in extensions_to_analyze:
                continue
            
            language = extensions_to_analyze[ext]
            
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Simple function detection
                        functions = []
                        
                        if language == 'python':
                            # Python functions and methods
                            function_matches = re.finditer(r'def\s+(\w+)\s*\(', content)
                            for match in function_matches:
                                func_name = match.group(1)
                                start_pos = match.start()
                                # Find end of function (heuristic)
                                end_pos = content.find('\ndef', start_pos + 1)
                                if end_pos == -1:
                                    end_pos = content.find('\nclass', start_pos + 1)
                                if end_pos == -1:
                                    end_pos = len(content)
                                func_code = content[start_pos:end_pos]
                                func_lines = func_code.count('\n') + 1
                                
                                # Calculate complexity
                                func_complexity = estimate_complexity(func_code, language)
                                
                                functions.append({
                                    'name': func_name,
                                    'lines': func_lines,
                                    'complexity': func_complexity
                                })
                        
                        elif language in ['javascript', 'typescript']:
                            # JS/TS functions
                            function_matches = re.finditer(r'function\s+(\w+)\s*\(|(\w+)\s*[:=]\s*function\s*\(|(\w+)\s*[:=]\s*\([^)]*\)\s*=>', content)
                            for match in function_matches:
                                func_name = match.group(1) or match.group(2) or match.group(3) or 'anonymous'
                                start_pos = match.start()
                                
                                # Find matching closing brace (simplified)
                                if '{' in content[start_pos:]:
                                    open_pos = content.find('{', start_pos)
                                    close_pos = open_pos + 1
                                    brace_count = 1
                                    
                                    while brace_count > 0 and close_pos < len(content):
                                        if content[close_pos] == '{':
                                            brace_count += 1
                                        elif content[close_pos] == '}':
                                            brace_count -= 1
                                        close_pos += 1
                                    
                                    func_code = content[start_pos:close_pos]
                                    func_lines = func_code.count('\n') + 1
                                    
                                    # Calculate complexity
                                    func_complexity = estimate_complexity(func_code, language)
                                    
                                    functions.append({
                                        'name': func_name,
                                        'lines': func_lines,
                                        'complexity': func_complexity
                                    })
                        
                        # Calculate file-level metrics
                        file_complexity = estimate_complexity(content, language)
                        rel_path = os.path.relpath(file_path, self.base_directory)
                        complexity['cyclomatic_complexity'][rel_path] = file_complexity
                        complexity_by_lang[language].append(file_complexity)
                        
                        # Add to max complexity files
                        complexity['max_complexity_files'].append({
                            'path': rel_path,
                            'complexity': file_complexity,
                            'language': language
                        })
                        
                        # Add long/complex functions
                        for func in functions:
                            if func['lines'] > 50 or func['complexity'] > 10:
                                complexity['long_functions'].append({
                                    'file': rel_path,
                                    'name': func['name'],
                                    'lines': func['lines'],
                                    'complexity': func['complexity']
                                })
                
                except Exception as e:
                    logger.debug(f"Error calculating complexity for {file_path}: {e}")
        
        # Sort max complexity files
        complexity['max_complexity_files'].sort(key=lambda x: x['complexity'], reverse=True)
        complexity['max_complexity_files'] = complexity['max_complexity_files'][:20]  # Top 20
        
        # Calculate average complexity by language
        for lang, values in complexity_by_lang.items():
            if values:
                avg_complexity = sum(values) / len(values)
                complexity['avg_complexity_by_language'][lang] = round(avg_complexity, 2)
        
        # Sort long functions
        complexity['long_functions'].sort(key=lambda x: x['complexity'], reverse=True)
        complexity['long_functions'] = complexity['long_functions'][:20]  # Top 20
        
        return complexity
    
    def _get_file_type(self, extension: str) -> str:
        """
        Determine file type based on extension.
        
        Args:
            extension: File extension
            
        Returns:
            str: File type
        """
        extension = extension.lower()
        
        # Code files
        if extension in ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.go', '.rs', '.rb',
                        '.php', '.swift', '.kt', '.scala', '.html', '.css', '.jsx', '.tsx']:
            return 'code'
        
        # Data files
        elif extension in ['.json', '.csv', '.tsv', '.xml', '.yaml', '.yml', '.toml', '.txt', '.log']:
            return 'data'
        
        # Documentation files
        elif extension in ['.md', '.rst', '.adoc', '.pdf', '.docx', '.epub', '.tex']:
            return 'documentation'
        
        # Configuration files
        elif extension in ['.ini', '.cfg', '.conf', '.properties', '.env'] or extension == '':
            return 'configuration'
        
        # Media files
        elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.mp3', '.wav', '.mp4', '.webm']:
            return 'media'
        
        # Archive files
        elif extension in ['.zip', '.tar', '.gz', '.tgz', '.7z', '.rar']:
            return 'archive'
        
        # Binary files
        elif extension in ['.exe', '.dll', '.so', '.dylib', '.pyc', '.class']:
            return 'binary'
        
        return 'other'
    
    def _get_language(self, extension: str) -> Optional[str]:
        """
        Map file extension to programming language.
        
        Args:
            extension: File extension
            
        Returns:
            Optional[str]: Language name or None
        """
        extension = extension.lower()
        
        # Language mapping
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.less': 'less',
            '.sql': 'sql',
            '.r': 'r',
            '.sh': 'shell',
            '.bash': 'shell',
            '.ps1': 'powershell'
        }
        
        return language_map.get(extension)
    
    def generate_html(self, output_file: str, title: str = "Codebase Metrics Dashboard") -> str:
        """
        Generate an interactive HTML dashboard visualization.
        
        Args:
            output_file: Path to save the HTML output
            title: Title for the dashboard
            
        Returns:
            str: Path to the generated HTML file
        """
        # Ensure metrics data is calculated
        if not self.metrics_data:
            self.calculate_metrics()
        
        # Define colors for different file types/languages
        colors = {
            'code': '#3572A5',
            'data': '#F1C40F',
            'documentation': '#2ECC71',
            'configuration': '#9B59B6',
            'media': '#E74C3C',
            'archive': '#95A5A6',
            'binary': '#34495E',
            'other': '#CCCCCC',
            
            'python': '#3572A5',
            'javascript': '#F7DF1E',
            'typescript': '#3178C6',
            'java': '#B07219',
            'cpp': '#F34B7D',
            'c': '#555555',
            'csharp': '#178600',
            'go': '#00ADD8',
            'rust': '#DEA584',
            'ruby': '#701516',
            'php': '#4F5D95',
            'swift': '#FFAC45',
            'kotlin': '#A97BFF',
            'scala': '#C22D40',
            'html': '#E34C26',
            'css': '#563D7C',
            'scss': '#CD6799',
            'sql': '#CCCCCC',
            'r': '#198CE7',
            'shell': '#89E051',
            'powershell': '#012456'
        }
        
        # Serialize the metrics data for JavaScript
        metrics_json = json.dumps(self.metrics_data)
        
        # Generate HTML with embedded charts using Chart.js
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-datalabels/2.0.0/chartjs-plugin-datalabels.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            padding: 20px;
            background-color: #fff;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        h1 {{
            margin: 0;
            color: #333;
            font-size: 24px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background-color: #fff;
            border-radius: 5px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-number {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #2980b9;
        }}
        .summary-label {{
            font-size: 14px;
            color: #7f8c8d;
        }}
        .chart-container {{
            background-color: #fff;
            border-radius: 5px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .chart-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        .chart-title {{
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin: 0;
        }}
        .chart {{
            width: 100%;
            height: 300px;
            position: relative;
        }}
        .chart-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .table-container {{
            background-color: #fff;
            border-radius: 5px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e1e1e1;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
            color: #333;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-size: 14px;
        }}
        .tabs {{
            display: flex;
            margin-bottom: 20px;
        }}
        .tab {{
            padding: 10px 20px;
            background-color: #f8f9fa;
            border: 1px solid #e1e1e1;
            border-bottom: none;
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
            cursor: pointer;
        }}
        .tab.active {{
            background-color: #fff;
            border-bottom: none;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            color: white;
        }}
        .badge-low {{
            background-color: #2ecc71;
        }}
        .badge-medium {{
            background-color: #f39c12;
        }}
        .badge-high {{
            background-color: #e74c3c;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>Generated on: <span id="generated-date"></span></p>
        </div>
        
        <div class="tabs">
            <div class="tab active" data-tab="overview">Overview</div>
            <div class="tab" data-tab="languages">Languages</div>
            <div class="tab" data-tab="complexity">Complexity</div>
            <div class="tab" data-tab="stats">File Stats</div>
        </div>
        
        <!-- Overview Tab -->
        <div class="tab-content active" id="overview-tab">
            <div class="summary">
                <div class="summary-card">
                    <div class="summary-number" id="total-files">-</div>
                    <div class="summary-label">Total Files</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number" id="total-dirs">-</div>
                    <div class="summary-label">Directories</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number" id="total-loc">-</div>
                    <div class="summary-label">Lines of Code</div>
                </div>
                <div class="summary-card">
                    <div class="summary-number" id="total-size">-</div>
                    <div class="summary-label">Total Size</div>
                </div>
            </div>
            
            <div class="chart-row">
                <div class="chart-container">
                    <div class="chart-header">
                        <h2 class="chart-title">File Types Distribution</h2>
                    </div>
                    <div class="chart">
                        <canvas id="file-types-chart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-header">
                        <h2 class="chart-title">Languages Distribution</h2>
                    </div>
                    <div class="chart">
                        <canvas id="languages-chart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="chart-row">
                <div class="chart-container">
                    <div class="chart-header">
                        <h2 class="chart-title">File Size Distribution</h2>
                    </div>
                    <div class="chart">
                        <canvas id="file-size-chart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-header">
                        <h2 class="chart-title">Top Directories by Size</h2>
                    </div>
                    <div class="chart">
                        <canvas id="directory-size-chart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Languages Tab -->
        <div class="tab-content" id="languages-tab">
            <div class="chart-container">
                <div class="chart-header">
                    <h2 class="chart-title">Language Statistics</h2>
                </div>
                <div class="chart">
                    <canvas id="language-stats-chart" height="100"></canvas>
                </div>
            </div>
            
            <div class="chart-row">
                <div class="chart-container">
                    <div class="chart-header">
                        <h2 class="chart-title">Lines of Code by Language</h2>
                    </div>
                    <div class="chart">
                        <canvas id="loc-by-language-chart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-header">
                        <h2 class="chart-title">Code to Comment Ratio</h2>
                    </div>
                    <div class="chart">
                        <canvas id="comment-ratio-chart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="table-container">
                <h2 class="chart-title">Language Details</h2>
                <table id="language-table">
                    <thead>
                        <tr>
                            <th>Language</th>
                            <th>Files</th>
                            <th>Lines of Code</th>
                            <th>Comments</th>
                            <th>Blank Lines</th>
                            <th>Comment Ratio</th>
                            <th>Total Size</th>
                        </tr>
                    </thead>
                    <tbody>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Complexity Tab -->
        <div class="tab-content" id="complexity-tab">
            <div class="chart-row">
                <div class="chart-container">
                    <div class="chart-header">
                        <h2 class="chart-title">Average Complexity by Language</h2>
                    </div>
                    <div class="chart">
                        <canvas id="complexity-by-language-chart"></canvas>
                    </div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-header">
                        <h2 class="chart-title">Complexity Distribution</h2>
                    </div>
                    <div class="chart">
                        <canvas id="complexity-distribution-chart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="table-container">
                <h2 class="chart-title">Most Complex Files</h2>
                <table id="complex-files-table">
                    <thead>
                        <tr>
                            <th>File</th>
                            <th>Language</th>
                            <th>Complexity</th>
                            <th>Risk</th>
                        </tr>
                    </thead>
                    <tbody>
                    </tbody>
                </table>
            </div>
            
            <div class="table-container">
                <h2 class="chart-title">Complex Functions</h2>
                <table id="complex-functions-table">
                    <thead>
                        <tr>
                            <th>File</th>
                            <th>Function</th>
                            <th>Lines</th>
                            <th>Complexity</th>
                            <th>Risk</th>
                        </tr>
                    </thead>
                    <tbody>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- File Stats Tab -->
        <div class="tab-content" id="stats-tab">
            <div class="chart-container">
                <div class="chart-header">
                    <h2 class="chart-title">File Size by Type</h2>
                </div>
                <div class="chart">
                    <canvas id="size-by-type-chart"></canvas>
                </div>
            </div>
            
            <div class="table-container">
                <h2 class="chart-title">Largest Files</h2>
                <table id="largest-files-table">
                    <thead>
                        <tr>
                            <th>File</th>
                            <th>Type</th>
                            <th>Size</th>
                        </tr>
                    </thead>
                    <tbody>
                    </tbody>
                </table>
            </div>
            
            <div class="table-container">
                <h2 class="chart-title">Largest Directories</h2>
                <table id="largest-dirs-table">
                    <thead>
                        <tr>
                            <th>Directory</th>
                            <th>Size</th>
                        </tr>
                    </thead>
                    <tbody>
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            Generated by AllSeeingEye | Metrics Dashboard
        </div>
    </div>
    
    <script>
    // Load metrics data
    const metricsData = {metrics_json};
    
    // Format size function
    function formatSize(bytes) {{
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }}
    
    // Format number with commas
    function formatNumber(num) {{
        return num.toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ",");
    }}
    
    // Set tab functionality
    document.querySelectorAll('.tab').forEach(tab => {{
        tab.addEventListener('click', () => {{
            // Remove active class from all tabs and content
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked tab
            tab.classList.add('active');
            
            // Show corresponding content
            const tabName = tab.getAttribute('data-tab');
            document.getElementById(tabName + '-tab').classList.add('active');
        }});
    }});
    
    // Fill summary data
    document.getElementById('total-files').textContent = formatNumber(metricsData.general.total_files);
    document.getElementById('total-dirs').textContent = formatNumber(metricsData.general.total_directories);
    document.getElementById('total-loc').textContent = formatNumber(metricsData.general.total_lines_of_code);
    document.getElementById('total-size').textContent = metricsData.general.total_size_formatted;
    document.getElementById('generated-date').textContent = new Date(metricsData.general.analyzed_at).toLocaleString();
    
    // Chart.js global settings
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
    Chart.defaults.font.size = 12;
    Chart.defaults.layout.padding = 20;
    Chart.defaults.plugins.legend.position = 'right';
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    
    // Create File Types Chart
    if (metricsData.file_types) {{
        const fileTypesCtx = document.getElementById('file-types-chart').getContext('2d');
        const fileTypes = Object.keys(metricsData.file_types);
        const fileTypeCounts = fileTypes.map(type => metricsData.file_types[type].count);
        const fileTypeColors = fileTypes.map(type => '{colors.get('code', '#CCCCCC')}');
        
        const fileTypesChart = new Chart(fileTypesCtx, {{
            type: 'doughnut',
            data: {{
                labels: fileTypes.map(t => t.charAt(0).toUpperCase() + t.slice(1)),
                datasets: [{{
                    data: fileTypeCounts,
                    backgroundColor: fileTypes.map(type => colors[type] || '#CCCCCC'),
                    borderWidth: 1
                }}]
            }},
            options: {{
                plugins: {{
                    datalabels: {{
                        formatter: (value, ctx) => {{
                            let sum = 0;
                            let dataArr = ctx.chart.data.datasets[0].data;
                            dataArr.map(data => {{
                                sum += data;
                            }});
                            let percentage = (value * 100 / sum).toFixed(1) + "%";
                            return percentage;
                        }},
                        color: '#fff',
                        font: {{
                            weight: 'bold'
                        }}
                    }}
                }},
                tooltips: {{
                    callbacks: {{
                        label: function(tooltipItem, data) {{
                            const label = data.labels[tooltipItem.index];
                            const value = data.datasets[0].data[tooltipItem.index];
                            return `${{label}}: ${{value}} files`;
                        }}
                    }}
                }}
            }}
        }});
    }}
    
    // Create Languages Chart
    if (metricsData.languages) {{
        const languagesCtx = document.getElementById('languages-chart').getContext('2d');
        const languages = Object.keys(metricsData.languages);
        const languageCounts = languages.map(lang => metricsData.languages[lang].count);
        
        const languagesChart = new Chart(languagesCtx, {{
            type: 'doughnut',
            data: {{
                labels: languages,
                datasets: [{{
                    data: languageCounts,
                    backgroundColor: languages.map(lang => colors[lang] || '#CCCCCC'),
                    borderWidth: 1
                }}]
            }},
            options: {{
                plugins: {{
                    datalabels: {{
                        formatter: (value, ctx) => {{
                            let sum = 0;
                            let dataArr = ctx.chart.data.datasets[0].data;
                            dataArr.map(data => {{
                                sum += data;
                            }});
                            let percentage = (value * 100 / sum).toFixed(1) + "%";
                            return percentage;
                        }},
                        color: '#fff',
                        font: {{
                            weight: 'bold'
                        }}
                    }}
                }}
            }}
        }});
        
        // Create Language Stats Table
        const langTable = document.getElementById('language-table').getElementsByTagName('tbody')[0];
        languages.forEach(lang => {{
            const stats = metricsData.languages[lang];
            const row = langTable.insertRow();
            
            row.insertCell(0).textContent = lang;
            row.insertCell(1).textContent = formatNumber(stats.count);
            row.insertCell(2).textContent = formatNumber(stats.lines_of_code);
            row.insertCell(3).textContent = formatNumber(stats.comment_lines);
            row.insertCell(4).textContent = formatNumber(stats.blank_lines);
            row.insertCell(5).textContent = (stats.comment_ratio * 100).toFixed(1) + '%';
            row.insertCell(6).textContent = formatSize(stats.total_size);
        }});
        
        // Create Lines of Code by Language Chart
        const locCtx = document.getElementById('loc-by-language-chart').getContext('2d');
        const locChart = new Chart(locCtx, {{
            type: 'bar',
            data: {{
                labels: languages,
                datasets: [{{
                    label: 'Lines of Code',
                    data: languages.map(lang => metricsData.languages[lang].lines_of_code),
                    backgroundColor: languages.map(lang => colors[lang] || '#CCCCCC'),
                    borderWidth: 1
                }}]
            }},
            options: {{
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Lines of Code'
                        }}
                    }}
                }}
            }}
        }});
        
        // Create Comment Ratio Chart
        const commentCtx = document.getElementById('comment-ratio-chart').getContext('2d');
        const commentChart = new Chart(commentCtx, {{
            type: 'horizontalBar',
            data: {{
                labels: languages,
                datasets: [{{
                    label: 'Code',
                    data: languages.map(lang => 1 - metricsData.languages[lang].comment_ratio),
                    backgroundColor: '#3498db',
                    stack: 'Stack 0'
                }},
                {{
                    label: 'Comments',
                    data: languages.map(lang => metricsData.languages[lang].comment_ratio),
                    backgroundColor: '#2ecc71',
                    stack: 'Stack 0'
                }}]
            }},
            options: {{
                scales: {{
                    x: {{
                        stacked: true,
                        max: 1,
                        ticks: {{
                            callback: function(value) {{
                                return value * 100 + '%';
                            }}
                        }}
                    }},
                    y: {{
                        stacked: true
                    }}
                }},
                plugins: {{
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                let label = context.dataset.label || '';
                                if (label) {{
                                    label += ': ';
                                }}
                                label += (context.raw * 100).toFixed(1) + '%';
                                return label;
                            }}
                        }}
                    }}
                }}
            }}
        }});
    }}
    
    // Create File Size Distribution Chart
    if (metricsData.file_size_distribution) {{
        const sizeDistCtx = document.getElementById('file-size-chart').getContext('2d');
        const sizeRanges = Object.keys(metricsData.file_size_distribution.size_ranges);
        const sizeRangeCounts = sizeRanges.map(range => metricsData.file_size_distribution.size_ranges[range]);
        
        const sizeDistChart = new Chart(sizeDistCtx, {{
            type: 'bar',
            data: {{
                labels: sizeRanges,
                datasets: [{{
                    label: 'Number of Files',
                    data: sizeRangeCounts,
                    backgroundColor: '#3498db',
                    borderWidth: 1
                }}]
            }},
            options: {{
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Number of Files'
                        }}
                    }}
                }}
            }}
        }});
        
        // Create Size by Type Chart
        const sizeByTypeCtx = document.getElementById('size-by-type-chart').getContext('2d');
        const typeDistribution = metricsData.file_size_distribution.type_distribution;
        
        const sizeByTypeChart = new Chart(sizeByTypeCtx, {{
            type: 'pie',
            data: {{
                labels: typeDistribution.map(item => item.type),
                datasets: [{{
                    data: typeDistribution.map(item => item.size),
                    backgroundColor: typeDistribution.map(item => colors[item.type] || '#CCCCCC'),
                    borderWidth: 1
                }}]
            }},
            options: {{
                plugins: {{
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const item = typeDistribution[context.dataIndex];
                                return `${{item.type}}: ${{item.size_formatted}}`;
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Populate Largest Files Table
        const largestFilesTable = document.getElementById('largest-files-table').getElementsByTagName('tbody')[0];
        metricsData.file_size_distribution.largest_files.forEach(file => {{
            const row = largestFilesTable.insertRow();
            row.insertCell(0).textContent = file.path;
            row.insertCell(1).textContent = file.type;
            row.insertCell(2).textContent = file.size_formatted;
        }});
    }}
    
    // Create Directory Size Chart
    if (metricsData.directory_sizes) {{
        const dirSizeCtx = document.getElementById('directory-size-chart').getContext('2d');
        
        // Get top 10 directories
        const topDirs = metricsData.directory_sizes.slice(0, 10);
        
        const dirSizeChart = new Chart(dirSizeCtx, {{
            type: 'bar',
            data: {{
                labels: topDirs.map(dir => dir.path === '' ? '(root)' : dir.path),
                datasets: [{{
                    label: 'Directory Size',
                    data: topDirs.map(dir => dir.size),
                    backgroundColor: '#9b59b6',
                    borderWidth: 1
                }}]
            }},
            options: {{
                indexAxis: 'y',
                scales: {{
                    x: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Size (bytes)'
                        }},
                        ticks: {{
                            callback: function(value) {{
                                return formatSize(value);
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Populate Largest Directories Table
        const largestDirsTable = document.getElementById('largest-dirs-table').getElementsByTagName('tbody')[0];
        metricsData.directory_sizes.forEach(dir => {{
            const row = largestDirsTable.insertRow();
            row.insertCell(0).textContent = dir.path === '' ? '(root)' : dir.path;
            row.insertCell(1).textContent = formatSize(dir.size);
        }});
    }}
    
    // Create Complexity Charts
    if (metricsData.complexity) {{
        // Average Complexity by Language
        if (metricsData.complexity.avg_complexity_by_language) {{
            const avgComplexityCtx = document.getElementById('complexity-by-language-chart').getContext('2d');
            const langs = Object.keys(metricsData.complexity.avg_complexity_by_language);
            const avgComplexities = langs.map(lang => metricsData.complexity.avg_complexity_by_language[lang]);
            
            const avgComplexityChart = new Chart(avgComplexityCtx, {{
                type: 'bar',
                data: {{
                    labels: langs,
                    datasets: [{{
                        label: 'Average Complexity',
                        data: avgComplexities,
                        backgroundColor: langs.map(lang => colors[lang] || '#CCCCCC'),
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Cyclomatic Complexity'
                            }}
                        }}
                    }}
                }}
            }});
        }}
        
        // Complexity Distribution
        const complexityDistCtx = document.getElementById('complexity-distribution-chart').getContext('2d');
        
        // Count complexity ranges
        const complexityValues = Object.values(metricsData.complexity.cyclomatic_complexity || {{}});
        const complexityRanges = {{
            '1-5': 0,
            '6-10': 0,
            '11-15': 0,
            '16-20': 0,
            '21-30': 0,
            '31+': 0
        }};
        
        complexityValues.forEach(value => {{
            if (value <= 5) complexityRanges['1-5']++;
            else if (value <= 10) complexityRanges['6-10']++;
            else if (value <= 15) complexityRanges['11-15']++;
            else if (value <= 20) complexityRanges['16-20']++;
            else if (value <= 30) complexityRanges['21-30']++;
            else complexityRanges['31+']++;
        }});
        
        const complexityDistChart = new Chart(complexityDistCtx, {{
            type: 'bar',
            data: {{
                labels: Object.keys(complexityRanges),
                datasets: [{{
                    label: 'Number of Files',
                    data: Object.values(complexityRanges),
                    backgroundColor: [
                        '#2ecc71', // Low (green)
                        '#2ecc71',
                        '#f39c12', // Medium (orange)
                        '#f39c12',
                        '#e74c3c', // High (red)
                        '#e74c3c'
                    ],
                    borderWidth: 1
                }}]
            }},
            options: {{
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Number of Files'
                        }}
                    }}
                }}
            }}
        }});
        
        // Populate Complex Files Table
        const complexFilesTable = document.getElementById('complex-files-table').getElementsByTagName('tbody')[0];
        
        if (metricsData.complexity.max_complexity_files) {{
            metricsData.complexity.max_complexity_files.forEach(file => {{
                const row = complexFilesTable.insertRow();
                
                // Determine risk level
                let risk = 'Low';
                let badgeClass = 'badge-low';
                
                if (file.complexity > 15) {{
                    risk = 'High';
                    badgeClass = 'badge-high';
                }} else if (file.complexity > 10) {{
                    risk = 'Medium';
                    badgeClass = 'badge-medium';
                }}
                
                row.insertCell(0).textContent = file.path;
                row.insertCell(1).textContent = file.language;
                row.insertCell(2).textContent = file.complexity;
                
                const riskCell = row.insertCell(3);
                riskCell.innerHTML = `<span class="badge ${{badgeClass}}">${{risk}}</span>`;
            }});
        }}
        
        // Populate Complex Functions Table
        const complexFunctionsTable = document.getElementById('complex-functions-table').getElementsByTagName('tbody')[0];
        
        if (metricsData.complexity.long_functions) {{
            metricsData.complexity.long_functions.forEach(func => {{
                const row = complexFunctionsTable.insertRow();
                
                // Determine risk level
                let risk = 'Low';
                let badgeClass = 'badge-low';
                
                if (func.complexity > 15 || func.lines > 100) {{
                    risk = 'High';
                    badgeClass = 'badge-high';
                }} else if (func.complexity > 10 || func.lines > 50) {{
                    risk = 'Medium';
                    badgeClass = 'badge-medium';
                }}
                
                row.insertCell(0).textContent = func.file;
                row.insertCell(1).textContent = func.name;
                row.insertCell(2).textContent = func.lines;
                row.insertCell(3).textContent = func.complexity;
                
                const riskCell = row.insertCell(4);
                riskCell.innerHTML = `<span class="badge ${{badgeClass}}">${{risk}}</span>`;
            }});
        }}
    }}
    
    // Register chart.js plugins
    Chart.register(ChartDataLabels);
    </script>
</body>
</html>
"""
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Metrics dashboard saved to {output_file}")
        return output_file
    
    def export_json(self, output_file: str) -> str:
        """
        Export the metrics data as JSON for custom visualization.
        
        Args:
            output_file: Path to save the JSON output
            
        Returns:
            str: Path to the generated JSON file
        """
        # Ensure metrics data is calculated
        if not self.metrics_data:
            self.calculate_metrics()
        
        with open(output_file, 'w') as f:
            json.dump(self.metrics_data, f, indent=2)
        
        logger.info(f"Metrics data exported to {output_file}")
        return output_file
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024 or unit == 'TB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
