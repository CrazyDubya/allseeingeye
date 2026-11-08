import pytest
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

    # Metadata for a small text file
    metadata_small = {
        "size": 500,
        "size_formatted": "500.00 B",
        "last_modified": "2023-01-01 12:00:00",
        "mime_type": "text/plain"
    }

    # Should process a small valid text file
    assert processor.should_process_file("test.txt", metadata_small) is True

    # Metadata for a large text file
    metadata_large = {
        "size": 2 * 1024 * 1024, # 2 MB
        "size_formatted": "2.00 MB",
        "last_modified": "2023-01-01 12:00:00",
        "mime_type": "text/plain"
    }

    # Should not process file exceeding max size
    assert processor.should_process_file("large.txt", metadata_large) is False

    # Metadata for a binary file
    metadata_binary = {
        "size": 500,
        "size_formatted": "500.00 B",
        "last_modified": "2023-01-01 12:00:00",
        "mime_type": "application/octet-stream"
    }

    # Should not process binary files
    assert processor.should_process_file("binary.bin", metadata_binary) is False

def test_process_file_redacts_unsafe_content(tmp_path):
    processor = FileProcessor(security_checks=True)

    # Create a dummy malicious file
    malicious_file = tmp_path / "malicious.py"
    # Three lines, so line count should be 3
    malicious_file.write_text("import os\nos.system('rm -rf /')\nprint('done')")

    result = processor.process_file(str(malicious_file))

    assert "security_warning" in result
    assert result["content"] == "[REDACTED FOR SECURITY]"
    # Ensure line count is preserved from the original content
    assert result["line_count"] == 3

def test_process_file_allows_safe_content(tmp_path):
    processor = FileProcessor(security_checks=True)

    safe_file = tmp_path / "safe.py"
    safe_file.write_text("print('Hello World')\nprint('Safe')")

    result = processor.process_file(str(safe_file))

    assert "security_warning" not in result
    assert result["content"] == "print('Hello World')\nprint('Safe')"
    assert result["line_count"] == 2
