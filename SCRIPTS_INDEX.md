# Script Descriptions

## allseeingeye.py
Purpose: Core directory analysis tool.
Responsibilities:
  - Categorizing files.
  - Formatting output (Markdown, JSON, text).
  - Building directory trees.
  - Processing file content and metadata.
  - Generating codebase summaries.
  - Providing a command-line interface for analysis.

## app.py
Purpose: Flask-based web interface for AllSeeingEye.
Responsibilities:
  - Providing a GUI for directory analysis and archive uploads.
  - Handling user input via web forms.
  - Displaying analysis results.
  - Integrating visualization and code similarity features.

## run_web.py
Purpose: Launcher for the Flask web application.
Responsibilities:
  - Configuring environment variables for Flask.
  - Running the Flask development server for `app.py`.

## src/api/api.py
Purpose: FastAPI-based REST API for AllSeeingEye.
Responsibilities:
  - Providing API endpoints for programmatic codebase analysis.
  - Handling directory analysis and file uploads via API.
  - Managing asynchronous analysis tasks.
  - Offering LLM integration (optional).
  - Supporting visualizations and code similarity analysis (optional).

## src/api/cli.py
Purpose: Command-line interface to launch the FastAPI server.
Responsibilities:
  - Parsing command-line arguments for server configuration (host, port, workers, etc.).
  - Running the Uvicorn server for `src/api/api.py`.

# Script Relationships

- `app.py` (Flask web app) uses `allseeingeye.py` as its core analysis engine to perform directory and code analysis when initiated by a user through the web interface.
- `run_web.py` is a launcher script specifically designed to start the `app.py` Flask application, setting up necessary configurations.
- `src/api/api.py` (FastAPI application) provides a RESTful API interface to the core functionalities offered by `allseeingeye.py`. It allows for programmatic access to the analysis capabilities.
- `src/api/cli.py` is the command-line interface used to launch the `src/api/api.py` FastAPI server, typically using Uvicorn.
- `allseeingeye.py` is the central script containing the primary logic for codebase analysis. It is utilized by both the web application (`app.py`) and the API (`src/api/api.py`) but can also be run as a standalone CLI tool.
