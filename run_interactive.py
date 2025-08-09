#!/usr/bin/env python3
"""
Web server for running the AllSeeingEye interactive report.
"""

from flask import Flask, render_template_string, request, jsonify
from allseeingeye import AllSeeingEye
import os

app = Flask(__name__)
eye = None

@app.route('/')
def index():
    global eye
    if eye is None:
        return "Please run the analysis first."

    # Read the template file
    template_path = os.path.join(os.path.dirname(__file__), 'src', 'formatters', 'exporters', 'templates', 'interactive_html_template.html')
    with open(template_path, 'r') as f:
        template = f.read()

    # Prepare data for embedding in the template
    import json
    json_data = json.dumps(eye.results)

    # Replace placeholder with data
    output_content = template.replace('__DATA__', json_data)
    return output_content

@app.route('/query', methods=['POST'])
def query():
    global eye
    if eye is None:
        return jsonify({"error": "Analysis not run."}), 500

    data = request.get_json()
    query = data.get('query')
    if not query:
        return jsonify({"error": "No query provided."}), 400

    answer = eye.query_rag_pipeline(query)
    return jsonify({"answer": answer})

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="AllSeeingEye Interactive Report Server")
    parser.add_argument("--directory", "-d", help="Directory to scan (default: current directory)")
    args = parser.parse_args()

    # Initialize and run AllSeeingEye
    eye = AllSeeingEye(
        directory=args.directory,
    )
    eye.analyze(summarize=True, build_rag=True)

    app.run(debug=True)
