#!/usr/bin/env python3
"""
PDF exporter for AllSeeingEye analysis results
"""

import os
import json
import logging
import datetime
import tempfile
from typing import Dict, Any, List, Optional

from .base_exporter import BaseExporter
from .html_exporter import HtmlExporter

# Try to import weasyprint
try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logging.warning("weasyprint not available. PDF export will use alternative method.")

class PdfExporter(BaseExporter):
    """Exporter for PDF format"""
    
    def __init__(self, 
                 theme: str = "default", 
                 template: Optional[str] = None,
                 include_structure: bool = False,
                 pdf_options: Optional[Dict[str, Any]] = None,
                 **kwargs):
        """
        Initialize the PDF exporter.
        
        Args:
            theme: Theme name
            template: Optional custom template path
            include_structure: Whether to include file structure
            pdf_options: Options for PDF generation
            **kwargs: Additional configuration options
        """
        super().__init__(theme, **kwargs)
        self.template_path = template
        self.include_structure = include_structure
        self.pdf_options = pdf_options or {}
    
    def get_file_extension(self) -> str:
        """
        Get the file extension for this exporter.
        
        Returns:
            File extension (with dot)
        """
        return ".pdf"
    
    def export(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Export analysis data to PDF.
        
        Args:
            data: Analysis data dictionary
            output_path: Path to write the output file
            
        Returns:
            Path to the exported file
        """
        # Ensure output directory exists
        self.ensure_output_directory(output_path)
        
        # Add file extension if not present
        if not output_path.endswith('.pdf'):
            output_path += '.pdf'
        
        if WEASYPRINT_AVAILABLE:
            return self._export_with_weasyprint(data, output_path)
        else:
            return self._export_alternative(data, output_path)
    
    def _export_with_weasyprint(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Export to PDF using WeasyPrint.
        
        Args:
            data: Analysis data dictionary
            output_path: Path to write the output file
            
        Returns:
            Path to the exported file
        """
        # Create a temporary HTML file
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
            html_path = tmp.name
        
        try:
            # Export to HTML first
            html_exporter = HtmlExporter(
                theme=self.theme,
                template=self.template_path,
                include_structure=self.include_structure
            )
            html_exporter.export(data, html_path)
            
            # Convert HTML to PDF
            html = weasyprint.HTML(filename=html_path)
            
            # Get PDF options
            css = self.pdf_options.get('css')
            presentational_hints = self.pdf_options.get('presentational_hints', True)
            optimize_size = self.pdf_options.get('optimize_size', ('images',))
            
            # Generate PDF
            pdf = html.write_pdf(
                stylesheets=css,
                presentational_hints=presentational_hints,
                optimize_size=optimize_size
            )
            
            # Save PDF to file
            with open(output_path, 'wb') as f:
                f.write(pdf)
            
            logging.info(f"Exported PDF report to: {output_path}")
            return output_path
            
        finally:
            # Clean up temporary file
            if os.path.exists(html_path):
                os.unlink(html_path)
    
    def _export_alternative(self, data: Dict[str, Any], output_path: str) -> str:
        """
        Alternative PDF export method when WeasyPrint is not available.
        Attempts to use other available libraries or falls back to HTML.
        
        Args:
            data: Analysis data dictionary
            output_path: Path to write the output file
            
        Returns:
            Path to the exported file
        """
        # Try to use pdfkit if available
        try:
            import pdfkit
            
            # Create a temporary HTML file
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
                html_path = tmp.name
            
            try:
                # Export to HTML first
                html_exporter = HtmlExporter(
                    theme=self.theme,
                    template=self.template_path,
                    include_structure=self.include_structure
                )
                html_exporter.export(data, html_path)
                
                # Convert HTML to PDF using pdfkit
                pdfkit.from_file(html_path, output_path)
                
                logging.info(f"Exported PDF report (via pdfkit) to: {output_path}")
                return output_path
                
            finally:
                # Clean up temporary file
                if os.path.exists(html_path):
                    os.unlink(html_path)
                    
        except ImportError:
            logging.warning("pdfkit not available. Falling back to HTML export.")
            
            # Fall back to HTML
            html_path = output_path.replace('.pdf', '.html')
            html_exporter = HtmlExporter(
                theme=self.theme,
                template=self.template_path,
                include_structure=self.include_structure
            )
            html_exporter.export(data, html_path)
            
            logging.warning(f"PDF export not available. Exported HTML report to: {html_path}")
            return html_path
