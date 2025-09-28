#!/usr/bin/env python3
"""
Interactive HTML exporter for AllSeeingEye.
"""

import os
import json
from .base_exporter import BaseExporter

class InteractiveHTMLExporter(BaseExporter):
    """Exports analysis results to an interactive HTML file."""

    def export(self, data: dict, output_path: str) -> None:
        """
        Exports the analysis data to an interactive HTML file.

        Args:
            data (dict): The analysis data.
            output_path (str): The path to the output HTML file.
        """
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'interactive_html_template.html')
        with open(template_path, 'r') as f:
            template = f.read()

        # Prepare data for embedding in the template
        json_data = json.dumps(data)

        # Replace placeholder with data
        output_content = template.replace('__DATA__', json_data)

        with open(output_path, 'w') as f:
            f.write(output_content)
