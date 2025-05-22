#!/usr/bin/env python3
"""
Visualization tab for AllSeeingEye GUI
"""

import os
import sys
import logging
import json
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QGroupBox, QCheckBox, QSpinBox, QFileDialog, QComboBox, QTextEdit,
    QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem, QProgressBar,
    QSplitter, QFrame, QTabWidget, QMessageBox, QScrollArea, QFormLayout,
    QRadioButton, QButtonGroup
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QUrl, QSize
from PyQt6.QtWebEngineWidgets import QWebEngineView

# Configure logging
logger = logging.getLogger(__name__)

# Try to import visualization modules
try:
    # Try from src structure
    from src.visualization.dependency_graph import DependencyGraph
    from src.visualization.codebase_structure import CodebaseTreemap
    from src.visualization.metrics_dashboard import MetricsDashboard
    
    HAS_VISUALIZATION = True
except ImportError:
    # Try from package structure (if visualization was moved to package)
    try:
        from allseeingeye.visualization import DependencyGraph, CodebaseTreemap, MetricsDashboard
        HAS_VISUALIZATION = True
    except ImportError:
        logger.warning("Visualization modules not found, some features will be disabled")
        HAS_VISUALIZATION = False

class VisualizationThread(QThread):
    """Thread for generating visualizations in the background"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, viz_type, directory, config):
        super().__init__()
        self.viz_type = viz_type  # dependency_graph, treemap, dashboard
        self.directory = directory
        self.config = config
    
    def run(self):
        """Run the visualization generation"""
        try:
            self.progress.emit(0, f"Starting {self.viz_type} visualization...")
            
            # Generate visualization based on type
            if self.viz_type == "dependency_graph":
                self._generate_dependency_graph()
            elif self.viz_type == "treemap":
                self._generate_treemap()
            elif self.viz_type == "dashboard":
                self._generate_dashboard()
            else:
                raise ValueError(f"Unknown visualization type: {self.viz_type}")
            
        except Exception as e:
            logger.error(f"Visualization error: {str(e)}")
            self.error.emit(f"Visualization failed: {str(e)}")
    
    def _generate_dependency_graph(self):
        """Generate dependency graph visualization"""
        self.progress.emit(10, "Initializing dependency graph...")
        
        # Configure dependency graph
        graph = DependencyGraph(
            base_directory=self.directory,
            excluded_dirs=self.config.get("excluded_dirs", []),
            max_file_size=self.config.get("max_file_size", 1024 * 1024),
            cache_dir=self.config.get("cache_dir")
        )
        
        self.progress.emit(20, "Building dependency graph...")
        
        # Build the graph
        graph.build_graph()
        
        self.progress.emit(70, "Generating HTML visualization...")
        
        # Generate HTML output
        output_file = os.path.join(os.path.dirname(self.directory), "dependency_graph.html")
        output_file = graph.generate_html(output_file)
        
        self.progress.emit(100, "Dependency graph visualization complete!")
        self.finished.emit(output_file)
    
    def _generate_treemap(self):
        """Generate treemap visualization"""
        self.progress.emit(10, "Initializing codebase treemap...")
        
        # Configure treemap
        treemap = CodebaseTreemap(
            base_directory=self.directory,
            metric=self.config.get("metric", "size"),  # size or lines
            excluded_dirs=self.config.get("excluded_dirs", []),
            max_file_size=self.config.get("max_file_size", 1024 * 1024),
            cache_dir=self.config.get("cache_dir")
        )
        
        self.progress.emit(20, "Building treemap data...")
        
        # Build the treemap data
        treemap.build_treemap_data()
        
        self.progress.emit(70, "Generating HTML visualization...")
        
        # Generate HTML output
        output_file = os.path.join(os.path.dirname(self.directory), "codebase_treemap.html")
        output_file = treemap.generate_html(output_file)
        
        self.progress.emit(100, "Treemap visualization complete!")
        self.finished.emit(output_file)
    
    def _generate_dashboard(self):
        """Generate metrics dashboard visualization"""
        self.progress.emit(10, "Initializing metrics dashboard...")
        
        # Configure dashboard
        dashboard = MetricsDashboard(
            base_directory=self.directory,
            excluded_dirs=self.config.get("excluded_dirs", []),
            max_file_size=self.config.get("max_file_size", 1024 * 1024),
            cache_dir=self.config.get("cache_dir")
        )
        
        self.progress.emit(20, "Calculating metrics...")
        
        # Calculate metrics
        dashboard.calculate_metrics()
        
        self.progress.emit(70, "Generating HTML dashboard...")
        
        # Generate HTML output
        output_file = os.path.join(os.path.dirname(self.directory), "metrics_dashboard.html")
        output_file = dashboard.generate_html(output_file)
        
        self.progress.emit(100, "Dashboard visualization complete!")
        self.finished.emit(output_file)

class VisualizationTab(QWidget):
    """Tab for generating and viewing code visualizations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.settings = QSettings("AllSeeingEye", "AllSeeingEye")
        self.directory = self.settings.value("last_project_directory", "")
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Split view between configuration and visualization
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)
        
        # Top section: Configuration
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)
        
        # Directory selection
        dir_group = QGroupBox("Project Directory")
        dir_layout = QHBoxLayout(dir_group)
        
        self.dir_edit = QLineEdit(self.directory)
        self.dir_edit.setReadOnly(True)
        dir_layout.addWidget(self.dir_edit)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.browse_btn)
        
        config_layout.addWidget(dir_group)
        
        # Visualization options (side by side)
        options_layout = QHBoxLayout()
        
        # Left side: Visualization Type
        type_group = QGroupBox("Visualization Type")
        type_layout = QVBoxLayout(type_group)
        
        self.type_buttons = QButtonGroup(self)
        
        self.dep_graph_radio = QRadioButton("Dependency Graph")
        self.dep_graph_radio.setChecked(True)
        self.dep_graph_radio.setToolTip("Visualize dependencies between files")
        self.type_buttons.addButton(self.dep_graph_radio)
        type_layout.addWidget(self.dep_graph_radio)
        
        self.treemap_radio = QRadioButton("Codebase Treemap")
        self.treemap_radio.setToolTip("Visualize structure and proportions using treemaps")
        self.type_buttons.addButton(self.treemap_radio)
        type_layout.addWidget(self.treemap_radio)
        
        self.dashboard_radio = QRadioButton("Metrics Dashboard")
        self.dashboard_radio.setToolTip("Show comprehensive metrics dashboard")
        self.type_buttons.addButton(self.dashboard_radio)
        type_layout.addWidget(self.dashboard_radio)
        
        options_layout.addWidget(type_group)
        
        # Right side: Visualization Options
        viz_options_group = QGroupBox("Options")
        viz_options_layout = QVBoxLayout(viz_options_group)
        
        # Treemap metric choice
        metric_layout = QHBoxLayout()
        metric_layout.addWidget(QLabel("Treemap Metric:"))
        self.metric_combo = QComboBox()
        self.metric_combo.addItems(["size", "lines"])
        self.metric_combo.setCurrentText(self.settings.value("viz_metric", "size"))
        metric_layout.addWidget(self.metric_combo)
        viz_options_layout.addLayout(metric_layout)
        
        # Cache option
        self.use_cache_check = QCheckBox("Use Visualization Cache")
        self.use_cache_check.setChecked(self.settings.value("use_viz_cache", "true") == "true")
        self.use_cache_check.setToolTip("Cache visualizations for faster subsequent loading")
        viz_options_layout.addWidget(self.use_cache_check)
        
        # Exclusions
        self.excluded_label = QLabel("Excluded Directories:")
        viz_options_layout.addWidget(self.excluded_label)
        
        self.exclusions_list = QListWidget()
        self.exclusions_list.setMaximumHeight(100)
        viz_options_layout.addWidget(self.exclusions_list)
        
        # Default excluded directories
        default_excludes = ['.git', 'node_modules', '.venv', '__pycache__', '.idea', '.vscode']
        custom_excludes = self.settings.value("viz_excluded_dirs", [])
        
        if isinstance(custom_excludes, str):
            custom_excludes = custom_excludes.split(',') if custom_excludes else []
        
        for exclude in default_excludes + custom_excludes:
            if exclude and exclude not in self.exclusions_list.findItems("*", Qt.MatchFlag.MatchWildcard):
                self.exclusions_list.addItem(exclude)
        
        options_layout.addWidget(viz_options_group)
        
        config_layout.addLayout(options_layout)
        
        # Generate button
        buttons_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Visualization")
        self.generate_btn.clicked.connect(self.generate_visualization)
        self.generate_btn.setMinimumHeight(40)
        buttons_layout.addWidget(self.generate_btn)
        
        # Export button
        self.export_btn = QPushButton("Export...")
        self.export_btn.clicked.connect(self.export_visualization)
        self.export_btn.setEnabled(False)
        buttons_layout.addWidget(self.export_btn)
        
        config_layout.addLayout(buttons_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        config_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        config_layout.addWidget(self.progress_label)
        
        splitter.addWidget(config_widget)
        
        # Bottom section: Visualization display
        viz_widget = QWidget()
        viz_layout = QVBoxLayout(viz_widget)
        
        self.web_view = QWebEngineView()
        viz_layout.addWidget(self.web_view)
        
        splitter.addWidget(viz_widget)
        
        # Set initial splitter sizes
        splitter.setSizes([300, 700])
        
        # Check for visualization modules
        if not HAS_VISUALIZATION:
            self.show_error("Visualization modules not found", 
                          "The visualization modules are not available. Some features will be disabled.")
            self.generate_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
    
    def browse_directory(self):
        """Open directory selection dialog"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Project Directory",
            self.directory or str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            self.set_directory(directory)
    
    def set_directory(self, directory):
        """Set the current directory"""
        self.directory = directory
        self.dir_edit.setText(directory)
        self.settings.setValue("last_project_directory", directory)
        
        # Update window title if possible
        if self.parent:
            self.parent.setWindowTitle(f"AllSeeingEye - {os.path.basename(directory)}")
    
    def get_config(self):
        """Get the current visualization configuration"""
        # Get excluded directories
        excluded_dirs = []
        for i in range(self.exclusions_list.count()):
            item_text = self.exclusions_list.item(i).text()
            if item_text:
                excluded_dirs.append(item_text)
        
        # Get cache directory
        cache_dir = None
        if self.use_cache_check.isChecked():
            cache_dir = os.path.join(os.path.expanduser("~"), ".allseeingeye", "cache")
            os.makedirs(cache_dir, exist_ok=True)
        
        # Build configuration
        config = {
            "excluded_dirs": excluded_dirs,
            "metric": self.metric_combo.currentText(),
            "max_file_size": 1024 * 1024,  # 1MB default
            "cache_dir": cache_dir
        }
        
        # Save settings
        self.settings.setValue("viz_excluded_dirs", ",".join(excluded_dirs))
        self.settings.setValue("viz_metric", config["metric"])
        self.settings.setValue("use_viz_cache", self.use_cache_check.isChecked())
        
        return config
    
    def get_visualization_type(self):
        """Get the selected visualization type"""
        if self.dep_graph_radio.isChecked():
            return "dependency_graph"
        elif self.treemap_radio.isChecked():
            return "treemap"
        elif self.dashboard_radio.isChecked():
            return "dashboard"
        else:
            return "dependency_graph"  # Default
    
    def generate_visualization(self):
        """Generate the selected visualization"""
        # Check for visualization modules
        if not HAS_VISUALIZATION:
            self.show_error("Visualization modules not found", 
                          "The visualization modules are not available.")
            return
        
        # Check directory
        if not self.directory or not os.path.isdir(self.directory):
            self.show_error("Invalid Directory", 
                          "Please select a valid project directory first.")
            return
        
        # Get configuration
        config = self.get_config()
        viz_type = self.get_visualization_type()
        
        # Update UI
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_label.setText(f"Preparing {viz_type} visualization...")
        self.progress_label.setVisible(True)
        self.generate_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        # Create and start the visualization thread
        self.viz_thread = VisualizationThread(viz_type, self.directory, config)
        self.viz_thread.progress.connect(self.update_progress)
        self.viz_thread.finished.connect(self.visualization_finished)
        self.viz_thread.error.connect(self.visualization_error)
        self.viz_thread.start()
    
    def update_progress(self, percentage, message):
        """Update progress bar and status"""
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(message)
    
    def visualization_finished(self, output_file):
        """Handle visualization completion"""
        # Update UI
        self.progress_bar.setValue(100)
        self.progress_label.setText("Visualization complete!")
        self.generate_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        # Store output file
        self.current_viz_file = output_file
        
        # Load visualization in web view
        self.web_view.load(QUrl.fromLocalFile(output_file))
        
        # Show success message
        self.progress_label.setText(f"Visualization generated: {os.path.basename(output_file)}")
    
    def visualization_error(self, error_message):
        """Handle visualization error"""
        # Update UI
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.generate_btn.setEnabled(True)
        
        # Show error
        self.show_error("Visualization Error", error_message)
    
    def export_visualization(self):
        """Export the current visualization to a file"""
        if not hasattr(self, 'current_viz_file') or not os.path.exists(self.current_viz_file):
            self.show_error("No Visualization", 
                          "Please generate a visualization first before exporting.")
            return
        
        # Get file name
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Visualization",
            os.path.basename(self.current_viz_file),
            "HTML Files (*.html)"
        )
        
        if file_path:
            # Copy the file
            import shutil
            try:
                shutil.copyfile(self.current_viz_file, file_path)
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Visualization exported to: {file_path}"
                )
            except Exception as e:
                self.show_error("Export Error", f"Failed to export visualization: {str(e)}")
    
    def show_error(self, title, message):
        """Show error message dialog"""
        QMessageBox.critical(self, title, message)
    
    # Convenience methods for external access
    def generate_dependency_graph(self):
        """Generate dependency graph (for toolbar/menu)"""
        self.dep_graph_radio.setChecked(True)
        self.generate_visualization()
    
    def generate_treemap(self):
        """Generate treemap (for toolbar/menu)"""
        self.treemap_radio.setChecked(True)
        self.generate_visualization()
    
    def generate_dashboard(self):
        """Generate dashboard (for toolbar/menu)"""
        self.dashboard_radio.setChecked(True)
        self.generate_visualization()
