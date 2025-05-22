#!/usr/bin/env python3
"""
Main window for AllSeeingEye GUI
"""

import os
import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTabWidget, QFileDialog, QStatusBar,
    QToolBar, QSplitter, QMenuBar, QMenu, QMessageBox, QDialog
)
from PyQt6.QtGui import QIcon, QAction, QFont, QPixmap
from PyQt6.QtCore import Qt, QSize, QSettings, QThread, pyqtSignal, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

# Import tabs
try:
    from .analysis_tab import AnalysisTab
    from .visualization_tab import VisualizationTab 
    from .similarity_tab import SimilarityTab
    from .settings_tab import SettingsTab
    from .about_dialog import AboutDialog
except ImportError:
    # Alternative import if relative imports fail
    import os
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    try:
        from analysis_tab import AnalysisTab
        from visualization_tab import VisualizationTab
        from similarity_tab import SimilarityTab
        from settings_tab import SettingsTab
        from about_dialog import AboutDialog
    except ImportError as e:
        logger.error(f"Failed to import tab modules: {e}")
        # Create placeholder tabs for critical error
        AnalysisTab = None
        VisualizationTab = None
        SimilarityTab = None
        SettingsTab = None
        AboutDialog = None

# Configure logging
logger = logging.getLogger(__name__)

class AllSeeingEyeGUI(QMainWindow):
    """Main window for AllSeeingEye application"""
    
    def __init__(self):
        super().__init__()
        
        # Application settings
        self.settings = QSettings("AllSeeingEye", "AllSeeingEye")
        
        # Initialize UI
        self.init_ui()
        
        # Restore window geometry
        self.restore_geometry()
        
    def init_ui(self):
        """Initialize the user interface"""
        # Set window properties
        self.setWindowTitle("AllSeeingEye - Codebase Analysis Tool")
        self.setMinimumSize(1200, 800)
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create toolbar
        self.create_toolbar()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create tabs
        self.create_tabs()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        open_action = QAction("Open Project...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        export_menu = file_menu.addMenu("Export")
        
        export_json_action = QAction("Export to JSON...", self)
        export_json_action.triggered.connect(lambda: self.export_results("json"))
        export_menu.addAction(export_json_action)
        
        export_md_action = QAction("Export to Markdown...", self)
        export_md_action.triggered.connect(lambda: self.export_results("markdown"))
        export_menu.addAction(export_md_action)
        
        export_html_action = QAction("Export to HTML...", self)
        export_html_action.triggered.connect(lambda: self.export_results("html"))
        export_menu.addAction(export_html_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        preferences_action = QAction("Preferences", self)
        preferences_action.triggered.connect(self.show_settings)
        edit_menu.addAction(preferences_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        for tab_name in ["Analysis", "Visualization", "Similarity", "Settings"]:
            tab_action = QAction(f"Show {tab_name}", self)
            tab_action.triggered.connect(lambda checked, name=tab_name: self.switch_to_tab(name))
            view_menu.addAction(tab_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        analyze_action = QAction("Run Analysis", self)
        analyze_action.triggered.connect(lambda: self.run_analysis())
        tools_menu.addAction(analyze_action)
        
        tools_menu.addSeparator()
        
        dependency_action = QAction("Generate Dependency Graph", self)
        dependency_action.triggered.connect(lambda: self.visualization_tab.generate_dependency_graph())
        tools_menu.addAction(dependency_action)
        
        treemap_action = QAction("Generate Treemap", self)
        treemap_action.triggered.connect(lambda: self.visualization_tab.generate_treemap())
        tools_menu.addAction(treemap_action)
        
        dashboard_action = QAction("Generate Metrics Dashboard", self)
        dashboard_action.triggered.connect(lambda: self.visualization_tab.generate_dashboard())
        tools_menu.addAction(dashboard_action)
        
        tools_menu.addSeparator()
        
        similarity_action = QAction("Analyze Code Similarity", self)
        similarity_action.triggered.connect(lambda: self.similarity_tab.analyze_similarity())
        tools_menu.addAction(similarity_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        docs_action = QAction("Documentation", self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create the application toolbar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # Open project action
        open_action = QAction("Open Project", self)
        open_action.triggered.connect(self.open_project)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        # Run analysis action
        analyze_action = QAction("Run Analysis", self)
        analyze_action.triggered.connect(self.run_analysis)
        toolbar.addAction(analyze_action)
        
        # Visualization actions
        toolbar.addSeparator()
        
        dependency_action = QAction("Dependency Graph", self)
        dependency_action.triggered.connect(lambda: self.visualization_tab.generate_dependency_graph())
        toolbar.addAction(dependency_action)
        
        treemap_action = QAction("Treemap", self)
        treemap_action.triggered.connect(lambda: self.visualization_tab.generate_treemap())
        toolbar.addAction(treemap_action)
        
        dashboard_action = QAction("Dashboard", self)
        dashboard_action.triggered.connect(lambda: self.visualization_tab.generate_dashboard())
        toolbar.addAction(dashboard_action)
        
        # Similarity action
        toolbar.addSeparator()
        
        similarity_action = QAction("Code Similarity", self)
        similarity_action.triggered.connect(lambda: self.similarity_tab.analyze_similarity())
        toolbar.addAction(similarity_action)
        
    def create_tabs(self):
        """Create the tabbed interface"""
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Check if tab classes are available
        if None in [AnalysisTab, VisualizationTab, SimilarityTab, SettingsTab]:
            # Create error message tab
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel("Error: Failed to load tab modules!")
            error_label.setStyleSheet("color: red; font-weight: bold; font-size: 16px;")
            error_layout.addWidget(error_label)
            
            details_label = QLabel("There was an error importing the GUI modules. Please check your installation.")
            error_layout.addWidget(details_label)
            
            self.tabs.addTab(error_widget, "Error")
            return
        
        # Create different tabs
        self.analysis_tab = AnalysisTab(self)
        self.visualization_tab = VisualizationTab(self)
        self.similarity_tab = SimilarityTab(self)
        self.settings_tab = SettingsTab(self)
        
        # Add tabs to tab widget
        self.tabs.addTab(self.analysis_tab, "Analysis")
        self.tabs.addTab(self.visualization_tab, "Visualization")
        self.tabs.addTab(self.similarity_tab, "Similarity")
        self.tabs.addTab(self.settings_tab, "Settings")
        
        # Connect tab changed signal
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
    def on_tab_changed(self, index):
        """Handle tab selection changes"""
        tab_name = self.tabs.tabText(index)
        logger.debug(f"Switched to {tab_name} tab")
        
        # Update status bar
        self.status_bar.showMessage(f"Ready - {tab_name}")
        
    def switch_to_tab(self, tab_name):
        """Switch to a specific tab by name"""
        tab_names = ["Analysis", "Visualization", "Similarity", "Settings"]
        
        if tab_name in tab_names:
            index = tab_names.index(tab_name)
            self.tabs.setCurrentIndex(index)
            
    def open_project(self):
        """Open a project directory"""
        # Get directory from user
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Project Directory",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            # Set as current project
            self.set_project_directory(directory)
    
    def set_project_directory(self, directory):
        """Set the current project directory"""
        if os.path.isdir(directory):
            # Store in settings
            self.settings.setValue("last_project_directory", directory)
            
            # Update all tabs with new directory
            self.analysis_tab.set_directory(directory)
            self.visualization_tab.set_directory(directory)
            self.similarity_tab.set_directory(directory)
            
            # Update window title
            self.setWindowTitle(f"AllSeeingEye - {os.path.basename(directory)}")
            
            # Update status
            self.status_bar.showMessage(f"Project set to: {directory}")
            
            logger.info(f"Set project directory to: {directory}")
    
    def run_analysis(self):
        """Run the analysis operation (delegates to analysis tab)"""
        self.switch_to_tab("Analysis")
        self.analysis_tab.run_analysis()
        
    def export_results(self, format_type):
        """Export analysis results in the specified format"""
        # Check if results exist
        if not hasattr(self, 'analysis_results'):
            QMessageBox.warning(
                self,
                "No Results",
                "Please run an analysis first before exporting results."
            )
            return
        
        # Get export file path
        file_types = {
            "json": "JSON Files (*.json)",
            "markdown": "Markdown Files (*.md)",
            "html": "HTML Files (*.html)",
        }
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Results",
            str(Path.home()),
            file_types.get(format_type, "All Files (*)")
        )
        
        if file_path:
            try:
                # Call appropriate export function
                self.analysis_tab.export_results(file_path, format_type)
                self.status_bar.showMessage(f"Results exported to: {file_path}")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export results: {str(e)}"
                )
    
    def show_settings(self):
        """Show the settings tab"""
        self.switch_to_tab("Settings")
    
    def show_documentation(self):
        """Show documentation"""
        # Placeholder for documentation
        QMessageBox.information(
            self,
            "Documentation",
            "Documentation is available on the project website."
        )
    
    def show_about(self):
        """Show about dialog"""
        about_dialog = AboutDialog(self)
        about_dialog.exec()
    
    def restore_geometry(self):
        """Restore window geometry from settings"""
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save window geometry
        self.settings.setValue("geometry", self.saveGeometry())
        
        # Accept the event
        event.accept()


def main():
    """Main entry point for the GUI application"""
    import sys
    app = QApplication(sys.argv)
    app.setApplicationName("AllSeeingEye")
    app.setOrganizationName("AllSeeingEye")
    app.setApplicationVersion("2.0")
    
    window = AllSeeingEyeGUI()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
