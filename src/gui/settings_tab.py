#!/usr/bin/env python3
"""
Settings tab for AllSeeingEye GUI
"""

import os
import sys
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QGroupBox, QCheckBox, QSpinBox, QFileDialog, QComboBox, QTextEdit,
    QTabWidget, QFormLayout, QMessageBox, QColorDialog, QSlider,
    QRadioButton, QButtonGroup
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QSettings, QSize

# Configure logging
logger = logging.getLogger(__name__)

class SettingsTab(QWidget):
    """Tab for configuring application settings"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.settings = QSettings("AllSeeingEye", "AllSeeingEye")
        
        # Initialize UI
        self.init_ui()
        
        # Load current settings
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Create tabs for different setting categories
        settings_tabs = QTabWidget()
        layout.addWidget(settings_tabs)
        
        # General settings tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Application settings group
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout(app_group)
        
        # Default output format
        self.format_combo = QComboBox()
        self.format_combo.addItems(["json", "markdown", "text", "html"])
        app_layout.addRow("Default Output Format:", self.format_combo)
        
        # Default max files
        self.max_files_spin = QSpinBox()
        self.max_files_spin.setRange(10, 100000)
        self.max_files_spin.setSingleStep(100)
        app_layout.addRow("Default Max Files:", self.max_files_spin)
        
        # Default max file size
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(1, 10000)
        self.max_size_spin.setSingleStep(100)
        self.max_size_spin.setSuffix(" KB")
        app_layout.addRow("Default Max File Size:", self.max_size_spin)
        
        # Use efficient analyzer
        self.efficient_check = QCheckBox()
        app_layout.addRow("Use Efficient Analyzer:", self.efficient_check)
        
        # Use caching
        self.caching_check = QCheckBox()
        app_layout.addRow("Enable Result Caching:", self.caching_check)
        
        # Cache location
        cache_location_layout = QHBoxLayout()
        self.cache_path_edit = QLineEdit()
        self.cache_path_edit.setReadOnly(True)
        cache_location_layout.addWidget(self.cache_path_edit)
        
        self.cache_browse_btn = QPushButton("Browse...")
        self.cache_browse_btn.clicked.connect(self.browse_cache_directory)
        cache_location_layout.addWidget(self.cache_browse_btn)
        
        app_layout.addRow("Cache Location:", cache_location_layout)
        
        general_layout.addWidget(app_group)
        
        # LLM integration group
        llm_group = QGroupBox("LLM Integration")
        llm_layout = QFormLayout(llm_group)
        
        # Enable LLM
        self.llm_check = QCheckBox()
        llm_layout.addRow("Enable LLM Integration:", self.llm_check)
        
        # LLM provider
        self.llm_provider_combo = QComboBox()
        self.llm_provider_combo.addItems(["ollama", "mock"])
        llm_layout.addRow("LLM Provider:", self.llm_provider_combo)
        
        # LLM model
        self.llm_model_combo = QComboBox()
        self.llm_model_combo.addItems(["gemma:7b", "llama2", "mistral"])
        self.llm_model_combo.setEditable(True)
        llm_layout.addRow("LLM Model:", self.llm_model_combo)
        
        # API base URL
        self.api_base_edit = QLineEdit()
        self.api_base_edit.setPlaceholderText("http://localhost:11434")
        llm_layout.addRow("API Base URL:", self.api_base_edit)
        
        general_layout.addWidget(llm_group)
        
        # Add spacer
        general_layout.addStretch()
        
        # Visualization settings tab
        viz_tab = QWidget()
        viz_layout = QVBoxLayout(viz_tab)
        
        # Visualization settings group
        viz_group = QGroupBox("Visualization Settings")
        viz_form_layout = QFormLayout(viz_group)
        
        # Default visualization type
        self.viz_type_combo = QComboBox()
        self.viz_type_combo.addItems(["dependency_graph", "treemap", "dashboard"])
        viz_form_layout.addRow("Default Visualization:", self.viz_type_combo)
        
        # Default metric
        self.viz_metric_combo = QComboBox()
        self.viz_metric_combo.addItems(["size", "lines"])
        viz_form_layout.addRow("Default Treemap Metric:", self.viz_metric_combo)
        
        # Visualization caching
        self.viz_cache_check = QCheckBox()
        viz_form_layout.addRow("Cache Visualizations:", self.viz_cache_check)
        
        viz_layout.addWidget(viz_group)
        
        # Theme settings group
        theme_group = QGroupBox("Visualization Theme")
        theme_layout = QFormLayout(theme_group)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark", "blue", "green"])
        theme_layout.addRow("Color Theme:", self.theme_combo)
        
        # Node size slider
        self.node_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.node_size_slider.setRange(1, 10)
        self.node_size_slider.setValue(5)
        theme_layout.addRow("Node Size:", self.node_size_slider)
        
        # Font size slider
        self.font_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.font_size_slider.setRange(8, 24)
        self.font_size_slider.setValue(12)
        theme_layout.addRow("Font Size:", self.font_size_slider)
        
        viz_layout.addWidget(theme_group)
        
        # Add spacer
        viz_layout.addStretch()
        
        # Similarity settings tab
        similarity_tab = QWidget()
        similarity_layout = QVBoxLayout(similarity_tab)
        
        # Similarity settings group
        similarity_group = QGroupBox("Similarity Analysis Settings")
        similarity_form_layout = QFormLayout(similarity_group)
        
        # Min clone size
        self.clone_size_spin = QSpinBox()
        self.clone_size_spin.setRange(5, 100)
        similarity_form_layout.addRow("Default Min Clone Size:", self.clone_size_spin)
        
        # Min fragment count
        self.fragment_count_spin = QSpinBox()
        self.fragment_count_spin.setRange(2, 10)
        similarity_form_layout.addRow("Default Min Fragment Count:", self.fragment_count_spin)
        
        # Min token count
        self.token_count_spin = QSpinBox()
        self.token_count_spin.setRange(10, 100)
        similarity_form_layout.addRow("Default Min Token Count:", self.token_count_spin)
        
        # Generate suggestions
        self.suggestions_check = QCheckBox()
        similarity_form_layout.addRow("Generate Refactoring Suggestions:", self.suggestions_check)
        
        # Similarity caching
        self.similarity_cache_check = QCheckBox()
        similarity_form_layout.addRow("Cache Similarity Results:", self.similarity_cache_check)
        
        similarity_layout.addWidget(similarity_group)
        
        # Add spacer
        similarity_layout.addStretch()
        
        # Add all tabs
        settings_tabs.addTab(general_tab, "General")
        settings_tabs.addTab(viz_tab, "Visualization")
        settings_tabs.addTab(similarity_tab, "Similarity")
        
        # Add save/reset buttons
        button_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        self.apply_btn = QPushButton("Apply")
        self.apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_btn)
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def load_settings(self):
        """Load settings from QSettings"""
        # General settings
        self.format_combo.setCurrentText(self.settings.value("output_format", "json"))
        self.max_files_spin.setValue(int(self.settings.value("max_files", 1000)))
        self.max_size_spin.setValue(int(self.settings.value("max_file_size", 1024)))
        self.efficient_check.setChecked(self.settings.value("use_efficient_analyzer", "true") == "true")
        self.caching_check.setChecked(self.settings.value("enable_caching", "true") == "true")
        
        # Cache location
        cache_path = self.settings.value("cache_directory", 
                                       os.path.join(os.path.expanduser("~"), ".allseeingeye", "cache"))
        self.cache_path_edit.setText(cache_path)
        
        # LLM settings
        self.llm_check.setChecked(self.settings.value("enable_llm", "false") == "true")
        self.llm_provider_combo.setCurrentText(self.settings.value("llm_provider", "ollama"))
        self.llm_model_combo.setCurrentText(self.settings.value("llm_model", "gemma:7b"))
        self.api_base_edit.setText(self.settings.value("llm_api_base", "http://localhost:11434"))
        
        # Visualization settings
        self.viz_type_combo.setCurrentText(self.settings.value("default_viz_type", "dependency_graph"))
        self.viz_metric_combo.setCurrentText(self.settings.value("viz_metric", "size"))
        self.viz_cache_check.setChecked(self.settings.value("use_viz_cache", "true") == "true")
        self.theme_combo.setCurrentText(self.settings.value("viz_theme", "light"))
        self.node_size_slider.setValue(int(self.settings.value("node_size", 5)))
        self.font_size_slider.setValue(int(self.settings.value("font_size", 12)))
        
        # Similarity settings
        self.clone_size_spin.setValue(int(self.settings.value("min_clone_size", 20)))
        self.fragment_count_spin.setValue(int(self.settings.value("min_fragment_count", 2)))
        self.token_count_spin.setValue(int(self.settings.value("min_token_count", 20)))
        self.suggestions_check.setChecked(self.settings.value("generate_suggestions", "true") == "true")
        self.similarity_cache_check.setChecked(self.settings.value("similarity_use_cache", "true") == "true")
    
    def apply_settings(self):
        """Apply settings without saving"""
        # Update parent if available
        if self.parent and hasattr(self.parent, 'analysis_tab'):
            self.parent.analysis_tab.format_combo.setCurrentText(self.format_combo.currentText())
            self.parent.analysis_tab.max_files_spin.setValue(self.max_files_spin.value())
            self.parent.analysis_tab.max_size_spin.setValue(self.max_size_spin.value())
            self.parent.analysis_tab.efficient_check.setChecked(self.efficient_check.isChecked())
        
        if self.parent and hasattr(self.parent, 'visualization_tab'):
            self.parent.visualization_tab.metric_combo.setCurrentText(self.viz_metric_combo.currentText())
            self.parent.visualization_tab.use_cache_check.setChecked(self.viz_cache_check.isChecked())
            
            # Set visualization type
            viz_type = self.viz_type_combo.currentText()
            if viz_type == "dependency_graph":
                self.parent.visualization_tab.dep_graph_radio.setChecked(True)
            elif viz_type == "treemap":
                self.parent.visualization_tab.treemap_radio.setChecked(True)
            elif viz_type == "dashboard":
                self.parent.visualization_tab.dashboard_radio.setChecked(True)
        
        if self.parent and hasattr(self.parent, 'similarity_tab'):
            self.parent.similarity_tab.clone_size_spin.setValue(self.clone_size_spin.value())
            self.parent.similarity_tab.fragment_count_spin.setValue(self.fragment_count_spin.value())
            self.parent.similarity_tab.token_count_spin.setValue(self.token_count_spin.value())
            self.parent.similarity_tab.suggestions_check.setChecked(self.suggestions_check.isChecked())
            self.parent.similarity_tab.use_cache_check.setChecked(self.similarity_cache_check.isChecked())
        
        # Show success message
        QMessageBox.information(
            self,
            "Settings Applied",
            "Settings have been applied to the current session."
        )
    
    def save_settings(self):
        """Save settings to QSettings"""
        # General settings
        self.settings.setValue("output_format", self.format_combo.currentText())
        self.settings.setValue("max_files", self.max_files_spin.value())
        self.settings.setValue("max_file_size", self.max_size_spin.value())
        self.settings.setValue("use_efficient_analyzer", self.efficient_check.isChecked())
        self.settings.setValue("enable_caching", self.caching_check.isChecked())
        self.settings.setValue("cache_directory", self.cache_path_edit.text())
        
        # LLM settings
        self.settings.setValue("enable_llm", self.llm_check.isChecked())
        self.settings.setValue("llm_provider", self.llm_provider_combo.currentText())
        self.settings.setValue("llm_model", self.llm_model_combo.currentText())
        self.settings.setValue("llm_api_base", self.api_base_edit.text())
        
        # Visualization settings
        self.settings.setValue("default_viz_type", self.viz_type_combo.currentText())
        self.settings.setValue("viz_metric", self.viz_metric_combo.currentText())
        self.settings.setValue("use_viz_cache", self.viz_cache_check.isChecked())
        self.settings.setValue("viz_theme", self.theme_combo.currentText())
        self.settings.setValue("node_size", self.node_size_slider.value())
        self.settings.setValue("font_size", self.font_size_slider.value())
        
        # Similarity settings
        self.settings.setValue("min_clone_size", self.clone_size_spin.value())
        self.settings.setValue("min_fragment_count", self.fragment_count_spin.value())
        self.settings.setValue("min_token_count", self.token_count_spin.value())
        self.settings.setValue("generate_suggestions", self.suggestions_check.isChecked())
        self.settings.setValue("similarity_use_cache", self.similarity_cache_check.isChecked())
        
        # Apply settings
        self.apply_settings()
        
        # Show success message
        QMessageBox.information(
            self,
            "Settings Saved",
            "Settings have been saved and will be applied to future sessions."
        )
    
    def reset_settings(self):
        """Reset settings to defaults"""
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset all settings
            self.settings.clear()
            
            # Reload with defaults
            self.load_settings()
            
            # Show success message
            QMessageBox.information(
                self,
                "Settings Reset",
                "All settings have been reset to their default values."
            )
    
    def browse_cache_directory(self):
        """Open directory selection dialog for cache location"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Cache Directory",
            self.cache_path_edit.text() or str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            self.cache_path_edit.setText(directory)
