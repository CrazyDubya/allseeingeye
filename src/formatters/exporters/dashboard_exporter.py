#!/usr/bin/env python3
"""
Interactive dashboard exporter for AllSeeingEye analysis results
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
    logging.warning("jinja2 not available. Dashboard export will be limited.")

class DashboardExporter(BaseExporter):
    """Exporter for interactive dashboard format"""
    
    def __init__(self, 
                 theme: str = "default", 
                 template: Optional[str] = None,
                 include_structure: bool = True,
                 **kwargs):
        """
        Initialize the dashboard exporter.
        
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
        Export analysis data to an interactive dashboard.
        
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
        
        # Generate dashboard content
        if JINJA2_AVAILABLE:
            content = self._render_with_jinja2(template_data)
        else:
            content = self._render_basic(template_data)
        
        # Write output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logging.info(f"Exported dashboard to: {output_path}")
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
        
        # Generate treemap data
        treemap_data = self._generate_treemap_data(data)
        
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
            'treemap_data': json.dumps(treemap_data),
            'theme': self.get_theme_config()
        }
    
    def _generate_treemap_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate data for the treemap visualization.
        
        Args:
            data: Analysis data
            
        Returns:
            Treemap data dictionary
        """
        # Create root node
        root = {
            'name': data.get('metadata', {}).get('directory', 'Codebase'),
            'children': []
        }
        
        if 'files' not in data:
            return root
        
        # Group files by directory
        directories = {}
        
        for file_path, file_info in data['files'].items():
            # Split path into parts
            path_parts = file_path.split('/')
            
            # Skip if no parts
            if not path_parts:
                continue
            
            # Process path
            current_dir = ""
            current_node = root
            
            # Process directory parts
            for i, part in enumerate(path_parts[:-1]):
                if not part:  # Skip empty parts
                    continue
                
                # Update current directory path
                if current_dir:
                    current_dir += '/' + part
                else:
                    current_dir = part
                
                # Create directory node if it doesn't exist
                dir_exists = False
                for child in current_node.get('children', []):
                    if child['name'] == part:
                        current_node = child
                        dir_exists = True
                        break
                
                if not dir_exists:
                    # Create new directory node
                    new_dir = {
                        'name': part,
                        'children': []
                    }
                    
                    # Add to current node
                    if 'children' not in current_node:
                        current_node['children'] = []
                    
                    current_node['children'].append(new_dir)
                    current_node = new_dir
            
            # Process file
            filename = path_parts[-1]
            if filename:
                # Create file node
                file_node = {
                    'name': filename,
                    'value': file_info.get('size', 1),  # Use size or 1 for treemap
                    'category': file_info.get('category', 'Unknown'),
                    'lines': file_info.get('lines'),
                }
                
                # Add size formatted
                size = file_info.get('size', 0)
                if size < 1024:
                    file_node['size_formatted'] = f"{size} B"
                elif size < 1024 * 1024:
                    file_node['size_formatted'] = f"{size / 1024:.1f} KB"
                else:
                    file_node['size_formatted'] = f"{size / (1024 * 1024):.1f} MB"
                
                # Add to current node
                if 'children' not in current_node:
                    current_node['children'] = []
                
                current_node['children'].append(file_node)
        
        return root
    
    def _render_with_jinja2(self, template_data: Dict[str, Any]) -> str:
        """
        Render dashboard using Jinja2.
        
        Args:
            template_data: Template data
            
        Returns:
            HTML content
        """
        # Get template path
        if self.template_path and os.path.exists(self.template_path):
            template_path = self.template_path
        else:
            template_path = self.get_template_path('dashboard_template.html')
        
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
        Render basic dashboard without Jinja2.
        
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
    <title>AllSeeingEye Dashboard: {title}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        h1, h2, h3 {{ color: #4682B4; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .card {{ border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-bottom: 20px; }}
        .card-header {{ background-color: #4682B4; color: white; border-radius: 10px 10px 0 0 !important; }}
        .stats-card {{ text-align: center; padding: 15px; }}
        .stats-card .value {{ font-size: 2.5rem; font-weight: bold; color: #4682B4; }}
        .stats-card .label {{ font-size: 1rem; color: #666; }}
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="#">AllSeeingEye Dashboard</a>
        </div>
    </nav>

    <div class="container mt-4">
        <div class="row mb-4">
            <div class="col-12 mb-4">
                <h2>Overview: {title}</h2>
                <p class="text-muted">Generated: {timestamp}</p>
            </div>
            
            <div class="col-md-3">
                <div class="card stats-card">
                    <div class="value">{statistics.get('total_files', 0)}</div>
                    <div class="label">Total Files</div>
                </div>
            </div>"""
        
        if 'total_lines' in statistics:
            html += f"""
            <div class="col-md-3">
                <div class="card stats-card">
                    <div class="value">{statistics['total_lines']}</div>
                    <div class="label">Total Lines</div>
                </div>
            </div>"""
        
        html += f"""
            <div class="col-md-3">
                <div class="card stats-card">
                    <div class="value">{len(statistics.get('files_by_category', {}))}</div>
                    <div class="label">Categories</div>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">Files by Category</div>
                    <div class="card-body">
                        <canvas id="category-chart"></canvas>
                    </div>
                </div>
            </div>
        </div>"""
        
        if recommendations:
            html += """
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">Recommendations</div>
                    <div class="card-body">"""
            
            for rec in recommendations:
                complexity_class = rec.get('complexity_class', 'medium')
                html += f"""
                        <div class="mb-4 p-3 border-start border-4 border-primary">
                            <h4>{rec['title']}</h4>
                            <p>{rec['description']}</p>
                            <p><strong>Complexity:</strong> {rec['complexity']}</p>
                        </div>"""
            
            html += """
                    </div>
                </div>
            </div>
        </div>"""
        
        html += """
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Category Chart
        const categoryData = {
            labels: ["""
        
        for category in statistics.get('files_by_category', {}):
            html += f"'{category}',"
        
        html += """
            ],
            datasets: [{
                label: 'Files by Category',
                data: ["""
        
        for category, count in statistics.get('files_by_category', {}).items():
            html += f"{count},"
        
        html += """
                ],
                backgroundColor: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)',
                    'rgba(255, 159, 64, 0.7)',
                    'rgba(199, 199, 199, 0.7)',
                    'rgba(83, 102, 255, 0.7)'
                ]
            }]
        };

        const categoryChart = new Chart(
            document.getElementById('category-chart'),
            {
                type: 'pie',
                data: categoryData,
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right',
                        }
                    }
                },
            }
        );
    </script>
</body>
</html>"""
        
        return html
