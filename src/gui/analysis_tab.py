#!/usr/bin/env python3
"""
Analysis tab for AllSeeingEye GUI
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
    QSplitter, QFrame, QTabWidget, QMessageBox, QScrollArea, QFormLayout
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QTimer

# Try to import AllSeeingEye modules
try:
    # Try importing from src structure
    from src.core.analyzer import Analyzer
    try:
        from src.performance.efficient_analyzer import EfficientAnalyzer
        HAS_EFFICIENT_ANALYZER = True
    except ImportError:
        HAS_EFFICIENT_ANALYZER = False
    
    MODULE_IMPORT_SUCCESS = True
    
except ImportError:
    # Fall back to importing from root module
    try:
        from allseeingeye import AllSeeingEye as Analyzer
        HAS_EFFICIENT_ANALYZER = False
        MODULE_IMPORT_SUCCESS = True
    except ImportError:
        logging.error("Failed to import AllSeeingEye modules")
        MODULE_IMPORT_SUCCESS = False

# Import AllSeeingEye core components
try:
    from src.core.file_category import FileCategory
    HAS_FILE_CATEGORY = True
except ImportError:
    try:
        from allseeingeye import FileCategory
        HAS_FILE_CATEGORY = True
    except ImportError:
        HAS_FILE_CATEGORY = False
        logging.error("Failed to import FileCategory")

# Configure logging
logger = logging.getLogger(__name__)

class AnalysisThread(QThread):
    """Thread for running analysis in the background"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, directory, config):
        super().__init__()
        self.directory = directory
        self.config = config
    
    def run(self):
        """Run the analysis"""
        try:
            self.progress.emit(0, "Starting analysis...")
            
            # Select analyzer class based on configuration
            if self.config.get("use_efficient_analyzer", True) and HAS_EFFICIENT_ANALYZER:
                analyzer_class = EfficientAnalyzer
                self.progress.emit(5, "Using EfficientAnalyzer...")
            else:
                analyzer_class = Analyzer
                self.progress.emit(5, "Using standard Analyzer...")
            
            # Configure analyzer
            analyzer = analyzer_class(
                directory=self.directory,
                excluded_dirs=self.config.get("excluded_dirs", []),
                excluded_files=self.config.get("excluded_files", []),
                included_categories=self.config.get("included_categories"),
                excluded_categories=self.config.get("excluded_categories"),
                max_file_size=self.config.get("max_file_size", 1024 * 1024),
                max_files=self.config.get("max_files", 1000),
                output_format=self.config.get("output_format", "json")
            )
            
            self.progress.emit(10, "Analyzer configured...")
            
            # Connect progress reporting if available
            if hasattr(analyzer, "set_progress_callback"):
                analyzer.set_progress_callback(self._progress_callback)
            
            # Run analysis
            self.progress.emit(15, "Running analysis...")
            output_file = analyzer.run()
            
            # Load the results
            self.progress.emit(90, "Loading results...")
            
            result_data = None
            if output_file and os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    if output_file.endswith('.json'):
                        result_data = json.load(f)
                    else:
                        # For non-JSON formats, just store the file path
                        result_data = {"output_file": output_file}
            
            self.progress.emit(100, "Analysis complete!")
            self.finished.emit(result_data)
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            self.error.emit(f"Analysis failed: {str(e)}")
    
    def _progress_callback(self, percentage, message):
        """Handle progress updates from the analyzer"""
        # Map the 0-100 percentage from analyzer to 15-90 range
        adjusted = 15 + (percentage * 0.75)
        self.progress.emit(int(adjusted), message)

class AnalysisTab(QWidget):
    """Tab for running and viewing analysis"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.settings = QSettings("AllSeeingEye", "AllSeeingEye")
        self.directory = self.settings.value("last_project_directory", "")
        
        # Initialize UI
        self.init_ui()
        
        # Update category checkboxes
        self.update_category_checkboxes()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create two main sections
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
        
        # Configuration options
        options_layout = QHBoxLayout()
        
        # Left column: Analysis Options
        analysis_group = QGroupBox("Analysis Options")
        analysis_layout = QVBoxLayout(analysis_group)
        
        # Output format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["json", "markdown", "text", "html"])
        self.format_combo.setCurrentText(self.settings.value("output_format", "json"))
        format_layout.addWidget(self.format_combo)
        analysis_layout.addLayout(format_layout)
        
        # Max files
        max_files_layout = QHBoxLayout()
        max_files_layout.addWidget(QLabel("Max Files:"))
        self.max_files_spin = QSpinBox()
        self.max_files_spin.setRange(10, 100000)
        self.max_files_spin.setValue(int(self.settings.value("max_files", 1000)))
        max_files_layout.addWidget(self.max_files_spin)
        analysis_layout.addLayout(max_files_layout)
        
        # Max file size
        max_size_layout = QHBoxLayout()
        max_size_layout.addWidget(QLabel("Max File Size (KB):"))
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(1, 10000)
        self.max_size_spin.setValue(int(self.settings.value("max_file_size", 1024)))
        max_size_layout.addWidget(self.max_size_spin)
        analysis_layout.addLayout(max_size_layout)
        
        # Use efficient analyzer
        self.efficient_check = QCheckBox("Use Efficient Analyzer")
        self.efficient_check.setChecked(self.settings.value("use_efficient_analyzer", "true") == "true")
        self.efficient_check.setEnabled(HAS_EFFICIENT_ANALYZER)
        if not HAS_EFFICIENT_ANALYZER:
            self.efficient_check.setToolTip("EfficientAnalyzer not available")
        analysis_layout.addWidget(self.efficient_check)
        
        options_layout.addWidget(analysis_group)
        
        # Middle column: Excluded Directories
        exclude_group = QGroupBox("Excluded Directories")
        exclude_layout = QVBoxLayout(exclude_group)
        
        self.exclude_list = QListWidget()
        exclude_layout.addWidget(self.exclude_list)
        
        # Default excluded directories
        default_excludes = ['.git', 'node_modules', '.venv', '__pycache__', '.idea', '.vscode']
        custom_excludes = self.settings.value("excluded_dirs", [])
        
        if isinstance(custom_excludes, str):
            custom_excludes = custom_excludes.split(',') if custom_excludes else []
        
        for exclude in default_excludes + custom_excludes:
            if exclude and exclude not in self.exclude_list.findItems("*", Qt.MatchFlag.MatchWildcard):
                self.exclude_list.addItem(exclude)
        
        # Buttons for list management
        exclude_btn_layout = QHBoxLayout()
        
        self.add_exclude_btn = QPushButton("Add")
        self.add_exclude_btn.clicked.connect(self.add_exclusion)
        exclude_btn_layout.addWidget(self.add_exclude_btn)
        
        self.remove_exclude_btn = QPushButton("Remove")
        self.remove_exclude_btn.clicked.connect(self.remove_exclusion)
        exclude_btn_layout.addWidget(self.remove_exclude_btn)
        
        exclude_layout.addLayout(exclude_btn_layout)
        options_layout.addWidget(exclude_group)
        
        # Right column: File Categories
        if HAS_FILE_CATEGORY:
            category_group = QGroupBox("File Categories")
            category_layout = QVBoxLayout(category_group)
            
            self.category_checks = {}
            self.category_layout = category_layout  # Store for later updates
            
            options_layout.addWidget(category_group)
        
        config_layout.addLayout(options_layout)
        
        # Run button
        self.run_btn = QPushButton("Run Analysis")
        self.run_btn.clicked.connect(self.run_analysis)
        self.run_btn.setMinimumHeight(40)
        config_layout.addWidget(self.run_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        config_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        config_layout.addWidget(self.progress_label)
        
        splitter.addWidget(config_widget)
        
        # Bottom section: Results
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        self.results_tabs = QTabWidget()
        
        # Summary tab
        self.summary_tab = QWidget()
        summary_layout = QVBoxLayout(self.summary_tab)
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        
        # Statistics tab
        self.stats_tab = QWidget()
        stats_layout = QVBoxLayout(self.stats_tab)
        self.stats_tree = QTreeWidget()
        self.stats_tree.setHeaderLabels(["Property", "Value"])
        stats_layout.addWidget(self.stats_tree)
        
        # Files tab
        self.files_tab = QWidget()
        files_layout = QVBoxLayout(self.files_tab)
        self.files_tree = QTreeWidget()
        self.files_tree.setHeaderLabels(["File", "Category", "Size", "Lines"])
        files_layout.addWidget(self.files_tree)
        
        # Add tabs
        self.results_tabs.addTab(self.summary_tab, "Summary")
        self.results_tabs.addTab(self.stats_tab, "Statistics")
        self.results_tabs.addTab(self.files_tab, "Files")
        
        results_layout.addWidget(self.results_tabs)
        
        # Export button
        self.export_btn = QPushButton("Export Results...")
        self.export_btn.clicked.connect(self.export_dialog)
        results_layout.addWidget(self.export_btn)
        
        splitter.addWidget(results_widget)
        
        # Set initial splitter sizes
        splitter.setSizes([400, 600])
    
    def update_category_checkboxes(self):
        """Update the category checkboxes based on FileCategory"""
        if HAS_FILE_CATEGORY:
            # Clear existing checkboxes
            for i in reversed(range(self.category_layout.count())):
                item = self.category_layout.itemAt(i)
                if item.widget():
                    item.widget().deleteLater()
            
            self.category_checks = {}
            
            # Get all categories
            categories = FileCategory.CATEGORIES if hasattr(FileCategory, 'CATEGORIES') else {}
            
            # Get selected categories from settings
            included_cats = self.settings.value("included_categories", [])
            excluded_cats = self.settings.value("excluded_categories", [])
            
            if isinstance(included_cats, str):
                included_cats = included_cats.split(',') if included_cats else []
            
            if isinstance(excluded_cats, str):
                excluded_cats = excluded_cats.split(',') if excluded_cats else []
            
            # Create a checkbox for each category
            for category, info in categories.items():
                description = info.get("description", category)
                check = QCheckBox(f"{category} ({description})")
                
                # Set checked state
                if included_cats:
                    # If included list exists, check if in it
                    check.setChecked(category in included_cats)
                elif excluded_cats:
                    # Otherwise use excluded list
                    check.setChecked(category not in excluded_cats)
                else:
                    # Default to checked
                    check.setChecked(True)
                
                self.category_layout.addWidget(check)
                self.category_checks[category] = check
            
            # Select all / Deselect all buttons
            btn_layout = QHBoxLayout()
            
            self.select_all_btn = QPushButton("Select All")
            self.select_all_btn.clicked.connect(self.select_all_categories)
            btn_layout.addWidget(self.select_all_btn)
            
            self.deselect_all_btn = QPushButton("Deselect All")
            self.deselect_all_btn.clicked.connect(self.deselect_all_categories)
            btn_layout.addWidget(self.deselect_all_btn)
            
            self.category_layout.addLayout(btn_layout)
    
    def select_all_categories(self):
        """Select all category checkboxes"""
        for check in self.category_checks.values():
            check.setChecked(True)
    
    def deselect_all_categories(self):
        """Deselect all category checkboxes"""
        for check in self.category_checks.values():
            check.setChecked(False)
    
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
    
    def add_exclusion(self):
        """Add a directory to the exclusion list"""
        # Simple implementation - just add a blank item for editing
        item = QListWidgetItem("new_exclusion")
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.exclude_list.addItem(item)
        self.exclude_list.editItem(item)
    
    def remove_exclusion(self):
        """Remove selected directory from exclusion list"""
        selected_items = self.exclude_list.selectedItems()
        for item in selected_items:
            self.exclude_list.takeItem(self.exclude_list.row(item))
    
    def get_config(self):
        """Get the current configuration"""
        # Get excluded directories
        excluded_dirs = []
        for i in range(self.exclude_list.count()):
            item_text = self.exclude_list.item(i).text()
            if item_text:
                excluded_dirs.append(item_text)
        
        # Get selected categories
        included_categories = []
        excluded_categories = []
        
        if self.category_checks:
            all_categories = list(self.category_checks.keys())
            
            # Determine whether to use include or exclude list based on what's shorter
            selected = [c for c, check in self.category_checks.items() if check.isChecked()]
            unselected = [c for c, check in self.category_checks.items() if not check.isChecked()]
            
            if len(unselected) < len(selected):
                # Use exclude list (it's shorter)
                excluded_categories = unselected
            else:
                # Use include list
                included_categories = selected
        
        # Build configuration
        config = {
            "excluded_dirs": excluded_dirs,
            "excluded_files": [],  # Could add UI for this later
            "output_format": self.format_combo.currentText(),
            "max_files": self.max_files_spin.value(),
            "max_file_size": self.max_size_spin.value() * 1024,  # Convert KB to bytes
            "use_efficient_analyzer": self.efficient_check.isChecked()
        }
        
        # Add categories if we have them
        if included_categories:
            config["included_categories"] = included_categories
        
        if excluded_categories:
            config["excluded_categories"] = excluded_categories
        
        # Save settings
        self.settings.setValue("excluded_dirs", ",".join(excluded_dirs))
        self.settings.setValue("output_format", config["output_format"])
        self.settings.setValue("max_files", config["max_files"])
        self.settings.setValue("max_file_size", config["max_file_size"] // 1024)  # Store as KB
        self.settings.setValue("use_efficient_analyzer", config["use_efficient_analyzer"])
        
        if included_categories:
            self.settings.setValue("included_categories", ",".join(included_categories))
        
        if excluded_categories:
            self.settings.setValue("excluded_categories", ",".join(excluded_categories))
        
        return config
    
    def run_analysis(self):
        """Run the analysis"""
        if not self.directory or not os.path.isdir(self.directory):
            QMessageBox.warning(
                self,
                "Invalid Directory",
                "Please select a valid project directory first."
            )
            return
        
        # Get configuration
        config = self.get_config()
        
        # Update UI
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_label.setText("Preparing analysis...")
        self.progress_label.setVisible(True)
        self.run_btn.setEnabled(False)
        
        # Create and start the analysis thread
        self.analysis_thread = AnalysisThread(self.directory, config)
        self.analysis_thread.progress.connect(self.update_progress)
        self.analysis_thread.finished.connect(self.analysis_finished)
        self.analysis_thread.error.connect(self.analysis_error)
        self.analysis_thread.start()
    
    def update_progress(self, percentage, message):
        """Update progress bar and status"""
        self.progress_bar.setValue(percentage)
        self.progress_label.setText(message)
    
    def analysis_finished(self, results):
        """Handle analysis completion"""
        # Update UI
        self.progress_bar.setValue(100)
        self.progress_label.setText("Analysis complete!")
        self.run_btn.setEnabled(True)
        
        # Hide progress after a delay
        QTimer.singleShot(3000, lambda: self.progress_bar.setVisible(False))
        QTimer.singleShot(3000, lambda: self.progress_label.setVisible(False))
        
        # Store results
        self.analysis_results = results
        
        # If parent exists, also store results there
        if self.parent:
            self.parent.analysis_results = results
        
        # Display results in UI
        self.display_results(results)
    
    def analysis_error(self, error_message):
        """Handle analysis error"""
        # Update UI
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.run_btn.setEnabled(True)
        
        # Show error
        QMessageBox.critical(
            self,
            "Analysis Error",
            error_message
        )
    
    def display_results(self, results):
        """Display analysis results in the UI"""
        if not results:
            # No results to display
            return
        
        # Clear existing results
        self.summary_text.clear()
        self.stats_tree.clear()
        self.files_tree.clear()
        
        # For JSON results
        if isinstance(results, dict):
            # Display summary
            if "codebase_summary" in results:
                self.summary_text.setText(results["codebase_summary"])
            
            # Display statistics
            if "statistics" in results:
                stats = results["statistics"]
                self._add_stats_to_tree(stats)
            
            # Display files
            if "files_content" in results:
                self._add_files_to_tree(results["files_content"])
        
        # For file path results
        elif "output_file" in results:
            output_file = results["output_file"]
            
            # Just display the file path
            self.summary_text.setText(f"Analysis complete. Results saved to:\n{output_file}")
    
    def _add_stats_to_tree(self, stats):
        """Add statistics to the tree widget"""
        def add_stat(parent, name, value):
            item = QTreeWidgetItem(parent)
            item.setText(0, str(name))
            item.setText(1, str(value))
            return item
        
        # Add top level stats
        for key, value in stats.items():
            if key == "files_by_category":
                # Add category counts as a subtree
                cat_item = QTreeWidgetItem(self.stats_tree)
                cat_item.setText(0, "Files by Category")
                cat_item.setText(1, "")
                
                for cat, count in value.items():
                    add_stat(cat_item, cat, count)
                
                cat_item.setExpanded(True)
            else:
                # Add as top-level item
                add_stat(self.stats_tree, key, value)
        
        # Auto-resize columns
        for i in range(self.stats_tree.columnCount()):
            self.stats_tree.resizeColumnToContents(i)
    
    def _add_files_to_tree(self, files_content):
        """Add files to the tree widget"""
        # Add files grouped by category
        for category, files in files_content.items():
            category_item = QTreeWidgetItem(self.files_tree)
            category_item.setText(0, category.capitalize())
            category_item.setText(1, f"{len(files)} files")
            
            for file_path, file_info in files.items():
                file_item = QTreeWidgetItem(category_item)
                file_item.setText(0, file_path)
                file_item.setText(1, category)
                file_item.setText(2, file_info.get("size_formatted", ""))
                
                if "line_count" in file_info:
                    file_item.setText(3, str(file_info["line_count"]))
        
        # Auto-resize columns
        for i in range(self.files_tree.columnCount()):
            self.files_tree.resizeColumnToContents(i)
    
    def export_dialog(self):
        """Show export dialog"""
        if not hasattr(self, 'analysis_results'):
            QMessageBox.warning(
                self,
                "No Results",
                "Please run an analysis first before exporting results."
            )
            return
        
        # Simple implementation - just prompt for file location
        formats = {
            "JSON": "json",
            "Markdown": "markdown",
            "HTML": "html",
            "Text": "text"
        }
        
        # Get format selection from combo box
        format_name = self.format_combo.currentText()
        
        file_types = {
            "json": "JSON Files (*.json)",
            "markdown": "Markdown Files (*.md)",
            "html": "HTML Files (*.html)",
            "text": "Text Files (*.txt)",
        }
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            os.path.join(str(Path.home()), f"codebase_analysis.{format_name}"),
            file_types.get(format_name, "All Files (*)")
        )
        
        if file_path:
            self.export_results(file_path, format_name)
    
    def export_results(self, file_path, format_type):
        """Export results to the specified file"""
        if not hasattr(self, 'analysis_results'):
            raise ValueError("No analysis results to export")
        
        try:
            # Get the results
            results = self.analysis_results
            
            # Determine how to export based on results and format type
            if isinstance(results, dict) and "statistics" in results:
                # We have full JSON results
                if format_type == "json":
                    # Write as JSON
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2)
                else:
                    # Need to convert to other format
                    # (this would call formatters from AllSeeingEye)
                    # For now, we'll just write JSON as a fallback
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2)
            
            elif "output_file" in results:
                # We already have a file on disk, just copy it
                import shutil
                shutil.copyfile(results["output_file"], file_path)
            
            else:
                # Fallback - just write whatever we have
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
            
            # Show success message
            QMessageBox.information(
                self,
                "Export Successful",
                f"Results exported to: {file_path}"
            )
            
        except Exception as e:
            raise Exception(f"Failed to export results: {str(e)}")
