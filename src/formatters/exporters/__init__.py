"""
Output format exporters for AllSeeingEye
"""

from .base_exporter import BaseExporter
from .html_exporter import HtmlExporter
from .pdf_exporter import PdfExporter
from .dashboard_exporter import DashboardExporter

__all__ = [
    'BaseExporter',
    'HtmlExporter',
    'PdfExporter',
    'DashboardExporter',
    'get_exporter'
]

def get_exporter(format_name, **kwargs):
    """
    Factory function to get an exporter instance by name.
    
    Args:
        format_name: Name of the format
        **kwargs: Additional arguments for the exporter
        
    Returns:
        BaseExporter instance
    """
    # Map format names to exporter classes
    exporters = {
        'html': HtmlExporter,
        'pdf': PdfExporter,
        'dashboard': DashboardExporter
    }
    
    # Get exporter class
    exporter_class = exporters.get(format_name.lower())
    if not exporter_class:
        raise ValueError(f"Unsupported export format: {format_name}")
    
    # Create exporter instance
    return exporter_class(**kwargs)
