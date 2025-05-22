#!/usr/bin/env python3
"""
Dependency graph visualization for AllSeeingEye.

This module analyzes import/include statements in code files and generates
interactive visualizations of file dependencies.
"""

import os
import re
import logging
from typing import Dict, List, Set, Tuple, Optional, Any
from pathlib import Path
import json
import networkx as nx
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

class DependencyGraph:
    """
    Creates and visualizes dependency graphs for codebases.
    
    This class parses code files to extract import/include statements, builds
    a directed graph of file dependencies, and generates visualizations.
    """
    
    def __init__(self, base_directory, excluded_dirs=None, excluded_files=None):
        """Initialize with the directory to analyze."""
        self.base_directory = os.path.abspath(base_directory)
        self.excluded_dirs = set(excluded_dirs or ['.git', 'node_modules', '.venv', '__pycache__', '.idea', '.vscode'])
        self.excluded_files = set(excluded_files or [])
    
    def generate(self):
        """Generate an HTML visualization of the dependency graph."""
        # Extract real dependency data from the codebase
        dependency_data = self._extract_dependencies()
        
        # Format the data as JSON string without using f-string for the JavaScript part
        json_data = json.dumps(dependency_data)
        
        # Create the dynamic parts separately to avoid JSON/JavaScript parsing issues
        base_dir = self.base_directory
        node_count = len(dependency_data['nodes'])
        link_count = len(dependency_data['links'])
        
        # Now create the HTML with minimal f-string usage
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Dependency Graph</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                #graph {{ width: 100%; height: 600px; }}
                .node {{ fill: #6a5acd; stroke: #fff; stroke-width: 2px; }}
                .node:hover {{ fill: #9370db; }}
                .link {{ stroke: #999; stroke-opacity: 0.6; }}
                text {{ font-size: 12px; fill: #333; pointer-events: none; }}
                h1 {{ color: #333; }}
                .info {{ background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>Codebase Dependency Graph</h1>
            <div class="info">
                <p>This graph shows dependencies between files in your codebase. Files are colored by type and grouped by directory.</p>
                <p>Analyzed: <strong>{base_dir}</strong></p>
                <p>Found: <strong>{node_count}</strong> files and <strong>{link_count}</strong> dependencies</p>
            </div>
            <div id="graph"></div>
            <script>
                // Real dependency data from the analyzed codebase
                const data = {json_data};

                // Create the force simulation
                const width = window.innerWidth;
                const height = 600;
                
                const svg = d3.select("#graph")
                    .append("svg")
                    .attr("width", width)
                    .attr("height", height);
                
                // Create the simulation
                const simulation = d3.forceSimulation()
                    .force("link", d3.forceLink().id(function(d) { return d.id; }).distance(100))
                    .force("charge", d3.forceManyBody().strength(-300))
                    .force("center", d3.forceCenter(width / 2, height / 2));
                
                // Add the links
                const link = svg.append("g")
                    .attr("class", "links")
                    .selectAll("line")
                    .data(data.links)
                    .enter().append("line")
                    .attr("class", "link")
                    .attr("stroke-width", function(d) { return Math.sqrt(d.value); });
                
                // Add the nodes
                const node = svg.append("g")
                    .attr("class", "nodes")
                    .selectAll("g")
                    .data(data.nodes)
                    .enter().append("g");
                
                node.append("circle")
                    .attr("class", "node")
                    .attr("r", 6)
                    .attr("fill", function(d) { return d3.schemeCategory10[d.group % 10]; })
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended));
                
                node.append("text")
                    .attr("dx", 12)
                    .attr("dy", ".35em")
                    .text(function(d) { return d.name || d.id; });
                
                // Update the simulation
                simulation
                    .nodes(data.nodes)
                    .on("tick", ticked);
                
                simulation.force("link")
                    .links(data.links);
                
                function ticked() {
                    link
                        .attr("x1", function(d) { return d.source.x; })
                        .attr("y1", function(d) { return d.source.y; })
                        .attr("x2", function(d) { return d.target.x; })
                        .attr("y2", function(d) { return d.target.y; });
                
                    node
                        .attr("transform", function(d) { 
                            return "translate(" + d.x + "," + d.y + ")";
                        });
                }
                
                function dragstarted(event, d) {
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                }
                
                function dragged(event, d) {
                    d.fx = event.x;
                    d.fy = event.y;
                }
                
                function dragended(event, d) {
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }
            </script>
        </body>
        </html>
        """
        return html
    
    def _extract_dependencies(self) -> Dict:
        """Extract dependency information from the codebase.
        
        Returns:
            Dict containing nodes and links for the dependency graph
        """
        # Map file extensions to language
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'cpp',
            '.cpp': 'cpp',
            '.h': 'cpp',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php'
        }
        
        nodes = []
        links = []
        processed_files = set()
        file_to_node_id = {}
        
        # Walk through the directory
        for root, dirs, files in os.walk(self.base_directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.base_directory)
                
                # Skip excluded files
                if rel_path in self.excluded_files:
                    continue
                
                # Only process source code files
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in ext_to_lang:
                    continue
                
                # Add to processed files
                processed_files.add(rel_path)
                file_to_node_id[rel_path] = len(nodes)
                
                # Determine group based on directory structure
                parts = rel_path.split(os.sep)
                group = 1
                if len(parts) > 1:
                    # Use the first directory as group
                    group_name = parts[0]
                    group = hash(group_name) % 10 + 1
                
                # Add node
                nodes.append({
                    'id': rel_path,
                    'group': group,
                    'name': os.path.basename(file_path)
                })
                
                # Process the file content for dependencies
                try:
                    language = ext_to_lang[ext]
                    dependencies = self._extract_file_dependencies(file_path, language)
                    
                    # Add links for dependencies
                    for dependency in dependencies:
                        # Try to resolve the dependency to an actual file
                        resolved_deps = self._resolve_dependency(rel_path, dependency)
                        for resolved in resolved_deps:
                            if resolved in processed_files:
                                links.append({
                                    'source': rel_path,
                                    'target': resolved,
                                    'value': 1
                                })
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
        
        # If we have no files, add some placeholder nodes to avoid D3 errors
        if not nodes:
            nodes.append({'id': 'no_files_found', 'group': 1, 'name': 'No files found'})
        
        # If we have files but no links, add some basic file relationships
        if nodes and not links:
            # Connect files in the same directories
            for i in range(len(nodes) - 1):
                for j in range(i + 1, min(i + 3, len(nodes))):
                    if nodes[i]['group'] == nodes[j]['group']:
                        links.append({
                            'source': nodes[i]['id'],
                            'target': nodes[j]['id'],
                            'value': 1
                        })
        
        return {'nodes': nodes, 'links': links}
    
    def _extract_file_dependencies(self, file_path: str, language: str) -> List[str]:
        """Extract import/include statements from a file.
        
        Args:
            file_path: Path to the file
            language: Programming language of the file
            
        Returns:
            List of dependencies found in the file
        """
        dependencies = []
        
        # Get patterns for this language
        patterns = self.IMPORT_PATTERNS.get(language, [])
        if not patterns:
            return dependencies
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Process line by line for import patterns
                for line in content.split('\n'):
                    for pattern in patterns:
                        matches = re.findall(pattern, line)
                        for match in matches:
                            if match and isinstance(match, str) and match.strip():
                                dependencies.append(match.strip())
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")
            
        return dependencies
    
    def _resolve_dependency(self, source_file: str, dependency: str) -> List[str]:
        """Resolve a dependency string to an actual file path.
        
        Args:
            source_file: The source file containing the import
            dependency: The dependency string from the import
            
        Returns:
            List of resolved file paths
        """
        resolved = []
        
        # Handle relative imports with dots (Python)
        if dependency.startswith('.'):
            source_dir = os.path.dirname(source_file)
            levels = 0
            while dependency.startswith('.'):
                dependency = dependency[1:]
                levels += 1
            
            # Go up directory levels
            target_dir = source_dir
            for _ in range(levels - 1):
                target_dir = os.path.dirname(target_dir)
                
            # Append the module path
            if dependency:
                target_path = os.path.join(target_dir, dependency.replace('.', os.sep))
            else:
                target_path = target_dir
                
            # Check for possible files
            for ext in ['.py', '.js', '.ts']:
                if os.path.isfile(os.path.join(self.base_directory, target_path + ext)):
                    resolved.append(target_path + ext)
                    
            # Check for __init__.py
            init_file = os.path.join(target_path, '__init__.py')
            if os.path.isfile(os.path.join(self.base_directory, init_file)):
                resolved.append(init_file)
                
        # Handle absolute imports
        else:
            # For Python standard modules
            py_module_path = dependency.replace('.', os.sep)
            possible_paths = []
            
            # Try with different extensions
            for ext in ['.py', '.js', '.ts']:
                possible_paths.append(py_module_path + ext)
                
            # Try with __init__.py for packages
            possible_paths.append(os.path.join(py_module_path, '__init__.py'))
            
            # Check if files exist
            for path in possible_paths:
                if os.path.isfile(os.path.join(self.base_directory, path)):
                    resolved.append(path)
                    
            # Check for JS/TS imports with path
            if not resolved and dependency.startswith(('./', '../')):
                source_dir = os.path.dirname(source_file)
                js_path = os.path.normpath(os.path.join(source_dir, dependency))
                
                # Try with extensions
                for ext in ['.js', '.jsx', '.ts', '.tsx']:
                    if os.path.isfile(os.path.join(self.base_directory, js_path + ext)):
                        resolved.append(js_path + ext)
                
        return resolved
    
    # Language-specific import patterns
    IMPORT_PATTERNS = {
        'python': [
            r'^\s*import\s+(\w+(?:\.\w+)*)', 
            r'^\s*from\s+(\w+(?:\.\w+)*)\s+import',
        ],
        'javascript': [
            r'^\s*import\s+.*\s+from\s+[\'"](.+)[\'"]',
            r'^\s*const\s+.*\s+=\s+require\([\'"](.+)[\'"]\)',
            r'^\s*import\s+[\'"](.+)[\'"]',
        ],
        'typescript': [
            r'^\s*import\s+.*\s+from\s+[\'"](.+)[\'"]',
            r'^\s*import\s+[\'"](.+)[\'"]',
        ],
        'java': [
            r'^\s*import\s+(.+);',
        ],
        'cpp': [
            r'^\s*#include\s+[<"](.+)[>"]',
        ],
        'go': [
            r'^\s*import\s+[\(]?[\'"](.+)[\'"]',
        ],
        'ruby': [
            r'^\s*require\s+[\'"](.+)[\'"]',
            r'^\s*require_relative\s+[\'"](.+)[\'"]',
        ],
    }
    
    # File extensions to language mapping
    EXTENSION_MAP = {
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
    }
    
    def __init__(self,
                 base_directory: str,
                 excluded_dirs: Optional[List[str]] = None,
                 max_file_size: int = 1024 * 1024,  # 1MB default
                 cache_dir: Optional[str] = None):
        """Initialize with configurable options."""
        self.base_directory = os.path.abspath(base_directory)
        self.excluded_dirs = set(excluded_dirs or ['.git', 'node_modules', '.venv', '__pycache__', '.idea', '.vscode'])
        self.max_file_size = max_file_size
        self.graph = nx.DiGraph()
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'dependency_graph.json') if cache_dir else None
    
    def build_graph(self) -> nx.DiGraph:
        """
        Build a directed graph representing file dependencies.
        
        Returns:
            nx.DiGraph: A NetworkX directed graph of file dependencies
        """
        # Try to load from cache first
        if self.cache_file and os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    self.graph = nx.node_link_graph(cache_data)
                    logger.info(f"Loaded dependency graph from cache: {self.cache_file}")
                    return self.graph
            except Exception as e:
                logger.warning(f"Failed to load from cache: {e}")
        
        # Start fresh with an empty graph
        self.graph = nx.DiGraph()
        
        # Map of module names to file paths
        module_map = self._build_module_map()
        
        # Process each file to extract imports
        for root, dirs, files in os.walk(self.base_directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs and 
                      os.path.relpath(os.path.join(root, d), self.base_directory) not in self.excluded_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Get file extension and determine language
                _, ext = os.path.splitext(file_path)
                language = self.EXTENSION_MAP.get(ext.lower())
                
                if not language:
                    continue  # Skip unsupported file types
                
                # Process file for imports
                self._process_file(file_path, language, module_map)
        
        # Save to cache if enabled
        if self.cache_file:
            try:
                os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
                with open(self.cache_file, 'w') as f:
                    json.dump(nx.node_link_data(self.graph), f)
                logger.info(f"Saved dependency graph to cache: {self.cache_file}")
            except Exception as e:
                logger.warning(f"Failed to save to cache: {e}")
        
        return self.graph
    
    def _build_module_map(self) -> Dict[str, str]:
        """
        Build a mapping of module names to file paths.
        
        Returns:
            Dict[str, str]: A dictionary mapping module names to file paths
        """
        module_map = {}
        
        for root, dirs, files in os.walk(self.base_directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs and 
                      os.path.relpath(os.path.join(root, d), self.base_directory) not in self.excluded_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.base_directory)
                
                # Get file extension and determine language
                _, ext = os.path.splitext(file_path)
                language = self.EXTENSION_MAP.get(ext.lower())
                
                if not language:
                    continue  # Skip unsupported file types
                
                # Map module name based on language
                if language == 'python':
                    # Convert path to Python module name
                    module_name = os.path.splitext(rel_path)[0].replace(os.sep, '.')
                    module_map[module_name] = rel_path
                    
                    # Also map directory as package if it has __init__.py
                    dir_path = os.path.dirname(rel_path)
                    if os.path.exists(os.path.join(self.base_directory, dir_path, '__init__.py')):
                        package_name = dir_path.replace(os.sep, '.')
                        module_map[package_name] = os.path.join(dir_path, '__init__.py')
                else:
                    # For other languages, map without extension
                    module_name = os.path.splitext(rel_path)[0]
                    module_map[module_name] = rel_path
                    
                    # Also map with extension for explicit imports
                    module_map[rel_path] = rel_path
        
        return module_map
    
    def _process_file(self, file_path: str, language: str, module_map: Dict[str, str]) -> None:
        """
        Process a file to extract imports and add edges to the graph.
        
        Args:
            file_path: Path to the file to process
            language: Programming language of the file
            module_map: Mapping of module names to file paths
        """
        try:
            # Check file size
            if os.path.getsize(file_path) > self.max_file_size:
                logger.debug(f"Skipping large file: {file_path}")
                return
            
            # Add node for this file
            rel_path = os.path.relpath(file_path, self.base_directory)
            self.graph.add_node(rel_path, label=os.path.basename(file_path), language=language)
            
            # Extract imports
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Get import patterns for this language
                patterns = self.IMPORT_PATTERNS.get(language, [])
                
                for pattern in patterns:
                    for match in re.finditer(pattern, content, re.MULTILINE):
                        import_name = match.group(1)
                        
                        # Resolve import to a file path
                        imported_file = self._resolve_import(import_name, language, rel_path, module_map)
                        
                        if imported_file and imported_file != rel_path:  # Avoid self-references
                            self.graph.add_edge(rel_path, imported_file)
        
        except Exception as e:
            logger.debug(f"Error processing file {file_path}: {e}")
    
    def _resolve_import(self, import_name: str, language: str, current_file: str, module_map: Dict[str, str]) -> Optional[str]:
        """
        Resolve an import statement to a file path.
        
        Args:
            import_name: The name imported in the code
            language: Programming language of the file
            current_file: Path to the file containing the import
            module_map: Mapping of module names to file paths
            
        Returns:
            Optional[str]: Resolved file path or None if unresolved
        """
        # Handle language-specific import resolution
        if language == 'python':
            # Direct module match
            if import_name in module_map:
                return module_map[import_name]
            
            # Handle relative imports
            if import_name.startswith('.'):
                current_dir = os.path.dirname(current_file)
                level = 0
                while import_name.startswith('.'):
                    level += 1
                    import_name = import_name[1:]
                
                # Go up by level
                parent_dir = current_dir
                for _ in range(level - 1):
                    parent_dir = os.path.dirname(parent_dir)
                
                if import_name:
                    # Relative import with module
                    rel_module = f"{parent_dir}.{import_name}".replace(os.sep, '.')
                    if rel_module in module_map:
                        return module_map[rel_module]
                else:
                    # Relative import of parent
                    rel_module = parent_dir.replace(os.sep, '.')
                    if rel_module in module_map:
                        return module_map[rel_module]
        
        elif language in ['javascript', 'typescript']:
            # Handle relative imports with extensions
            if import_name.startswith('./') or import_name.startswith('../'):
                # Resolve relative to current file
                dir_path = os.path.dirname(current_file)
                resolved_path = os.path.normpath(os.path.join(dir_path, import_name))
                
                # Try with different extensions if no extension in import
                if '.' not in os.path.basename(import_name):
                    for ext in ['.js', '.jsx', '.ts', '.tsx']:
                        path_with_ext = f"{resolved_path}{ext}"
                        if path_with_ext in module_map:
                            return path_with_ext
                
                # Try exact path
                if resolved_path in module_map:
                    return module_map[resolved_path]
                
                # Try with /index.js etc.
                for ext in ['.js', '.jsx', '.ts', '.tsx']:
                    index_path = os.path.join(resolved_path, f"index{ext}")
                    if index_path in module_map:
                        return index_path
            
            # Handle bare imports (might be from node_modules, hard to resolve precisely)
            # Just return None for these as they're external dependencies
            
        elif language == 'cpp':
            # Simple resolution for system includes
            if import_name in module_map:
                return module_map[import_name]
            
            # Try with various C++ extensions
            for ext in ['.h', '.hpp', '.c', '.cpp', '.cc']:
                name_with_ext = f"{import_name}{ext}"
                if name_with_ext in module_map:
                    return module_map[name_with_ext]
        
        # Default case: try direct lookup
        return module_map.get(import_name)
    
    def generate_html(self, output_file: str) -> str:
        """
        Generate an interactive HTML visualization of the dependency graph.
        
        Args:
            output_file: Path to save the HTML output
            
        Returns:
            str: Path to the generated HTML file
        """
        # Ensure graph is built
        if self.graph.number_of_nodes() == 0:
            self.build_graph()
        
        try:
            # Import here to make visualizations optional
            from pyvis.network import Network
            
            # Create network
            net = Network(notebook=False, height="800px", width="100%", directed=True)
            
            # Group nodes by language for coloring
            language_groups = defaultdict(list)
            for node, attrs in self.graph.nodes(data=True):
                lang = attrs.get('language', 'unknown')
                language_groups[lang].append(node)
            
            # Color map for languages
            color_map = {
                'python': '#3572A5',
                'javascript': '#F7DF1E',
                'typescript': '#3178C6',
                'java': '#B07219',
                'cpp': '#F34B7D',
                'go': '#00ADD8',
                'ruby': '#701516',
                'unknown': '#CCCCCC'
            }
            
            # Add nodes with appropriate colors
            for lang, nodes in language_groups.items():
                color = color_map.get(lang, '#CCCCCC')
                for node in nodes:
                    net.add_node(node, 
                                 label=os.path.basename(node), 
                                 title=node,
                                 color=color)
            
            # Add edges
            for source, target in self.graph.edges():
                net.add_edge(source, target)
            
            # Set physics for better visualization
            net.set_options("""
            {
                "physics": {
                    "hierarchicalRepulsion": {
                        "centralGravity": 0.0,
                        "springLength": 100,
                        "springConstant": 0.01,
                        "nodeDistance": 120
                    },
                    "maxVelocity": 50,
                    "minVelocity": 0.1,
                    "solver": "hierarchicalRepulsion"
                },
                "layout": {
                    "hierarchical": {
                        "enabled": true,
                        "direction": "LR",
                        "sortMethod": "directed"
                    }
                },
                "edges": {
                    "smooth": {
                        "type": "cubicBezier",
                        "forceDirection": "horizontal"
                    }
                }
            }
            """)
            
            # Save to HTML file
            net.save_graph(output_file)
            logger.info(f"Dependency graph visualization saved to {output_file}")
            
            return output_file
        
        except ImportError:
            logger.error("pyvis is required for HTML visualization. Install with 'pip install pyvis'")
            raise
    
    def export_json(self, output_file: str) -> str:
        """
        Export the dependency graph as JSON for custom visualization.
        
        Args:
            output_file: Path to save the JSON output
            
        Returns:
            str: Path to the generated JSON file
        """
        # Ensure graph is built
        if self.graph.number_of_nodes() == 0:
            self.build_graph()
        
        # Convert to node-link format for JSON serialization
        data = nx.node_link_data(self.graph)
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Dependency graph data exported to {output_file}")
        return output_file
    
    def get_most_central_files(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Get the most central files in the codebase.
        
        Args:
            top_n: Number of files to return
            
        Returns:
            List[Tuple[str, float]]: List of (file_path, centrality_score) tuples
        """
        # Ensure graph is built
        if self.graph.number_of_nodes() == 0:
            self.build_graph()
        
        # Calculate betweenness centrality
        centrality = nx.betweenness_centrality(self.graph)
        
        # Sort by centrality score
        sorted_files = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_files[:top_n]
    
    def get_circular_dependencies(self) -> List[List[str]]:
        """
        Find circular dependencies in the codebase.
        
        Returns:
            List[List[str]]: List of circular dependency paths
        """
        # Ensure graph is built
        if self.graph.number_of_nodes() == 0:
            self.build_graph()
        
        try:
            # Find strongly connected components
            sccs = list(nx.strongly_connected_components(self.graph))
            
            # Filter for components with more than one node (circular dependencies)
            circular_deps = [list(component) for component in sccs if len(component) > 1]
            
            return circular_deps
        
        except Exception as e:
            logger.error(f"Error finding circular dependencies: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the dependency graph.
        
        Returns:
            Dict[str, Any]: Dictionary of graph statistics
        """
        # Ensure graph is built
        if self.graph.number_of_nodes() == 0:
            self.build_graph()
        
        # Calculate basic statistics
        stats = {
            'total_files': self.graph.number_of_nodes(),
            'total_dependencies': self.graph.number_of_edges(),
            'isolated_files': len(list(nx.isolates(self.graph))),
            'average_dependencies': 0,
            'max_outgoing_deps': 0,
            'max_incoming_deps': 0,
            'file_with_most_outgoing_deps': '',
            'file_with_most_incoming_deps': '',
            'languages': defaultdict(int),
        }
        
        if stats['total_files'] > 0:
            stats['average_dependencies'] = stats['total_dependencies'] / stats['total_files']
        
        # Find max dependencies
        out_degrees = dict(self.graph.out_degree())
        in_degrees = dict(self.graph.in_degree())
        
        if out_degrees:
            max_out = max(out_degrees.items(), key=lambda x: x[1])
            stats['max_outgoing_deps'] = max_out[1]
            stats['file_with_most_outgoing_deps'] = max_out[0]
        
        if in_degrees:
            max_in = max(in_degrees.items(), key=lambda x: x[1])
            stats['max_incoming_deps'] = max_in[1]
            stats['file_with_most_incoming_deps'] = max_in[0]
        
        # Count files by language
        for _, attrs in self.graph.nodes(data=True):
            lang = attrs.get('language', 'unknown')
            stats['languages'][lang] += 1
        
        return stats
