#!/usr/bin/env python3
"""
Base exporter class for AllSeeingEye analysis results
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AllSeeingEye-Exporter")

class BaseExporter(ABC):
    """Base class for exporting analysis results to different formats"""
    
    def __init__(self, theme: str = "default", **kwargs):
        """
        Initialize the exporter.
        
        Args:
            theme: Theme name for styling
            **kwargs: Additional configuration options
        """
        self.theme = theme
        self.config = kwargs
    
    @abstractmethod
    def export(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Export analysis data to the specified format.
        
        Args:
            data: Analysis data dictionary
            output_path: Path to write the output file
            
        Returns:
            Path to the exported file
        """
        pass
    
    def load_input_data(self, input_path: str) -> Dict[str, Any]:
        """
        Load input data from a file.
        
        Args:
            input_path: Path to input file (JSON)
            
        Returns:
            Data dictionary
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading input data: {e}")
            raise
    
    def ensure_output_directory(self, output_path: str) -> None:
        """
        Ensure the output directory exists.
        
        Args:
            output_path: Output file path
        """
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
    
    def get_file_extension(self) -> str:
        """
        Get the file extension for this exporter.
        
        Returns:
            File extension (with dot)
        """
        return ".txt"
    
    def get_template_path(self, template_name: str) -> str:
        """
        Get the path to a template file.
        
        Args:
            template_name: Template name
            
        Returns:
            Template file path
        """
        # Get the directory of this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Construct template path
        return os.path.join(current_dir, 'templates', template_name)
    
    def get_theme_config(self) -> Dict[str, Any]:
        """
        Get theme configuration.
        
        Returns:
            Theme configuration dictionary
        """
        theme_config = {
            'default': {
                'primary_color': '#4682B4',
                'secondary_color': '#6495ED',
                'background_color': '#FFFFFF',
                'text_color': '#333333',
                'highlight_color': '#5F9EA0',
                'border_color': '#DDDDDD',
                'font_family': 'Arial, sans-serif'
            },
            'dark': {
                'primary_color': '#2C3E50',
                'secondary_color': '#3498DB',
                'background_color': '#1E1E1E',
                'text_color': '#F0F0F0',
                'highlight_color': '#3498DB',
                'border_color': '#444444',
                'font_family': 'Arial, sans-serif'
            },
            'light': {
                'primary_color': '#3498DB',
                'secondary_color': '#2980B9',
                'background_color': '#F8F9FA',
                'text_color': '#333333',
                'highlight_color': '#2980B9',
                'border_color': '#DDDDDD',
                'font_family': 'Arial, sans-serif'
            }
        }
        
        return theme_config.get(self.theme, theme_config['default'])
    
    def format_statistics(self, statistics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format statistics for display.
        
        Args:
            statistics: Statistics dictionary
            
        Returns:
            Formatted statistics
        """
        formatted = {}
        
        # Format total files
        if 'total_files' in statistics:
            formatted['total_files'] = f"{statistics['total_files']:,}"
        
        # Format total lines
        if 'total_lines' in statistics:
            formatted['total_lines'] = f"{statistics['total_lines']:,}"
        
        # Format files by category
        if 'files_by_category' in statistics:
            formatted['files_by_category'] = {
                k: f"{v:,}" for k, v in statistics['files_by_category'].items()
            }
        
        # Format languages
        if 'languages' in statistics:
            formatted['languages'] = statistics['languages']
        
        return formatted
    
    def format_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format recommendations for display.
        
        Args:
            recommendations: List of recommendation dictionaries
            
        Returns:
            Formatted recommendations
        """
        # Add complexity class
        for rec in recommendations:
            if 'complexity' in rec:
                complexity = rec['complexity'].lower()
                if complexity in ('low', 'medium', 'high'):
                    rec['complexity_class'] = complexity
                else:
                    rec['complexity_class'] = 'medium'
        
        return recommendations
