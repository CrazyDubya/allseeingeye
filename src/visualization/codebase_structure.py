#!/usr/bin/env python3
"""
Codebase structure visualization for AllSeeingEye.

This module creates treemap visualizations of codebase structure,
providing insight into code organization and proportions.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import math
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

class CodebaseTreemap:
    """
    Creates treemap visualizations of codebase structure.
    
    This class analyzes the structure of a codebase and generates
    interactive treemap visualizations showing file sizes, types,
    and directory organization.
    """
    
# Add the CodebaseStructure wrapper class for backward compatibility
class CodebaseStructure:
    """
    Wrapper for codebase structure visualization.
    Maintains compatibility with original API.
    """
    
    def __init__(self, base_directory, excluded_dirs=None, excluded_files=None, **kwargs):
        """Initialize with the treemap visualization."""
        self.treemap = CodebaseTreemap(
            base_directory=base_directory,
            excluded_dirs=excluded_dirs,
            excluded_files=excluded_files,
            **kwargs
        )
        
    def generate(self):
        """Generate structure visualization using treemap."""
        # Build real treemap data from the codebase
        treemap_data = self._build_real_treemap_data()
        
        # Format the data as JSON string directly to avoid f-string issues
        data_json = json.dumps(treemap_data)
        base_dir = self.base_directory
        
        # Generate HTML as a normal string, not an f-string for the JavaScript part
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Codebase Structure</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                #treemap {{ width: 100%; height: 600px; }}
                rect {{ stroke: #fff; }}
                .label {{ font-size: 12px; fill: white; pointer-events: none; }}
                .parent {{ fill: none; stroke: #ccc; }}
                h1 {{ color: #333; }}
                .info {{ background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>Codebase Structure Treemap</h1>
            <div class="info">
                <p>This treemap shows the structure of your codebase. Files are colored by type and sized by file size or line count.</p>
                <p>Analyzed: <strong>{base_dir}</strong></p>
            </div>
            <div id="treemap"></div>
            <div id="legend" style="margin-top: 20px;"></div>
            
            <script>
                // Real data representing file structure
                const data = {data_json};

                // Set up the dimensions and margins
                const width = document.getElementById('treemap').clientWidth;
                const height = 600;
                
                // Create the color scale
                const colorScale = d3.scaleOrdinal()
                    .domain(["code", "documentation", "configuration", "data", "other"])
                    .range(["#6a5acd", "#2ecc71", "#9b59b6", "#f1c40f", "#95a5a6"]);
                
                // Create the treemap layout
                const treemap = d3.treemap()
                    .size([width, height])
                    .paddingTop(28)
                    .paddingRight(5)
                    .paddingBottom(5)
                    .paddingLeft(5)
                    .round(true);
                
                // Create the hierarchy from the data
                const root = d3.hierarchy(data)
                    .sum(function(d) { return d.value; })
                    .sort(function(a, b) { return b.value - a.value; });
                
                // Compute the treemap layout
                treemap(root);
                
                // Create the SVG container
                const svg = d3.select("#treemap")
                    .append("svg")
                    .attr("width", width)
                    .attr("height", height);
                
                // Add the cells
                const cell = svg.selectAll("g")
                    .data(root.descendants())
                    .enter()
                    .append("g")
                    .attr("transform", function(d) { 
                        return "translate(" + d.x0 + "," + d.y0 + ")"; 
                    });
                
                // Add the rectangles
                cell.append("rect")
                    .attr("width", function(d) { return d.x1 - d.x0; })
                    .attr("height", function(d) { return d.y1 - d.y0; })
                    .attr("fill", function(d) { 
                        return d.children ? "none" : colorScale(d.data.type || "other"); 
                    })
                    .attr("stroke", function(d) { 
                        return d.children ? "#ccc" : "white"; 
                    });
                
                // Add the labels
                cell.append("text")
                    .attr("class", "label")
                    .attr("x", 5)
                    .attr("y", 20)
                    .text(function(d) { return d.data.name; })
                    .style("font-size", function(d) {
                        const width = d.x1 - d.x0;
                        const height = d.y1 - d.y0;
                        return Math.min(width, height) > 50 ? "12px" : "8px";
                    })
                    .style("fill", function(d) {
                        if (d.children) return "#333";
                        const brightness = d3.hsl(colorScale(d.data.type || "other")).l;
                        return brightness > 0.5 ? "#333" : "#fff";
                    })
                    .attr("dy", ".35em")
                    .each(function(d) {
                        const width = d.x1 - d.x0;
                        if (width < 40) d3.select(this).style("display", "none");
                    });
                
                // Create the legend
                const legend = d3.select("#legend")
                    .append("svg")
                    .attr("width", width)
                    .attr("height", 50);
                
                const legendItems = ["code", "documentation", "configuration", "data", "other"];
                const legendWidth = 120;
                
                legendItems.forEach(function(item, i) {
                    const g = legend.append("g")
                        .attr("transform", "translate(" + (i * legendWidth + 10) + ", 10)");
                    
                    g.append("rect")
                        .attr("width", 15)
                        .attr("height", 15)
                        .attr("fill", colorScale(item));
                    
                    g.append("text")
                        .attr("x", 20)
                        .attr("y", 12)
                        .text(item.charAt(0).toUpperCase() + item.slice(1));
                });
            </script>
        </body>
        </html>
        """
        return html
    
    def _build_real_treemap_data(self) -> Dict[str, Any]:
        """Build real hierarchical data from the file system."""
        root_name = os.path.basename(self.base_directory)
        root = {
            "name": root_name,
            "children": []
        }
        
        # Helper to get the file type
        def get_file_type(ext):
            ext = ext.lower()
            if ext in ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.go', '.rb', '.php', '.jsx', '.tsx']:
                return 'code'
            elif ext in ['.md', '.txt', '.rst', '.pdf', '.docx']:
                return 'documentation'
            elif ext in ['.json', '.yml', '.yaml', '.xml', '.ini', '.cfg', '.conf', '.env']:
                return 'configuration'
            elif ext in ['.csv', '.tsv', '.xlsx', '.db', '.sql']:
                return 'data'
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico']:
                return 'media'
            else:
                return 'other'
        
        # Track directories we've already added
        dir_nodes = {}
        
        # Walk through the directory and build the tree
        for root_path, dirs, files in os.walk(self.base_directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            # Skip the root directory name
            rel_path = os.path.relpath(root_path, self.base_directory)
            if rel_path == '.':
                current_node = root
            else:
                # Get or create path to this directory
                path_parts = rel_path.split(os.sep)
                parent_path = ''
                current_node = root
                
                for part in path_parts:
                    if not parent_path:
                        parent_path = part
                    else:
                        parent_path = os.path.join(parent_path, part)
                    
                    if parent_path in dir_nodes:
                        current_node = dir_nodes[parent_path]
                    else:
                        # Create the directory node
                        new_node = {
                            "name": part,
                            "children": []
                        }
                        current_node["children"].append(new_node)
                        current_node = new_node
                        dir_nodes[parent_path] = new_node
            
            # Add files in this directory
            for file in files:
                # Skip excluded files
                if file in self.excluded_files:
                    continue
                
                file_path = os.path.join(root_path, file)
                try:
                    # Get file size and type
                    file_size = os.path.getsize(file_path)
                    _, ext = os.path.splitext(file)
                    file_type = get_file_type(ext)
                    
                    # Add the file node with its size as value
                    file_node = {
                        "name": file,
                        "value": file_size,
                        "type": file_type
                    }
                    current_node["children"].append(file_node)
                except:
                    # Skip files we can't access
                    pass
        
        # Clean up empty directories
        def clean_empty_dirs(node):
            if "children" in node:
                node["children"] = [child for child in node["children"] if "value" in child or "children" in child]
                for child in node["children"]:
                    if "children" in child:
                        clean_empty_dirs(child)
        
        clean_empty_dirs(root)
        
        # If we have no data, provide a sample structure
        if not root["children"]:
            root["children"] = [
                {"name": "No files found", "value": 100, "type": "other"}
            ]
        
        return root
        
    def build_treemap_data(self) -> Dict[str, Any]:
        """
        Build hierarchical data for treemap visualization.
        
        Returns:
            Dict[str, Any]: Hierarchical data structure for treemap
        """
        # Try to load from cache first
        if self.cache_file and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    self.treemap_data = json.load(f)
                    logger.info(f"Loaded treemap data from cache: {self.cache_file}")
                    return self.treemap_data
            except Exception as e:
                logger.warning(f"Failed to load from cache: {e}")
        
        # Start with root node
        base_name = os.path.basename(self.base_directory)
        self.treemap_data = {
            'name': base_name,
            'path': '',
            'children': [],
            'value': 0,
            'type': 'directory'
        }
        
        # Build the tree recursively
        self._build_tree_recursive(self.base_directory, self.treemap_data, '')
        
        # Save to cache if enabled
        if self.cache_file:
            try:
                os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
                with open(self.cache_file, 'w') as f:
                    json.dump(self.treemap_data, f)
                logger.info(f"Saved treemap data to cache: {self.cache_file}")
            except Exception as e:
                logger.warning(f"Failed to save to cache: {e}")
        
        return self.treemap_data
    
    def _build_tree_recursive(self, directory: str, node: Dict[str, Any], rel_path: str) -> int:
        """
        Recursively build the tree structure.
        
        Args:
            directory: Directory to process
            node: Current node in the tree
            rel_path: Relative path from base directory
            
        Returns:
            int: Total size/lines in this directory
        """
        total_metric = 0
        
        try:
            # List all entries in the directory
            entries = os.listdir(directory)
            
            # Process directories first
            dirs = [e for e in entries if os.path.isdir(os.path.join(directory, e))]
            for dir_name in sorted(dirs):
                dir_path = os.path.join(directory, dir_name)
                dir_rel_path = os.path.join(rel_path, dir_name)
                
                # Skip excluded directories
                if dir_name in self.excluded_dirs or dir_rel_path in self.excluded_dirs:
                    continue
                
                # Create child node for this directory
                child_node = {
                    'name': dir_name,
                    'path': dir_rel_path,
                    'children': [],
                    'value': 0,
                    'type': 'directory'
                }
                
                # Process this directory recursively
                dir_metric = self._build_tree_recursive(dir_path, child_node, dir_rel_path)
                
                # Only add non-empty directories
                if dir_metric > 0:
                    child_node['value'] = dir_metric
                    node['children'].append(child_node)
                    total_metric += dir_metric
            
            # Then process files
            files = [e for e in entries if os.path.isfile(os.path.join(directory, e))]
            for file_name in sorted(files):
                file_path = os.path.join(directory, file_name)
                file_rel_path = os.path.join(rel_path, file_name)
                
                # Skip excluded files
                if file_name in self.excluded_files or file_rel_path in self.excluded_files:
                    continue
                
                # Get file category and metric value
                category, metric_value = self._get_file_info(file_path)
                
                # Skip files with no metric value
                if metric_value <= 0:
                    continue
                
                # Create child node for this file
                child_node = {
                    'name': file_name,
                    'path': file_rel_path,
                    'value': metric_value,
                    'type': 'file',
                    'category': category
                }
                
                node['children'].append(child_node)
                total_metric += metric_value
        
        except Exception as e:
            logger.error(f"Error processing directory {directory}: {e}")
        
        return total_metric
    
    def _get_file_info(self, file_path: str) -> Tuple[str, int]:
        """
        Get file category and metric value.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple[str, int]: (category, metric_value)
        """
        try:
            # Check file size first
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return 'large', 0
            
            # Get file extension for category
            _, ext = os.path.splitext(file_path)
            category = self._get_category(ext)
            
            # Determine metric value based on configuration
            if self.metric == 'size':
                metric_value = file_size
            elif self.metric == 'lines':
                # Count lines for certain file types
                if category in ['code', 'data', 'documentation', 'configuration']:
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            line_count = sum(1 for _ in f)
                        metric_value = line_count
                    except Exception:
                        # Fall back to file size for binary files
                        metric_value = file_size
                else:
                    # Use file size for binary files
                    metric_value = file_size
            else:
                # Default to file size
                metric_value = file_size
            
            return category, metric_value
        
        except Exception as e:
            logger.debug(f"Error getting file info for {file_path}: {e}")
            return 'unknown', 0
    
    def _get_category(self, extension: str) -> str:
        """
        Determine file category based on extension.
        
        Args:
            extension: File extension
            
        Returns:
            str: Category name
        """
        extension = extension.lower()
        
        # Code files
        if extension in ['.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.go', '.rs', '.rb', '.php',
                        '.swift', '.kt', '.scala', '.html', '.css', '.jsx', '.tsx', '.vue', '.sql']:
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
    
    def generate_html(self, output_file: str, title: str = "Codebase Structure Treemap") -> str:
        """
        Generate an interactive HTML treemap visualization.
        
        Args:
            output_file: Path to save the HTML output
            title: Title for the visualization
            
        Returns:
            str: Path to the generated HTML file
        """
        # Ensure treemap data is built
        if not self.treemap_data:
            self.build_treemap_data()
        
        # Define colors for different file categories
        colors = {
            'code': '#3572A5',
            'data': '#F1C40F',
            'documentation': '#2ECC71',
            'configuration': '#9B59B6',
            'media': '#E74C3C',
            'archive': '#95A5A6',
            'binary': '#34495E',
            'other': '#95A5A6',
            'large': '#CCCCCC',
            'unknown': '#CCCCCC'
        }
        
        # Generate HTML with embedded D3.js
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        #container {{
            max-width: 100%;
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        #header {{
            padding: 20px;
            background-color: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}
        h1 {{
            margin: 0;
            color: #333;
            font-size: 24px;
        }}
        #chart {{
            width: 100%;
            height: 800px;
        }}
        #tooltip {{
            position: absolute;
            padding: 10px;
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            border-radius: 4px;
            font-size: 14px;
            pointer-events: none;
            opacity: 0;
            z-index: 1000;
        }}
        #legend {{
            padding: 20px;
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin-right: 15px;
        }}
        .legend-color {{
            width: 15px;
            height: 15px;
            margin-right: 5px;
            border-radius: 3px;
        }}
        .controls {{
            padding: 10px 20px;
            background-color: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            align-items: center;
        }}
        select, button {{
            margin-right: 10px;
            padding: 5px 10px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            background-color: white;
            font-size: 14px;
        }}
        button {{
            cursor: pointer;
            background-color: #007bff;
            color: white;
            border: none;
        }}
        button:hover {{
            background-color: #0069d9;
        }}
        .breadcrumb {{
            padding: 10px 20px;
            background-color: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            font-size: 14px;
        }}
        .breadcrumb span {{
            cursor: pointer;
            color: #007bff;
        }}
        .breadcrumb span:hover {{
            text-decoration: underline;
        }}
        .node {{
            stroke: #fff;
        }}
        .node:hover {{
            stroke: #000;
            stroke-width: 2px;
        }}
        .metric-value {{
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div id="container">
        <div id="header">
            <h1>{title}</h1>
        </div>
        <div class="controls">
            <label for="metric-select">Metric:</label>
            <select id="metric-select">
                <option value="size" {'selected' if self.metric == 'size' else ''}>File Size</option>
                <option value="lines" {'selected' if self.metric == 'lines' else ''}>Line Count</option>
            </select>
            <label for="color-select">Color By:</label>
            <select id="color-select">
                <option value="category">File Type</option>
                <option value="depth">Directory Depth</option>
            </select>
            <button id="reset-button">Reset View</button>
        </div>
        <div class="breadcrumb" id="breadcrumb">
            Home
        </div>
        <div id="tooltip"></div>
        <div id="chart"></div>
        <div id="legend"></div>
    </div>

    <script>
    // Initial data
    const initialData = {JSON.dumps(self.treemap_data)};
    let currentData = initialData;
    let breadcrumbHistory = [];
    let colorBy = "category";
    
    // Color scales
    const categoryColors = {{
        'code': '{colors["code"]}',
        'data': '{colors["data"]}',
        'documentation': '{colors["documentation"]}',
        'configuration': '{colors["configuration"]}',
        'media': '{colors["media"]}',
        'archive': '{colors["archive"]}',
        'binary': '{colors["binary"]}',
        'other': '{colors["other"]}',
        'large': '{colors["large"]}',
        'unknown': '{colors["unknown"]}',
        'directory': '#7FB3D5'
    }};
    
    const depthColors = d3.scaleOrdinal()
        .range(["#8dd3c7","#ffffb3","#bebada","#fb8072","#80b1d3","#fdb462","#b3de69","#fccde5","#d9d9d9","#bc80bd"]);
    
    // Format size in human-readable format
    function formatSize(bytes) {{
        const units = ['B', 'KB', 'MB', 'GB'];
        let size = bytes;
        let unitIndex = 0;
        while (size >= 1024 && unitIndex < units.length - 1) {{
            size /= 1024;
            unitIndex++;
        }}
        return size.toFixed(1) + ' ' + units[unitIndex];
    }}
    
    // Create treemap layout
    const width = document.getElementById('chart').clientWidth;
    const height = document.getElementById('chart').clientHeight;
    
    function renderTreemap(data) {{
        // Clear existing chart
        d3.select("#chart").html("");
        
        const tooltip = d3.select("#tooltip");
        
        // Create hierarchy
        const root = d3.hierarchy(data)
            .sum(d => d.value)
            .sort((a, b) => b.value - a.value);
        
        // Create treemap layout
        const treemap = d3.treemap()
            .size([width, height])
            .padding(2)
            .round(true);
        
        treemap(root);
        
        // Create SVG
        const svg = d3.select("#chart")
            .append("svg")
            .attr("width", width)
            .attr("height", height)
            .style("font", "10px sans-serif");
        
        // Create cells
        const cell = svg.selectAll("g")
            .data(root.leaves())
            .join("g")
            .attr("transform", d => `translate(${{d.x0}},${{d.y0}})`);
        
        // Cell rectangles
        cell.append("rect")
            .attr("class", "node")
            .attr("width", d => d.x1 - d.x0)
            .attr("height", d => d.y1 - d.y0)
            .attr("fill", d => {{
                if (colorBy === "category") {{
                    return categoryColors[d.data.category || d.data.type] || categoryColors.other;
                }} else {{
                    return depthColors(d.depth);
                }}
            }})
            .on("mouseover", (event, d) => {{
                tooltip.style("opacity", 0.9);
                
                const isMetricSize = document.getElementById('metric-select').value === 'size';
                const metricValue = isMetricSize ? formatSize(d.data.value) : d.data.value.toLocaleString() + ' lines';
                
                tooltip.html(`
                    <strong>${{d.data.name}}</strong><br/>
                    Path: ${{d.data.path || 'Root'}}<br/>
                    Type: ${{d.data.category || d.data.type}}<br/>
                    ${{isMetricSize ? 'Size' : 'Lines'}}: <span class="metric-value">${{metricValue}}</span>
                `)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 28) + "px");
            }})
            .on("mouseout", () => {{
                tooltip.style("opacity", 0);
            }})
            .on("click", (event, d) => {{
                if (d.data.type === 'directory' && d.data.children && d.data.children.length > 0) {{
                    // Navigate into the directory
                    breadcrumbHistory.push(currentData);
                    currentData = d.data;
                    updateBreadcrumb();
                    renderTreemap(currentData);
                }}
            }});
        
        // Add text labels (for larger cells only)
        cell.append("text")
            .style("user-select", "none")
            .attr("x", 4)
            .attr("y", 15)
            .text(d => {{
                // Only show text if there's enough space
                const cellWidth = d.x1 - d.x0;
                const cellHeight = d.y1 - d.y0;
                return (cellWidth > 50 && cellHeight > 20) ? d.data.name : "";
            }})
            .attr("fill", "white")
            .style("font-weight", "bold")
            .style("text-shadow", "1px 1px 1px rgba(0,0,0,0.5)");
        
        // Create legend
        updateLegend();
    }}
    
    function updateLegend() {{
        const legend = d3.select("#legend").html("");
        
        if (colorBy === "category") {{
            // Category legend
            const categories = Object.keys(categoryColors);
            categories.forEach(category => {{
                const item = legend.append("div")
                    .attr("class", "legend-item");
                
                item.append("div")
                    .attr("class", "legend-color")
                    .style("background-color", categoryColors[category]);
                
                item.append("div")
                    .text(category.charAt(0).toUpperCase() + category.slice(1));
            }});
        }} else {{
            // Depth legend
            const depths = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
            depths.forEach(depth => {{
                const item = legend.append("div")
                    .attr("class", "legend-item");
                
                item.append("div")
                    .attr("class", "legend-color")
                    .style("background-color", depthColors(depth));
                
                item.append("div")
                    .text(`Level ${{depth}}`);
            }});
        }}
    }}
    
    function updateBreadcrumb() {{
        const breadcrumb = d3.select("#breadcrumb");
        breadcrumb.html("");
        
        // Add home
        breadcrumb.append("span")
            .text("Home")
            .on("click", () => {{
                currentData = initialData;
                breadcrumbHistory = [];
                updateBreadcrumb();
                renderTreemap(currentData);
            }});
        
        // Add each level
        breadcrumbHistory.forEach((data, index) => {{
            breadcrumb.append("span").text(" > ");
            breadcrumb.append("span")
                .text(data.name)
                .on("click", () => {{
                    // Navigate to this level
                    currentData = data;
                    breadcrumbHistory = breadcrumbHistory.slice(0, index);
                    updateBreadcrumb();
                    renderTreemap(currentData);
                }});
        }});
        
        // Add current level if not home
        if (currentData !== initialData) {{
            breadcrumb.append("span").text(" > ");
            breadcrumb.append("span")
                .text(currentData.name)
                .style("font-weight", "bold")
                .style("color", "black")
                .style("cursor", "default");
        }}
    }}
    
    // Event listeners
    document.getElementById('color-select').addEventListener('change', function() {{
        colorBy = this.value;
        renderTreemap(currentData);
    }});
    
    document.getElementById('metric-select').addEventListener('change', function() {{
        // In a real implementation, we would re-fetch data based on the new metric
        // For now, just show an alert
        alert("Changing metrics requires re-analyzing the codebase with the new metric.");
    }});
    
    document.getElementById('reset-button').addEventListener('click', function() {{
        currentData = initialData;
        breadcrumbHistory = [];
        updateBreadcrumb();
        renderTreemap(currentData);
    }});
    
    // Initial render
    renderTreemap(currentData);
    updateBreadcrumb();
    </script>
</body>
</html>
"""
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Treemap visualization saved to {output_file}")
        return output_file
    
    def export_json(self, output_file: str) -> str:
        """
        Export the treemap data as JSON for custom visualization.
        
        Args:
            output_file: Path to save the JSON output
            
        Returns:
            str: Path to the generated JSON file
        """
        # Ensure treemap data is built
        if not self.treemap_data:
            self.build_treemap_data()
        
        with open(output_file, 'w') as f:
            json.dump(self.treemap_data, f, indent=2)
        
        logger.info(f"Treemap data exported to {output_file}")
        return output_file
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the codebase structure.
        
        Returns:
            Dict[str, Any]: Dictionary of structure statistics
        """
        # Ensure treemap data is built
        if not self.treemap_data:
            self.build_treemap_data()
        
        # Initialize statistics
        stats = {
            'total_size': 0,
            'total_files': 0,
            'categories': defaultdict(lambda: {'count': 0, 'size': 0}),
            'max_file_size': 0,
            'max_directory_size': 0,
            'largest_file': '',
            'largest_directory': '',
            'deepest_level': 0,
            'avg_files_per_directory': 0,
            'directory_count': 0
        }
        
        # Helper function to traverse the tree
        def traverse(node, level=0):
            nonlocal stats
            
            if level > stats['deepest_level']:
                stats['deepest_level'] = level
            
            if node['type'] == 'directory':
                stats['directory_count'] += 1
                
                # Check if this is the largest directory
                if node['value'] > stats['max_directory_size']:
                    stats['max_directory_size'] = node['value']
                    stats['largest_directory'] = node['path'] or 'Root'
                
                # Recursively process children
                for child in node.get('children', []):
                    traverse(child, level + 1)
            else:
                # This is a file
                stats['total_files'] += 1
                stats['total_size'] += node['value']
                
                # Update category statistics
                category = node.get('category', 'unknown')
                stats['categories'][category]['count'] += 1
                stats['categories'][category]['size'] += node['value']
                
                # Check if this is the largest file
                if node['value'] > stats['max_file_size']:
                    stats['max_file_size'] = node['value']
                    stats['largest_file'] = node['path']
        
        # Start traversal
        traverse(self.treemap_data)
        
        # Calculate average files per directory
        if stats['directory_count'] > 0:
            stats['avg_files_per_directory'] = stats['total_files'] / stats['directory_count']
        
        # Convert defaultdict to regular dict for serialization
        stats['categories'] = dict(stats['categories'])
        
        # Format size values
        for category in stats['categories']:
            stats['categories'][category]['size_formatted'] = self._format_size(stats['categories'][category]['size'])
        
        stats['total_size_formatted'] = self._format_size(stats['total_size'])
        stats['max_file_size_formatted'] = self._format_size(stats['max_file_size'])
        stats['max_directory_size_formatted'] = self._format_size(stats['max_directory_size'])
        
        return stats
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024 or unit == 'TB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
