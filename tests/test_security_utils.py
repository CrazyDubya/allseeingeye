import os
import pytest
from src.security.security_utils import SecurityUtils

def test_validate_path_traversal(tmp_path):
    """Test that validate_path correctly prevents sibling traversal vulnerabilities."""
    # Create base directory and sibling directory
    base_dir = tmp_path / "app" / "data"
    sibling_dir = tmp_path / "app" / "data2"
    base_dir.mkdir(parents=True, exist_ok=True)
    sibling_dir.mkdir(parents=True, exist_ok=True)

    # Create a file in the sibling directory
    sibling_file = sibling_dir / "test.txt"
    sibling_file.write_text("hello")

    # Path inside base dir should pass
    inside_file = base_dir / "inside.txt"
    inside_file.write_text("hello inside")
    is_valid, _ = SecurityUtils.validate_path(str(inside_file), str(base_dir))
    assert is_valid is True

    # Path in sibling dir should fail traversal check
    # Without commonpath fix, startswith("/app/data") would match "/app/data2/test.txt"
    is_valid, err = SecurityUtils.validate_path(str(sibling_file), str(base_dir))
    assert is_valid is False
    assert "is outside the base directory" in err

def test_is_safe_file_content_malicious_patterns():
    """Test that is_safe_file_content correctly detects and rejects malicious patterns."""
    # Safe text
    is_safe, msg = SecurityUtils.is_safe_file_content("This is normal text with no issues.")
    assert is_safe is True
    assert msg == ""

    # Malicious eval pattern
    is_safe, msg = SecurityUtils.is_safe_file_content("result = eval('2 + 2')")
    assert is_safe is False
    assert "Found potentially unsafe pattern" in msg

    # Malicious os.system pattern
    is_safe, msg = SecurityUtils.is_safe_file_content("import os; os.system('rm -rf /')")
    assert is_safe is False
    assert "Found potentially unsafe pattern" in msg

def test_is_safe_file_content_hidden_emojis():
    """Test that is_safe_file_content correctly detects and rejects text with emojis."""
    # With emoji
    is_safe, msg = SecurityUtils.is_safe_file_content("Hello 😊, how are you?")
    assert is_safe is False
    assert "Found and sanitized" in msg and "emojis that might contain hidden data" in msg
