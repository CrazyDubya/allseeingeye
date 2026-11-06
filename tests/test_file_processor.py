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

def test_process_file_unsafe_content(tmp_path):
    processor = FileProcessor(max_file_size=1024 * 1024) # 1 MB

    # Create a temporary file with a malicious pattern
    test_file = tmp_path / "unsafe_script.py"
    unsafe_content = "import os\nos.system('echo malicious')\nprint('done')\n"
    test_file.write_text(unsafe_content)

    # Process the file
    result = processor.process_file(str(test_file))

    # The line count should still be calculated
    assert result["line_count"] == 4

    # Check if security warning is correctly populated
    assert "security_warning" in result
    assert "Found potentially unsafe pattern" in result["security_warning"]

    # Check if content was properly redacted
    assert result["content"] == "[CONTENT REDACTED DUE TO SECURITY WARNING]"
    assert "os.system" not in result["content"]
