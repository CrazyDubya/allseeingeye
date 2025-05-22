# AllSeeingEye Web Application

A modern Flask-based web interface for the AllSeeingEye codebase analysis tool.

## Features

- **Modern Web Interface**: Bootstrap-based responsive design
- **Directory Analysis**: Analyze local project directories
- **Archive Upload**: Upload and analyze project archives (.zip, .tar, etc.)
- **Visualization**: Interactive codebase visualizations including:
  - Dependency graphs
  - Codebase structure treemaps
  - Metrics dashboards
- **Similarity Analysis**: Detect code similarity and get refactoring suggestions
- **Multiple Output Formats**: Export results in Markdown, JSON, HTML, or plain text
- **REST API**: Programmatic access to all analysis features

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Run the web application:

```bash
python run_web.py
```

By default, the application will run on http://127.0.0.1:5000.

## Command Line Options

The `run_web.py` script accepts the following options:

- `--host`: Host address to bind to (default: 127.0.0.1)
- `--port`: Port to run on (default: 5000)
- `--debug`: Run in debug mode
- `--upload-dir`: Directory to store uploads (default: /tmp/allseeingeye_uploads)

Example:

```bash
python run_web.py --host 0.0.0.0 --port 8080 --debug --upload-dir /path/to/uploads
```

## API Usage

The web application provides a REST API for programmatic access:

### Directory Analysis

```
POST /api/analyze
Content-Type: application/json

{
  "directory": "/path/to/project",
  "exclude_dirs": ["node_modules", "venv"],
  "exclude_files": ["*.pyc", "*.log"],
  "output_format": "json",
  "include_visualizations": true,
  "include_similarity": true
}
```

Response:

```json
{
  "success": true,
  "results": { ... },
  "visualizations": [ ... ],
  "similarity_results": [ ... ]
}
```

## Directory Structure

```
allseeingeye/
├── app.py                 # Main Flask application
├── run_web.py             # Web application launcher
├── static/                # Static assets
│   ├── css/
│   │   └── style.css      # Custom styles
│   └── js/
│       └── main.js        # Custom JavaScript
├── templates/             # HTML templates
│   ├── base.html          # Base template
│   ├── index.html         # Homepage
│   └── results.html       # Results page
└── utils/                 # Utility functions
    ├── __init__.py
    └── archive_handler.py # Archive extraction utilities
```

## Security Considerations

- The application implements secure archive extraction to prevent path traversal attacks
- Temporary files are automatically cleaned up
- File upload size is limited to 50MB by default
- Input validation is performed on all form submissions
- User-submitted content is properly escaped

## Future Improvements

- Authentication for API access
- Persistent storage of analysis results
- Export to additional formats (PDF, etc.)
- Real-time analysis progress updates
- Custom visualization options