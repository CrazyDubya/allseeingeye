import os
import json
import pytest
from unittest.mock import patch, MagicMock
from allseeingeye import AllSeeingEye, FileCategory, OutputFormat

def test_file_category_methods():
    assert ".py" in FileCategory.get_extensions_by_category("code")
    assert FileCategory.get_extensions_by_category("unknown_category") == []

    assert FileCategory.get_category_for_extension(".py") == "code"
    assert FileCategory.get_category_for_extension(".md") == "documentation"
    assert FileCategory.get_category_for_extension(".unknown") == "other"

    assert FileCategory.is_binary_mimetype("image/png") is True
    assert FileCategory.is_binary_mimetype("text/plain") is False
    assert FileCategory.is_binary_mimetype("application/json") is False
    assert FileCategory.is_binary_mimetype(None) is False

    assert FileCategory.is_text_category("code") is True
    assert FileCategory.is_text_category("data") is True
    assert FileCategory.is_text_category("documentation") is True
    assert FileCategory.is_text_category("configuration") is True
    assert FileCategory.is_text_category("media") is False
    assert FileCategory.is_text_category("binary") is False
    assert FileCategory.is_text_category("other") is False

def test_get_language_for_file():
    assert OutputFormat._get_language_for_file("test.py") == "python"
    assert OutputFormat._get_language_for_file("script.js") == "javascript"
    assert OutputFormat._get_language_for_file("styles.css") == "css"
    assert OutputFormat._get_language_for_file("unknown.ext") == ""

def test_allseeingeye_init(tmp_path):
    ase = AllSeeingEye(
        directory=str(tmp_path),
        excluded_dirs=['.git', 'node_modules'],
        excluded_files=['secret.txt'],
        included_categories=['code', 'data'],
        max_file_size=5000,
        max_files=50,
        output_format="json",
        verbose=True
    )

    assert ase.directory == str(tmp_path)
    assert '.git' in ase.excluded_dirs
    assert 'node_modules' in ase.excluded_dirs
    assert 'secret.txt' in ase.excluded_files

    assert 'code' in ase.included_categories
    assert 'data' in ase.included_categories
    assert 'documentation' not in ase.active_categories
    assert 'code' in ase.active_categories

    assert ase.max_file_size == 5000
    assert ase.max_files == 50
    assert ase.output_format == "json"

def test_format_size():
    ase = AllSeeingEye()
    assert ase._format_size(500) == "500.00 B"
    assert ase._format_size(1024) == "1.00 KB"
    assert ase._format_size(1024 * 1024) == "1.00 MB"
    assert ase._format_size(1024 * 1024 * 1024) == "1.00 GB"
    assert ase._format_size(1024 * 1024 * 1024 * 1024) == "1024.00 GB"

def test_get_file_metadata(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")

    ase = AllSeeingEye()
    metadata = ase.get_file_metadata(str(test_file))

    assert metadata["size"] == 11
    assert metadata["size_formatted"] == "11.00 B"
    assert "last_modified" in metadata
    assert metadata["mime_type"] == "text/plain"

def test_should_process_file():
    ase = AllSeeingEye(max_file_size=1000, included_categories=['code'])

    # Exceeds max file size
    assert not ase.should_process_file("large.py", {"size": 2000, "mime_type": "text/x-python", "size_formatted": "2 KB"})

    # Binary mime type
    assert not ase.should_process_file("image.png", {"size": 500, "mime_type": "image/png", "size_formatted": "500 B"})

    # Not in included categories (test.md is documentation, which is not in ['code'])
    assert not ase.should_process_file("test.md", {"size": 500, "mime_type": "text/markdown", "size_formatted": "500 B"})

    # Should process valid code file
    assert ase.should_process_file("script.py", {"size": 500, "mime_type": "text/x-python", "size_formatted": "500 B"})

def test_get_file_category():
    ase = AllSeeingEye()
    assert ase.get_file_category("script.py") == "code"
    assert ase.get_file_category("data.json") == "data"
    assert ase.get_file_category("image.png") == "media"
    assert ase.get_file_category("unknown.ext") == "other"

@patch('allseeingeye.AllSeeingEye.build_tree')
@patch('allseeingeye.AllSeeingEye.create_codebase_summary')
@patch('allseeingeye.AllSeeingEye.generate_dependency_graph_data')
@patch('allseeingeye.AllSeeingEye.generate_treemap_data')
def test_analyze(mock_treemap, mock_dep_graph, mock_summary, mock_tree, tmp_path):
    def fake_build_tree():
        ase.stats["total_size_formatted"] = "1.00 KB"
        ase.stats["duration"] = 0.5
        return "├── file.py"

    mock_tree.side_effect = fake_build_tree
    mock_summary.return_value = "Summary"
    mock_dep_graph.return_value = {}
    mock_treemap.return_value = {}

    ase = AllSeeingEye(directory=str(tmp_path))
    ase.analyze()

    assert ase.directory_structure == "├── file.py"
    assert ase.codebase_summary == "Summary"
    assert ase.results is not None

def test_create_codebase_summary(tmp_path):
    ase = AllSeeingEye(directory=str(tmp_path))
    ase.stats['files_by_category'] = {'code': 5, 'data': 2}
    ase.stats['total_files'] = 7
    ase.stats['total_lines'] = 100
    ase.stats['total_size'] = 1024

    summary = ase.create_codebase_summary()
    assert "This codebase contains:" in summary
    assert "- 5 Source code files" in summary
    assert "- 2 Data files" in summary
