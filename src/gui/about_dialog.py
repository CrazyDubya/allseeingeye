#!/usr/bin/env python3
"""
About dialog for AllSeeingEye GUI
"""

import os
import sys
import platform
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QTextEdit, QWidget
)
from PyQt6.QtGui import QFont, QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize

class AboutDialog(QDialog):
    """About dialog showing application information"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About AllSeeingEye")
        self.setMinimumSize(600, 400)
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        layout = QVBoxLayout(self)
        
        # Header with title and version
        header_layout = QHBoxLayout()
        
        # Logo placeholder (would be replaced with an actual logo)
        logo_label = QLabel()
        logo_label.setFixedSize(QSize(64, 64))
        header_layout.addWidget(logo_label)
        
        # Title and version
        title_layout = QVBoxLayout()
        
        title_label = QLabel("AllSeeingEye")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_layout.addWidget(title_label)
        
        version_label = QLabel("Version 2.0")
        version_label.setFont(QFont("Arial", 10))
        title_layout.addWidget(version_label)
        
        description_label = QLabel("A powerful codebase analysis tool optimized for LLMs")
        title_layout.addWidget(description_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Tabs for different information
        tabs = QTabWidget()
        
        # About tab
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml("""
        <h3>About AllSeeingEye</h3>
        
        <p>AllSeeingEye is a powerful codebase analysis tool designed to provide comprehensive context to Large Language Models (LLMs) for code understanding and assistance.</p>
        
        <p>It analyzes directory structures, categorizes files, and generates detailed reports about your codebase that provide LLMs with the necessary context to understand your projects.</p>
        
        <h4>Key Features:</h4>
        <ul>
            <li>Smart file categorization for 25+ programming languages</li>
            <li>LLM-optimized output in multiple formats (Markdown, JSON, HTML, PDF)</li>
            <li>Interactive visualizations (dependency graphs, structure treemaps, metrics dashboards)</li>
            <li>Code similarity analysis with refactoring suggestions</li>
            <li>Intelligent codebase summary generation</li>
            <li>Cross-platform compatibility</li>
            <li>Customizable analysis parameters</li>
            <li>Security validation of files and content</li>
            <li>LLM integration for enhanced analysis</li>
        </ul>
        
        <p>AllSeeingEye helps developers and LLMs better understand codebases, find opportunities for improvement, and make sense of complex projects.</p>
        """)
        
        about_layout.addWidget(about_text)
        
        # System tab
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)
        
        system_text = QTextEdit()
        system_text.setReadOnly(True)
        
        # Get system information
        python_version = platform.python_version()
        qt_version = "6.x"  # Would be dynamically determined in a real implementation
        system_os = platform.system() + " " + platform.release()
        
        system_info = f"""
        <h3>System Information</h3>
        
        <table>
            <tr>
                <td><b>Python Version:</b></td>
                <td>{python_version}</td>
            </tr>
            <tr>
                <td><b>Qt Version:</b></td>
                <td>{qt_version}</td>
            </tr>
            <tr>
                <td><b>Operating System:</b></td>
                <td>{system_os}</td>
            </tr>
            <tr>
                <td><b>Platform:</b></td>
                <td>{platform.platform()}</td>
            </tr>
            <tr>
                <td><b>Architecture:</b></td>
                <td>{platform.architecture()[0]}</td>
            </tr>
        </table>
        
        <h3>Dependencies</h3>
        <ul>
            <li>PyQt6 - GUI framework</li>
            <li>NetworkX - Graph analysis</li>
            <li>PyVis - Visualization</li>
            <li>Jinja2 - HTML templating</li>
            <li>Ollama - LLM integration</li>
        </ul>
        """
        
        system_text.setHtml(system_info)
        system_layout.addWidget(system_text)
        
        # License tab
        license_tab = QWidget()
        license_layout = QVBoxLayout(license_tab)
        
        license_text = QTextEdit()
        license_text.setReadOnly(True)
        license_text.setHtml("""
        <h3>MIT License</h3>
        
        <p>Copyright (c) 2025 AllSeeingEye</p>
        
        <p>Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:</p>
        
        <p>The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.</p>
        
        <p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.</p>
        """)
        
        license_layout.addWidget(license_text)
        
        # Add tabs
        tabs.addTab(about_tab, "About")
        tabs.addTab(system_tab, "System Info")
        tabs.addTab(license_tab, "License")
        
        layout.addWidget(tabs)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
