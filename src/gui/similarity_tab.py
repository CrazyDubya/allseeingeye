#!/usr/bin/env python3
"""
Code similarity tab for AllSeeingEye GUI
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
    QSlider, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import QFont, QColor, QTextOption
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings, QUrl, QSize

# Configure logging
logger = logging.getLogger(__name__)

# Try to import similarity modules
try:
    # Try from src structure
    from src.similarity.code_similarity import CodeSimilarityAnalyzer
    from src.similarity.refactoring_suggestions import RefactoringSuggestionGenerator
    
    HAS_SIMILARITY = True
except ImportError:
    # Try from package structure
    try:
        from allseeingeye.similarity import CodeSimilarityAnalyzer, RefactoringSuggestionGenerator
        HAS_SIMILARITY = True
    except ImportError:
        logger.warning("Similarity modules not found, some features will be disabled")
        HAS_SIMILARITY = False

class SimilarityAnalysisThread(QThread):
    """Thread for running code similarity analysis in the background"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, directory, config):
        super().__init__()
        self.directory = directory
        self.config = config
    
    def run(self):
        """Run the similarity analysis"""
        try:
            self.progress.emit(0, "Starting similarity analysis...")
            
            # Configure analyzer
            analyzer = CodeSimilarityAnalyzer(
                base_directory=self.directory,
                excluded_dirs=self.config.get("excluded_dirs", []),
                excluded_files=self.config.get("excluded_files", []),
                max_file_size=self.config.get("max_file_size", 1024 * 1024),
                min_clone_size=self.config.get("min_clone_size", 20),
                cache_dir=self.config.get("cache_dir")
            )
            
            self.progress.emit(10, "Analyzing codebase...")
            
            # Run analysis
            results = analyzer.analyze_codebase()
            
            # Generate refactoring suggestions if requested
            if self.config.get("generate_suggestions", True):
                self.progress.emit(70, "Generating refactoring suggestions...")
                
                suggestion_generator = RefactoringSuggestionGenerator(
                    base_directory=self.directory,
                    min_fragment_count=self.config.get("min_fragment_count", 2),
                    min_token_count=self.config.get("min_token_count", 20)
                )
                
                suggestions = suggestion_generator.generate_suggestions(
                    similarity_results=results,
                    analyzer=analyzer
                )
                
                # Add suggestions to results
                if "refactoring_opportunities" not in results:
                    results["refactoring_opportunities"] = []
                
                results["refactoring_opportunities"].extend(suggestions)
            
            self.progress.emit(100, "Analysis complete!")
            self.finished.emit(results)
            
        except Exception as e:
            logger.error(f"Similarity analysis error: {str(e)}")
            self.error.emit(f"Analysis failed: {str(e)}")

class SimilarityTab(QWidget):
    """Tab for analyzing code similarity and refactoring opportunities"""
    
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
        
        # Split view between configuration and results
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
        
        # Configuration options (side by side)
        options_layout = QHBoxLayout()
        
        # Left column: Analysis Options
        analysis_group = QGroupBox("Analysis Options")
        analysis_layout = QFormLayout(analysis_group)
        
        # Min clone size
        self.clone_size_spin = QSpinBox()
        self.clone_size_spin.setRange(5, 100)
        self.clone_size_spin.setValue(int(self.settings.value("min_clone_size", 20)))
        self.clone_size_spin.setToolTip("Minimum token sequence to consider as a clone")
        analysis_layout.addRow("Min Clone Size:", self.clone_size_spin)
        
        # Min fragment count
        self.fragment_count_spin = QSpinBox()
        self.fragment_count_spin.setRange(2, 10)
        self.fragment_count_spin.setValue(int(self.settings.value("min_fragment_count", 2)))
        self.fragment_count_spin.setToolTip("Minimum number of fragments to suggest refactoring")
        analysis_layout.addRow("Min Fragment Count:", self.fragment_count_spin)
        
        # Min token count
        self.token_count_spin = QSpinBox()
        self.token_count_spin.setRange(10, 100)
        self.token_count_spin.setValue(int(self.settings.value("min_token_count", 20)))
        self.token_count_spin.setToolTip("Minimum tokens for viable refactoring")
        analysis_layout.addRow("Min Token Count:", self.token_count_spin)
        
        # Generate suggestions
        self.suggestions_check = QCheckBox()
        self.suggestions_check.setChecked(self.settings.value("generate_suggestions", "true") == "true")
        self.suggestions_check.setToolTip("Generate refactoring suggestions for duplicated code")
        analysis_layout.addRow("Generate Suggestions:", self.suggestions_check)
        
        # Use cache
        self.use_cache_check = QCheckBox()
        self.use_cache_check.setChecked(self.settings.value("similarity_use_cache", "true") == "true")
        self.use_cache_check.setToolTip("Cache analysis results for faster subsequent runs")
        analysis_layout.addRow("Use Cache:", self.use_cache_check)
        
        options_layout.addWidget(analysis_group)
        
        # Right column: Excluded Directories
        exclude_group = QGroupBox("Excluded Directories")
        exclude_layout = QVBoxLayout(exclude_group)
        
        self.exclude_list = QListWidget()
        exclude_layout.addWidget(self.exclude_list)
        
        # Default excluded directories
        default_excludes = ['.git', 'node_modules', '.venv', '__pycache__', '.idea', '.vscode']
        custom_excludes = self.settings.value("similarity_excluded_dirs", [])
        
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
        
        config_layout.addLayout(options_layout)
        
        # Run button
        self.run_btn = QPushButton("Analyze Code Similarity")
        self.run_btn.clicked.connect(self.analyze_similarity)
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
        
        # Clone Groups tab
        self.clones_tab = QWidget()
        clones_layout = QVBoxLayout(self.clones_tab)
        
        # Clone group list and details
        clones_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Clone group list
        self.clone_list = QTreeWidget()
        self.clone_list.setHeaderLabels(["ID", "Type", "Fragments", "Similarity", "Lines"])
        self.clone_list.setColumnWidth(0, 100)
        self.clone_list.setColumnWidth(1, 80)
        self.clone_list.setColumnWidth(2, 80)
        self.clone_list.setColumnWidth(3, 80)
        self.clone_list.currentItemChanged.connect(self.on_clone_selected)
        clones_splitter.addWidget(self.clone_list)
        
        # Right side: Clone details
        clone_details_widget = QWidget()
        clone_details_layout = QVBoxLayout(clone_details_widget)
        
        clone_details_layout.addWidget(QLabel("Fragment Details:"))
        
        self.fragment_text = QTextEdit()
        self.fragment_text.setReadOnly(True)
        clone_details_layout.addWidget(self.fragment_text)
        
        clones_splitter.addWidget(clone_details_widget)
        clones_splitter.setSizes([300, 500])
        
        clones_layout.addWidget(clones_splitter)
        
        # Refactoring tab
        self.refactoring_tab = QWidget()
        refactoring_layout = QVBoxLayout(self.refactoring_tab)
        
        self.refactoring_table = QTableWidget()
        self.refactoring_table.setColumnCount(5)
        self.refactoring_table.setHorizontalHeaderLabels(
            ["Title", "Type", "Files", "Complexity", "Benefit"]
        )
        self.refactoring_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.refactoring_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.refactoring_table.verticalHeader().setVisible(False)
        self.refactoring_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.refactoring_table.currentItemChanged.connect(self.on_refactoring_selected)
        refactoring_layout.addWidget(self.refactoring_table)
        
        # Refactoring details
        refactoring_layout.addWidget(QLabel("Refactoring Details:"))
        
        self.refactoring_details = QTextEdit()
        self.refactoring_details.setReadOnly(True)
        refactoring_layout.addWidget(self.refactoring_details)
        
        # Files tab
        self.files_tab = QWidget()
        files_layout = QVBoxLayout(self.files_tab)
        
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels(
            ["File", "Total Lines", "Duplicated Lines", "Duplication %"]
        )
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.files_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.files_table.verticalHeader().setVisible(False)
        self.files_table.setSortingEnabled(True)
        files_layout.addWidget(self.files_table)
        
        # Add tabs
        self.results_tabs.addTab(self.summary_tab, "Summary")
        self.results_tabs.addTab(self.clones_tab, "Clone Groups")
        self.results_tabs.addTab(self.refactoring_tab, "Refactoring")
        self.results_tabs.addTab(self.files_tab, "Files")
        
        results_layout.addWidget(self.results_tabs)
        
        # Export button
        self.export_btn = QPushButton("Export Results...")
        self.export_btn.clicked.connect(self.export_results)
        results_layout.addWidget(self.export_btn)
        
        splitter.addWidget(results_widget)
        
        # Set initial splitter sizes
        splitter.setSizes([300, 700])
        
        # Check for similarity modules
        if not HAS_SIMILARITY:
            self.show_error("Similarity modules not found", 
                          "The code similarity modules are not available. Some features will be disabled.")
            self.run_btn.setEnabled(False)
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
        
        # Get cache directory
        cache_dir = None
        if self.use_cache_check.isChecked():
            cache_dir = os.path.join(os.path.expanduser("~"), ".allseeingeye", "cache")
            os.makedirs(cache_dir, exist_ok=True)
        
        # Build configuration
        config = {
            "excluded_dirs": excluded_dirs,
            "excluded_files": [],  # Could add UI for this later
            "min_clone_size": self.clone_size_spin.value(),
            "min_fragment_count": self.fragment_count_spin.value(),
            "min_token_count": self.token_count_spin.value(),
            "generate_suggestions": self.suggestions_check.isChecked(),
            "cache_dir": cache_dir,
            "max_file_size": 1024 * 1024  # 1MB default
        }
        
        # Save settings
        self.settings.setValue("similarity_excluded_dirs", ",".join(excluded_dirs))
        self.settings.setValue("min_clone_size", config["min_clone_size"])
        self.settings.setValue("min_fragment_count", config["min_fragment_count"])
        self.settings.setValue("min_token_count", config["min_token_count"])
        self.settings.setValue("generate_suggestions", config["generate_suggestions"])
        self.settings.setValue("similarity_use_cache", self.use_cache_check.isChecked())
        
        return config
    
    def analyze_similarity(self):
        """Run the similarity analysis"""
        # Check for similarity modules
        if not HAS_SIMILARITY:
            self.show_error("Similarity modules not found", 
                          "The code similarity modules are not available.")
            return
        
        # Check directory
        if not self.directory or not os.path.isdir(self.directory):
            self.show_error("Invalid Directory", 
                          "Please select a valid project directory first.")
            return
        
        # Get configuration
        config = self.get_config()
        
        # Update UI
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.progress_label.setText("Preparing similarity analysis...")
        self.progress_label.setVisible(True)
        self.run_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        # Clear previous results
        self.clear_results()
        
        # Create and start the analysis thread
        self.analysis_thread = SimilarityAnalysisThread(self.directory, config)
        self.analysis_thread.progress.connect(self.update_progress)
        self.analysis_thread.finished.connect(self.analysis_finished)
        self.analysis_thread.error.connect(self.analysis_error)
        self.analysis_thread.start()
    
    def clear_results(self):
        """Clear all result displays"""
        self.summary_text.clear()
        self.clone_list.clear()
        self.fragment_text.clear()
        self.refactoring_table.setRowCount(0)
        self.refactoring_details.clear()
        self.files_table.setRowCount(0)
    
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
        self.export_btn.setEnabled(True)
        
        # Store results
        self.similarity_results = results
        
        # Display results in UI
        self.display_results(results)
    
    def analysis_error(self, error_message):
        """Handle analysis error"""
        # Update UI
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        self.run_btn.setEnabled(True)
        
        # Show error
        self.show_error("Analysis Error", error_message)
    
    def display_results(self, results):
        """Display similarity analysis results in the UI"""
        if not results:
            # No results to display
            return
        
        # Display summary
        self.display_summary(results)
        
        # Display clone groups
        self.display_clone_groups(results)
        
        # Display refactoring opportunities
        self.display_refactoring(results)
        
        # Display file statistics
        self.display_file_stats(results)
    
    def display_summary(self, results):
        """Display summary information"""
        if "summary" in results:
            summary = results["summary"]
            
            # Format summary text
            summary_text = f"""
            <h2>Code Similarity Analysis Summary</h2>
            
            <p>
            <b>Files analyzed:</b> {summary.get('analyzed_files', 0)}<br>
            <b>Code fragments:</b> {summary.get('code_fragments', 0)}<br>
            <b>Clone groups found:</b> {summary.get('clone_groups', 0)}<br>
            <b>Duplicated fragments:</b> {summary.get('duplicated_fragments', 0)}<br>
            <b>Duplication percentage:</b> {summary.get('duplication_percentage', 0)}%
            </p>
            
            <h3>Clone Types:</h3>
            <ul>
            """
            
            if "clone_types" in results:
                for clone_type, count in results["clone_types"].items():
                    summary_text += f"<li><b>{clone_type}</b>: {count}</li>"
            
            summary_text += """
            </ul>
            
            <p>
            <b>Type 1:</b> Exact duplicates (identical code)<br>
            <b>Type 2:</b> Renamed duplicates (same structure, different identifiers)<br>
            <b>Type 3:</b> Similar code (structural changes but similar functionality)
            </p>
            """
            
            if "refactoring_opportunities" in results:
                opps = results["refactoring_opportunities"]
                summary_text += f"""
                <h3>Refactoring Opportunities:</h3>
                <p>{len(opps)} potential refactoring opportunities identified.</p>
                """
            
            self.summary_text.setHtml(summary_text)
    
    def display_clone_groups(self, results):
        """Display clone groups in tree widget"""
        if "clone_groups" in results:
            clone_groups = results["clone_groups"]
            
            for group in clone_groups:
                # Create tree item for group
                item = QTreeWidgetItem(self.clone_list)
                item.setText(0, group.get("id", ""))
                item.setText(1, group.get("clone_type", ""))
                item.setText(2, str(group.get("fragment_count", 0)))
                item.setText(3, f"{group.get('similarity_score', 0):.2f}")
                item.setText(4, str(group.get("average_lines", 0)))
                
                # Store group data
                item.setData(0, Qt.ItemDataRole.UserRole, group)
                
                # Add fragments as child items
                fragments = group.get("fragments", [])
                for i, fragment in enumerate(fragments):
                    frag_item = QTreeWidgetItem(item)
                    frag_item.setText(0, f"Fragment {i+1}")
                    frag_item.setText(1, "")
                    frag_item.setText(2, "")
                    frag_item.setText(3, "")
                    frag_item.setText(4, f"{fragment.get('start_line', 0)}-{fragment.get('end_line', 0)}")
                    
                    # Store fragment file path
                    frag_item.setData(0, Qt.ItemDataRole.UserRole, fragment)
            
            # Adjust column widths
            for i in range(self.clone_list.columnCount()):
                self.clone_list.resizeColumnToContents(i)
    
    def on_clone_selected(self, current, previous):
        """Handle clone group selection"""
        if not current:
            self.fragment_text.clear()
            return
        
        # Get clone group data
        data = current.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            self.fragment_text.clear()
            return
        
        # Check if it's a fragment or group
        if "file_path" in data:
            # It's a fragment
            self.display_fragment(data)
        else:
            # It's a group - show general info
            group = data
            info = f"""
            <h3>Clone Group: {group.get('id', '')}</h3>
            <p>
            <b>Type:</b> {group.get('clone_type', '')}<br>
            <b>Fragments:</b> {group.get('fragment_count', 0)}<br>
            <b>Similarity Score:</b> {group.get('similarity_score', 0):.2f}<br>
            <b>Average Lines:</b> {group.get('average_lines', 0)}<br>
            <b>Token Count:</b> {group.get('token_count', 0)}
            </p>
            
            <p>Select a fragment to view its content.</p>
            """
            self.fragment_text.setHtml(info)
    
    def display_fragment(self, fragment):
        """Display fragment details"""
        file_path = fragment.get("file_path", "")
        start_line = fragment.get("start_line", 0)
        end_line = fragment.get("end_line", 0)
        
        # Try to load file content
        try:
            full_path = os.path.join(self.directory, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                    # Extract fragment
                    if 0 < start_line <= len(lines) and 0 < end_line <= len(lines):
                        fragment_content = ''.join(lines[start_line-1:end_line])
                    else:
                        fragment_content = "Invalid line range"
                    
                    # Format display
                    info = f"""
                    <h3>Fragment in {file_path}</h3>
                    <p>Lines {start_line}-{end_line}</p>
                    <pre>{fragment_content}</pre>
                    """
                    self.fragment_text.setHtml(info)
            else:
                self.fragment_text.setHtml(f"<p>File not found: {file_path}</p>")
        except Exception as e:
            self.fragment_text.setHtml(f"<p>Error reading file: {str(e)}</p>")
    
    def display_refactoring(self, results):
        """Display refactoring opportunities"""
        if "refactoring_opportunities" in results:
            opportunities = results["refactoring_opportunities"]
            
            # Clear table
            self.refactoring_table.setRowCount(0)
            
            # Add each opportunity
            for i, opp in enumerate(opportunities):
                row = self.refactoring_table.rowCount()
                self.refactoring_table.insertRow(row)
                
                # Add data
                self.refactoring_table.setItem(row, 0, QTableWidgetItem(opp.get("title", "")))
                self.refactoring_table.setItem(row, 1, QTableWidgetItem(opp.get("type", "")))
                
                # Format files
                files = opp.get("affected_files", [])
                file_count = len(files)
                files_text = f"{file_count} {'files' if file_count != 1 else 'file'}"
                self.refactoring_table.setItem(row, 2, QTableWidgetItem(files_text))
                
                # Complexity and benefit
                self.refactoring_table.setItem(row, 3, QTableWidgetItem(opp.get("complexity", "")))
                self.refactoring_table.setItem(row, 4, QTableWidgetItem(opp.get("estimated_benefit", "")))
                
                # Store data
                self.refactoring_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, opp)
    
    def on_refactoring_selected(self, current, previous):
        """Handle refactoring opportunity selection"""
        if not current:
            self.refactoring_details.clear()
            return
        
        # Get opportunity data from first cell
        row = current.row()
        item = self.refactoring_table.item(row, 0)
        if not item:
            self.refactoring_details.clear()
            return
        
        opp = item.data(Qt.ItemDataRole.UserRole)
        if not opp:
            self.refactoring_details.clear()
            return
        
        # Format details
        details = f"""
        <h3>{opp.get("title", "")}</h3>
        
        <p>
        <b>Type:</b> {opp.get("type", "")}<br>
        <b>Complexity:</b> {opp.get("complexity", "")}<br>
        <b>Estimated Benefit:</b> {opp.get("estimated_benefit", "")}
        </p>
        
        <h4>Affected Files:</h4>
        <ul>
        """
        
        for file in opp.get("affected_files", []):
            details += f"<li>{file}</li>"
        
        details += """
        </ul>
        
        <h4>Implementation:</h4>
        <ol>
        """
        
        # Add implementation steps if available
        steps = opp.get("implementation_steps", [])
        if steps:
            for step in steps:
                details += f"<li>{step}</li>"
        else:
            details += f"<li>Extract duplicated code into a {opp.get('type', 'function')}</li>"
            details += f"<li>Replace duplicate instances with calls to the new {opp.get('type', 'function')}</li>"
            details += f"<li>Adjust parameters as needed for each specific usage context</li>"
        
        details += "</ol>"
        
        self.refactoring_details.setHtml(details)
    
    def display_file_stats(self, results):
        """Display file statistics"""
        if "file_statistics" in results:
            file_stats = results["file_statistics"]
            
            # Clear table
            self.files_table.setRowCount(0)
            
            # Add each file
            for i, stat in enumerate(file_stats):
                row = self.files_table.rowCount()
                self.files_table.insertRow(row)
                
                # Add data
                self.files_table.setItem(row, 0, QTableWidgetItem(stat.get("file_path", "")))
                self.files_table.setItem(row, 1, QTableWidgetItem(str(stat.get("total_lines", 0))))
                self.files_table.setItem(row, 2, QTableWidgetItem(str(stat.get("duplicated_lines", 0))))
                
                # Format duplication percentage
                dup_pct = stat.get("duplication_percentage", 0)
                pct_item = QTableWidgetItem(f"{dup_pct:.2f}%")
                
                # Color based on percentage
                if dup_pct > 50:
                    pct_item.setBackground(QColor(255, 150, 150))  # Red
                elif dup_pct > 20:
                    pct_item.setBackground(QColor(255, 230, 150))  # Yellow
                
                self.files_table.setItem(row, 3, pct_item)
                
                # Make numerical columns sortable
                self.files_table.item(row, 1).setData(Qt.ItemDataRole.UserRole, int(stat.get("total_lines", 0)))
                self.files_table.item(row, 2).setData(Qt.ItemDataRole.UserRole, int(stat.get("duplicated_lines", 0)))
                self.files_table.item(row, 3).setData(Qt.ItemDataRole.UserRole, float(dup_pct))
    
    def export_results(self):
        """Export analysis results"""
        if not hasattr(self, 'similarity_results'):
            QMessageBox.warning(
                self,
                "No Results",
                "Please run a similarity analysis first before exporting results."
            )
            return
        
        # Get export file path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Similarity Results",
            os.path.join(str(Path.home()), "similarity_analysis.json"),
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                # Write results to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.similarity_results, f, indent=2)
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Results exported to: {file_path}"
                )
            except Exception as e:
                self.show_error("Export Error", f"Failed to export results: {str(e)}")
    
    def show_error(self, title, message):
        """Show error message dialog"""
        QMessageBox.critical(self, title, message)
