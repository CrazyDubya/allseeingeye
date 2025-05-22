# AllSeeingEye - Web Application

A powerful codebase analysis tool with a Flask-based web interface. This repository has been reorganized to focus on the web application functionality.

## Overview

AllSeeingEye analyzes directory structures, categorizes files, and generates comprehensive reports. The web interface provides an easy way to analyze local directories or upload project archives for analysis.

## Features

- Web-based interface for codebase analysis
- Support for local directory analysis and archive upload
- Multiple output formats (Markdown, JSON, HTML, plain text)
- Interactive visualizations (dependency graphs, treemaps, dashboards)
- Code similarity detection
- REST API for programmatic access

## Project Structure

The repository has been reorganized to focus on web functionality:

```
allseeingeye/
├── app.py                  # Flask web application
├── run_web.py              # Web server launcher
├── allseeingeye.py         # Core analysis engine
├── templates/              # Web templates
│   ├── base.html           # Base template
│   ├── index.html          # Home page
│   └── results.html        # Results page
├── static/                 # Static assets
│   ├── css/                # Stylesheets
│   └── js/                 # JavaScript files
├── src/                    # Core modules
│   ├── formatters/         # Output formatting
│   ├── visualization/      # Visualization tools
│   └── similarity/         # Code similarity analysis
├── utils/                  # Utility functions
├── requirements.txt        # Dependencies
└── WEB_README.md           # Detailed documentation
```

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the web application
python run_web.py
```

## Usage

1. Start the web server: `python run_web.py`
2. Open your browser to http://localhost:5000
3. Enter a directory path or upload an archive
4. View the analysis results

## API Access

The web application also provides a REST API for programmatic access:

```bash
# Example API call using curl
curl -X POST http://localhost:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"directory": "/path/to/project", "output_format": "json"}'
```

## Note on Legacy Code

All non-web components have been moved to the `old/` directory. This includes:
- GUI application code
- Command-line interface
- Editor extensions
- LLM integration modules
- Test suite

## Additional Documentation

For more detailed information, see:
- `WEB_README.md` - Comprehensive documentation of the web application
- `SECURITY.md` - Security considerations 
- `FIXES.md` - Recent bug fixes and improvements