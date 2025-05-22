#!/usr/bin/env python3
"""
HTML exporter for AllSeeingEye analysis results
"""

import os
import json
import logging
import datetime
from typing import Dict, Any, List, Optional

from .base_exporter import BaseExporter

# Try to import jinja2
try:
    import jinja2
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    logging.warning("jinja2 not available. HTML export will use basic template.")

class HtmlExporter(BaseExporter):
    """Exporter for HTML format"""
    
    def __init__(self, 
                 theme: str = "default", 
                 template: Optional[str] = None,
                 include_structure: bool = True,
                 **kwargs):
        """
        Initialize the HTML exporter.
        
        Args:
            theme: Theme name
            template: Optional custom template path
            include_structure: Whether to include file structure
            **kwargs: Additional configuration options
        """
        super().__init__(theme, **kwargs)
        self.template_path = template
        self.include_structure = include_structure
    
    def get_file_extension(self) -> str:
        """
        Get the file extension for this exporter.
        
        Returns:
            File extension (with dot)
        """
        return ".html"
    
    def export(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Export analysis data to HTML.
        
        Args:
            data: Analysis data dictionary
            output_path: Path to write the output file
            
        Returns:
            Path to the exported file
        """
        # Ensure output directory exists
        self.ensure_output_directory(output_path)
        
        # Add file extension if not present
        if not output_path.endswith('.html'):
            output_path += '.html'
        
        # Prepare template data
        template_data = self._prepare_template_data(data)
        
        # Generate HTML content
        if JINJA2_AVAILABLE:
            content = self._render_with_jinja2(template_data)
        else:
            content = self._render_basic(template_data)
        
        # Write output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logging.info(f"Exported HTML report to: {output_path}")
        return output_path
    
    def _prepare_template_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data for template rendering.
        
        Args:
            data: Analysis data
            
        Returns:
            Template data dictionary
        """
        # Get basic metadata
        title = data.get('metadata', {}).get('directory', 'Codebase')
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Format statistics
        statistics = self.format_statistics(data.get('statistics', {}))
        
        # Format recommendations
        recommendations = self.format_recommendations(data.get('recommendations', []))
        
        # Prepare file categories
        file_categories = []
        if 'files' in data:
            # Group files by category
            files_by_category = {}
            for file_path, file_info in data['files'].items():
                category = file_info.get('category', 'Unknown')
                
                if category not in files_by_category:
                    files_by_category[category] = []
                
                # Add formatted size
                size = file_info.get('size', 0)
                if size < 1024:
                    size_formatted = f"{size} B"
                elif size < 1024 * 1024:
                    size_formatted = f"{size / 1024:.1f} KB"
                else:
                    size_formatted = f"{size / (1024 * 1024):.1f} MB"
                
                files_by_category[category].append({
                    'path': file_path,
                    'lines': file_info.get('lines'),
                    'size': size,
                    'size_formatted': size_formatted
                })
            
            # Create file categories list
            for category, files in files_by_category.items():
                # Sort files by path
                files.sort(key=lambda x: x['path'])
                
                file_categories.append({
                    'name': category,
                    'files': files
                })
            
            # Sort categories by name
            file_categories.sort(key=lambda x: x['name'])
        
        # Generate file structure
        file_structure = None
        if self.include_structure and 'structure' in data:
            file_structure = data['structure']
        
        # Return template data
        return {
            'title': title,
            'timestamp': timestamp,
            'statistics': statistics,
            'recommendations': recommendations,
            'file_categories': file_categories,
            'file_structure': file_structure,
            'theme': self.get_theme_config()
        }
    
    def _render_with_jinja2(self, template_data: Dict[str, Any]) -> str:
        """
        Render HTML using Jinja2.
        
        Args:
            template_data: Template data
            
        Returns:
            HTML content
        """
        # Get template path
        if self.template_path and os.path.exists(self.template_path):
            template_path = self.template_path
        else:
            template_path = self.get_template_path('html_template.html')
        
        # Create Jinja2 environment
        template_dir = os.path.dirname(template_path)
        template_name = os.path.basename(template_path)
        
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Render template
        template = env.get_template(template_name)
        return template.render(**template_data)
    
    def _render_basic(self, template_data: Dict[str, Any]) -> str:
        """
        Render basic HTML without Jinja2.
        
        Args:
            template_data: Template data
            
        Returns:
            HTML content
        """
        # Create basic HTML
        title = template_data['title']
        timestamp = template_data['timestamp']
        statistics = template_data['statistics']
        recommendations = template_data['recommendations']
        
        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AllSeeingEye Analysis: {title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        h1, h2, h3 {{ color: #4682B4; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4682B4; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>AllSeeingEye Analysis: {title}</h1>
    <p>Generated: {timestamp}</p>
    
    <h2>Statistics</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Value</th>
        </tr>
        <tr>
            <td>Total Files</td>
            <td>{statistics.get('total_files', 0)}</td>
        </tr>"""
        
        if 'total_lines' in statistics:
            html += f"""
        <tr>
            <td>Total Lines</td>
            <td>{statistics['total_lines']}</td>
        </tr>"""
        
        html += f"""
    </table>
    
    <h3>Files by Category</h3>
    <table>
        <tr>
            <th>Category</th>
            <th>Count</th>
        </tr>"""
        
        for category, count in statistics.get('files_by_category', {}).items():
            html += f"""
        <tr>
            <td>{category}</td>
            <td>{count}</td>
        </tr>"""
        
        html += """
    </table>
    """
        
        if recommendations:
            html += """
    <h2>Recommendations</h2>
    """
            
            for rec in recommendations:
                html += f"""
    <div style="margin-bottom: 20px; border-left: 4px solid #4682B4; padding: 10px;">
        <h3>{rec['title']}</h3>
        <p>{rec['description']}</p>
        <p><strong>Complexity:</strong> {rec['complexity']}</p>
    </div>"""
        
        html += """
</body>
</html>"""
        
        return html
