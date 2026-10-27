import pytest
from unittest.mock import patch, mock_open
from src.core.file_processor import FileProcessor

def test_format_size():
    processor = FileProcessor()
    assert processor.format_size(0) == "0.00 B"
    assert processor.format_size(500) == "500.00 B"
    assert processor.format_size(1024) == "1.00 KB"
    assert processor.format_size(1536) == "1.50 KB"
    assert processor.format_size(1024 * 1024) == "1.00 MB"
    assert processor.format_size(1024 * 1024 * 1024) == "1.00 GB"
    assert processor.format_size(2 * 1024 * 1024 * 1024) == "2.00 GB"

def test_should_process_file():
    processor = FileProcessor(max_file_size=1024 * 1024) # 1 MB
    metadata_small = {
        "size": 500,
        "size_formatted": "500.00 B",
        "last_modified": "2023-01-01 12:00:00",
        "mime_type": "text/plain"
    }
    assert processor.should_process_file("test.txt", metadata_small) is True
    metadata_large = {
        "size": 2 * 1024 * 1024, # 2 MB
        "size_formatted": "2.00 MB",
        "last_modified": "2023-01-01 12:00:00",
        "mime_type": "text/plain"
    }
    assert processor.should_process_file("large.txt", metadata_large) is False
    metadata_binary = {
        "size": 500,
        "size_formatted": "500.00 B",
        "last_modified": "2023-01-01 12:00:00",
        "mime_type": "application/octet-stream"
    }
    assert processor.should_process_file("binary.bin", metadata_binary) is False

def test_get_file_metadata(tmp_path):
    processor = FileProcessor()
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")
    metadata = processor.get_file_metadata(str(test_file))
    assert metadata["size"] == 5
    assert metadata["mime_type"] == "text/plain"

def test_get_file_metadata_missing(tmp_path):
    processor = FileProcessor()
    missing_file = tmp_path / "missing.txt"
    with pytest.raises(OSError) as excinfo:
        processor.get_file_metadata(str(missing_file))
    assert "No such file or directory" in str(excinfo.value)

def test_get_file_category():
    processor = FileProcessor()
    assert processor.get_file_category("test.py") == "code"
    assert processor.get_file_category("README.md") == "documentation"

def test_process_file_security_failure(tmp_path):
    processor = FileProcessor(security_checks=True)
    # Simulate a path traversal path
    result = processor.process_file(f"{tmp_path}/../test.txt")
    assert "error" in result
    assert "Security validation failed" in result["error"]

def test_process_file_success(tmp_path):
    processor = FileProcessor(security_checks=True)
    test_file = tmp_path / "test.txt"
    test_file.write_text("safe content")
    result = processor.process_file(str(test_file))
    assert "error" not in result
    assert result["content"] == "safe content"
    assert result["line_count"] == 1
    assert result["size"] == 12

def test_process_file_with_emojis(tmp_path):
    processor = FileProcessor(security_checks=True)
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello 😊")
    result = processor.process_file(str(test_file))
    # Emojis are stripped, so the length or content changes depending on sanitize_emojis logic
    assert "error" not in result
    assert "security_warning" in result
    assert "Found and sanitized" in result["security_warning"]

@patch('builtins.open', new_callable=mock_open)
def test_process_file_read_error(mock_file, tmp_path):
    processor = FileProcessor(security_checks=False)
    mock_file.side_effect = PermissionError("Permission denied")
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")  # real write, mock is patched during open in process_file
    with patch('os.stat') as mock_stat, patch('mimetypes.guess_type') as mock_mime:
        class FakeStat:
            st_size = 5
            st_mtime = 1234567890
        mock_stat.return_value = FakeStat()
        mock_mime.return_value = ("text/plain", None)
        result = processor.process_file(str(test_file))
        assert "error" in result
        assert "Permission denied" in result["error"]

def test_list_directory_success(tmp_path):
    processor = FileProcessor(security_checks=True)
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    (test_dir / "file.txt").touch()
    entries = processor.list_directory(str(test_dir))
    assert "file.txt" in entries

def test_list_directory_security_failure(tmp_path):
    processor = FileProcessor(security_checks=True)
    # Using parent reference which fails validation
    entries = processor.list_directory(f"{tmp_path}/../some_dir")
    assert entries == []

def test_list_directory_missing_dir(tmp_path):
    processor = FileProcessor(security_checks=False)
    missing_dir = tmp_path / "missing_dir"
    entries = processor.list_directory(str(missing_dir))
    assert entries == []
