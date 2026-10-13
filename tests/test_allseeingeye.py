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
def test_output_format_markdown():
    from allseeingeye import OutputFormat
    stats = {
        'total_files': 10,
        'total_dirs': 2,
        'total_lines': 500,
        'total_size_formatted': '5.00 KB',
        'files_by_category': {'code': 8, 'data': 2}
    }

    md_output = OutputFormat.format_markdown(
        directory_structure="├── file.py",
        stats=stats,
        codebase_summary="Summary text."
    )

    assert "# Codebase Analysis" in md_output
    assert "Files analyzed: 10" in md_output
    assert "- code: 8 files" in md_output
    assert "Summary text." in md_output
    assert "├── file.py" in md_output

def test_output_format_json():
    from allseeingeye import OutputFormat
    stats = {
        'total_files': 10,
        'total_dirs': 2,
        'total_lines': 500,
        'total_size_formatted': '5.00 KB',
        'files_by_category': {'code': 8, 'data': 2}
    }

    json_output = OutputFormat.format_json(
        directory_structure="├── file.py",
        stats=stats,
        codebase_summary="Summary text."
    )

    parsed = json.loads(json_output)
    assert parsed["statistics"]["total_files"] == 10
    assert parsed["codebase_summary"] == "Summary text."
    assert parsed["directory_structure"] == "├── file.py"

def test_output_format_text():
    from allseeingeye import OutputFormat
    stats = {
        'total_files': 10,
        'total_dirs': 2,
        'total_lines': 500,
        'total_size_formatted': '5.00 KB',
        'files_by_category': {'code': 8, 'data': 2}
    }

    text_output = OutputFormat.format_text(
        directory_structure="├── file.py",
        stats=stats,
        codebase_summary="Summary text."
    )

    assert "CODEBASE ANALYSIS" in text_output
    assert "Files analyzed: 10" in text_output
    assert "Summary text." in text_output
    assert "├── file.py" in text_output

def test_allseeingeye_db_and_process_file(tmp_path):
    import sqlite3
    db_file = tmp_path / "test.db"
    ase = AllSeeingEye(directory=str(tmp_path))
    ase.db = MagicMock()

    # Create test file
    test_file = tmp_path / "code.py"
    test_file.write_text("print('hello')\n")

    # Test process_file
    with patch("src.llm.code_chunker.CodeChunker") as mock_chunker:
        mock_instance = MagicMock()
        mock_instance.chunk.return_value = ["chunk1"]
        mock_chunker.return_value = mock_instance
        ase.process_file(str(test_file))

    assert ase.db.insert_file.called
    assert ase.db.insert_chunk.called
    assert ase.stats["total_lines"] == 2

def test_allseeingeye_build_tree_recursive(tmp_path):
    # Setup directory structure
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir1" / "file1.txt").write_text("test")
    (tmp_path / "file2.py").write_text("print('test')")

    ase = AllSeeingEye(directory=str(tmp_path))
    ase.db = MagicMock()

    with patch("src.llm.code_chunker.CodeChunker"):
        tree_output = ase.build_tree()

    assert "dir1/" in tree_output
    assert "file1.txt" in tree_output
    assert "file2.py" in tree_output

    assert ase.stats["total_files"] == 2
    assert ase.stats["total_dirs"] == 1

@patch('src.visualization.codebase_structure.CodebaseStructure')
def test_generate_treemap_data(mock_codebase_structure, tmp_path):
    # Mock the visualizer
    mock_instance = MagicMock()
    mock_instance._build_real_treemap_data.return_value = {"name": "root", "children": []}
    mock_codebase_structure.return_value = mock_instance

    ase = AllSeeingEye(directory=str(tmp_path))
    result = ase.generate_treemap_data()

    assert mock_codebase_structure.called
    assert mock_instance._build_real_treemap_data.called
    assert result == {"name": "root", "children": []}

@patch('src.visualization.dependency_graph.DependencyGraph')
def test_generate_dependency_graph_data(mock_dependency_graph, tmp_path):
    # Mock the visualizer
    mock_instance = MagicMock()
    mock_instance._extract_dependencies.return_value = {"nodes": [], "links": []}
    mock_dependency_graph.return_value = mock_instance

    ase = AllSeeingEye(directory=str(tmp_path))
    result = ase.generate_dependency_graph_data()

    assert mock_dependency_graph.called
    assert mock_instance._extract_dependencies.called
    assert result == {"nodes": [], "links": []}

@patch('allseeingeye.get_llm_integration')
@patch('allseeingeye.PromptFormatter')
def test_llm_methods_summarize(mock_prompt, mock_get_llm, tmp_path):
    mock_llm = MagicMock()
    mock_llm.provider.generate.return_value = {"text": "This is a summary"}
    mock_llm.is_available.return_value = True
    mock_get_llm.return_value = mock_llm

    ase = AllSeeingEye(directory=str(tmp_path))
    ase.db = MagicMock()
    ase.db.get_all_chunks.return_value = [{"id": 1, "content": "test chunk"}]

    ase.summarize_files()

    assert mock_get_llm.called
    assert mock_prompt.format_summarization_prompt.called
    assert mock_llm.provider.generate.called

@patch('src.llm.embedding_generator.EmbeddingGenerator')
def test_build_rag_pipeline(mock_embedding, tmp_path):
    mock_embedder = MagicMock()
    mock_embedder.generate.return_value = [[0.1, 0.2]]
    mock_embedding.return_value = mock_embedder

    ase = AllSeeingEye(directory=str(tmp_path))

    ase.db = MagicMock()
    ase.db.get_all_chunks.return_value = [{"id": 1, "content": "chunk"}]

    ase.build_rag_pipeline()

    assert mock_embedding.called
    assert mock_embedder.generate.called
    assert ase.db.insert_embedding.called

@patch('sys.argv', ['allseeingeye.py', '-d', '/tmp', '-f', 'json', '--summarize'])
def test_parse_arguments():
    from allseeingeye import parse_arguments
    args = parse_arguments()
    assert args.directory == '/tmp'
    assert args.format == 'json'
    assert args.summarize is True

@patch('sys.argv', ['allseeingeye.py', '-d', '/tmp', '-f', 'json'])
@patch('allseeingeye.AllSeeingEye')
def test_main(mock_ase, tmp_path):
    from allseeingeye import main
    # Mock the instance returned by AllSeeingEye
    mock_instance = MagicMock()
    mock_ase.return_value = mock_instance

    # We should also patch os.path.isdir to return True so it doesn't fail the directory check
    with patch('os.path.isdir', return_value=True):
        main()

    assert mock_ase.called
    assert mock_instance.run.called
