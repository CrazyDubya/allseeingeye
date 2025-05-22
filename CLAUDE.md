# AllSeeingEye Project Guide

## Commands
```bash
# Installation
pip install -r requirements.txt
pip install -e .  # Dev mode

# Running
allseeingeye --directory /path/to/project
python -m src.gui.main_window  # GUI

# Testing
pytest  # All tests
pytest tests/test_file.py  # Single file
pytest tests/test_file.py::TestClass::test_method  # Single test

# Code Quality
black .  # Format
isort .  # Sort imports
flake8  # Lint
mypy  # Type check
```

## Code Style
- **Imports**: Standard lib → Third-party → Local (alphabetized)
- **Formatting**: Black (88 chars), Google-style docstrings
- **Types**: Use typing annotations for all functions and complex structures
- **Naming**: PascalCase (classes), snake_case (functions/variables), UPPER_SNAKE_CASE (constants)
- **Error handling**: Specific exception types, context managers for resources