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

    # Path with symlink traversal should fail
    symlink_path = base_dir / "symlink_to_sibling"
    try:
        os.symlink(str(sibling_dir), str(symlink_path))
        is_valid, err = SecurityUtils.validate_path(str(symlink_path / "test.txt"), str(base_dir))
        assert is_valid is False
        assert "is outside the base directory" in err
    except OSError:
        # Skip if running in environment where symlink creation is not permitted
        pass

def test_validate_path_symlink_traversal(tmp_path):
    """Test that validate_path rejects a symlinked file that resolves outside base_dir."""
    base_dir = tmp_path / "app" / "base"
    base_dir.mkdir(parents=True, exist_ok=True)
    sensitive_file = tmp_path / "sensitive.txt"
    sensitive_file.write_text("secret")
    symlink_file = base_dir / "link.txt"
    os.symlink(str(sensitive_file), str(symlink_file))
    is_valid, err = SecurityUtils.validate_path(str(symlink_file), str(base_dir))
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

    # Malicious os.system pattern with bypass (spaces)
    is_safe, msg = SecurityUtils.is_safe_file_content("import os; os . system('rm -rf /')")
    assert is_safe is False
    assert "Found potentially unsafe pattern" in msg

    # Malicious subprocess pattern with bypass (spaces)
    is_safe, msg = SecurityUtils.is_safe_file_content("import subprocess; subprocess . Popen(['ls'])")
    assert is_safe is False
    assert "Found potentially unsafe pattern" in msg

    # Multiline evasion pattern (shell commands)
    is_safe, msg = SecurityUtils.is_safe_file_content("`\nrm -rf /\n`")
    assert is_safe is False
    assert "Found potentially unsafe pattern" in msg

    # Multiline evasion pattern (script tags)
    is_safe, msg = SecurityUtils.is_safe_file_content("<script>\nalert(1);\n</script>")
    assert is_safe is False
    assert "Found potentially unsafe pattern" in msg

def test_is_safe_file_content_hidden_emojis():
    """Test that is_safe_file_content correctly detects and rejects text with emojis."""
    # With emoji
    is_safe, msg = SecurityUtils.is_safe_file_content("Hello 😊, how are you?")
    assert is_safe is False
    assert "Found and sanitized" in msg and "emojis that might contain hidden data" in msg

def test_sanitize_filename():
    """Test that sanitize_filename correctly sanitizes various filenames."""
    assert SecurityUtils.sanitize_filename("normal_file.txt") == "normal_file.txt"
    assert SecurityUtils.sanitize_filename("file with spaces.txt") == "file_with_spaces.txt"
    assert SecurityUtils.sanitize_filename("-dash_at_start.txt") == "_dash_at_start.txt"
    assert SecurityUtils.sanitize_filename("CON.txt") == "_CON.txt"
    assert SecurityUtils.sanitize_filename("PRN.txt") == "_PRN.txt"
    assert SecurityUtils.sanitize_filename("lpt1.log") == "_lpt1.log"
    assert SecurityUtils.sanitize_filename("../../../etc/passwd") == ".._.._.._etc_passwd"

def test_ensure_directory_is_safe(tmp_path):
    """Test ensure_directory_is_safe."""
    # Test valid directory
    safe_dir = tmp_path / "safe"
    safe_dir.mkdir()
    is_safe, msg = SecurityUtils.ensure_directory_is_safe(str(safe_dir))
    assert is_safe is True

    # Test non-existent directory
    missing_dir = tmp_path / "missing"
    is_safe, msg = SecurityUtils.ensure_directory_is_safe(str(missing_dir))
    assert is_safe is False
    assert "Path does not exist" in msg

    # Test file instead of directory
    a_file = tmp_path / "file.txt"
    a_file.touch()
    is_safe, msg = SecurityUtils.ensure_directory_is_safe(str(a_file))
    assert is_safe is False
    assert "Not a directory" in msg

def test_check_file_integrity(tmp_path):
    """Test check_file_integrity."""
    import hashlib
    test_file = tmp_path / "test.txt"
    content = b"hello world"
    test_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()

    # Correct hash
    is_valid, msg = SecurityUtils.check_file_integrity(str(test_file), expected_hash)
    assert is_valid is True

    # Incorrect hash
    is_valid, msg = SecurityUtils.check_file_integrity(str(test_file), "wrong_hash")
    assert is_valid is False

    # Missing file
    missing_file = tmp_path / "missing.txt"
    is_valid, msg = SecurityUtils.check_file_integrity(str(missing_file), expected_hash)
    assert is_valid is False

def test_sanitize_text():
    """Test text sanitization."""
    # Control characters
    assert SecurityUtils.sanitize_text("Hello\x00World") == "HelloWorld"

    # Emojis
    assert SecurityUtils.sanitize_text("Hello 🤫") == "Hello [EMOJI]"

    # Homoglyphs
    assert SecurityUtils.sanitize_text("p\u0430ssword") == "password"

    # Valid common text
    assert SecurityUtils.sanitize_text("Hello World!") == "Hello World!"

def test_validate_path_suspicious_patterns(tmp_path):
    """Test validate_path with suspicious paths."""
    base_dir = tmp_path / "app"
    base_dir.mkdir(exist_ok=True)

    # Needs to exist to pass the first check
    proc_file = tmp_path / "proc"
    proc_file.mkdir(exist_ok=True)
    proc_test = proc_file / "test"
    proc_test.touch()

    is_valid, msg = SecurityUtils.validate_path(str(proc_test))
    assert is_valid is False
    assert "suspicious component" in msg
import stat

import os
def test_ensure_directory_is_safe_permissions(tmp_path):
    """Test ensure_directory_is_safe with permissions."""
    safe_dir = tmp_path / "noperms"
    safe_dir.mkdir()

    # Needs to be a directory we cannot write to
    try:
        os.chmod(str(safe_dir), stat.S_IRUSR | stat.S_IXUSR) # Read and execute, no write
        is_safe, msg = SecurityUtils.ensure_directory_is_safe(str(safe_dir))
        assert is_safe is False
        assert "Insufficient permissions" in msg or "Error checking directory safety" in msg
    finally:
        os.chmod(str(safe_dir), stat.S_IRWXU)


def test_is_safe_file_content_too_large():
    # 10MB + 1 byte
    large_content = "a" * (10 * 1024 * 1024 + 1)
    is_safe, msg = SecurityUtils.is_safe_file_content(large_content)
    assert is_safe is False
    assert "too large" in msg

def test_is_safe_file_content_unusual_chars():
    unusual_content = "\u4e00" * 100
    is_safe, msg = SecurityUtils.is_safe_file_content(unusual_content)
    assert is_safe is False
    assert "unusual Unicode characters" in msg

def test_is_safe_file_content_obfuscated():
    # Long line
    long_line = "a" * 1000
    is_safe, msg = SecurityUtils.is_safe_file_content(long_line)
    assert is_safe is False
    assert "obfuscated" in msg

def test_check_file_integrity_no_expected_hash(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")
    is_valid, msg = SecurityUtils.check_file_integrity(str(test_file))
    assert is_valid is True
    assert "File hash:" in msg

def test_validate_path_empty():
    is_valid, msg = SecurityUtils.validate_path("")
    assert is_valid is False
    assert "cannot be empty" in msg
    is_valid, msg = SecurityUtils.validate_path(None)
    assert is_valid is False
    assert "cannot be empty" in msg

def test_is_safe_file_content_obfuscated_repetitive():
    # Repetitive pattern
    repetitive_content = "abc" * 50
    is_safe, msg = SecurityUtils.is_safe_file_content(repetitive_content)
    assert is_safe is False
    assert "obfuscated" in msg

def test_ensure_directory_is_safe_exception(monkeypatch, tmp_path):
    safe_dir = tmp_path / "except_dir"
    safe_dir.mkdir()
    def mock_listdir(*args, **kwargs):
        raise OSError("Mock error")
    import os
    monkeypatch.setattr(os, "listdir", mock_listdir)

    is_safe, msg = SecurityUtils.ensure_directory_is_safe(str(safe_dir))
    assert is_safe is False
    assert "Error checking directory safety: Mock error" in msg


def test_detect_obfuscation():
    # Long line without alphanumeric dominance
    # Normal text should return False
    normal_text = "a " * 50
    assert SecurityUtils._detect_obfuscation(normal_text) is False

    # Entropy check (simulate encryption)
    # This might be hard to guarantee, but we can try something with uniform distribution
    high_entropy = "".join(chr(i) for i in range(256))
    assert SecurityUtils._detect_obfuscation(high_entropy) is True

    # Low uniqueness ratio check
    # Let's make it have regular alphanumeric ratio (< 0.9) to pass that check
    repetitive_text = "a b c " * 50
    assert SecurityUtils._detect_obfuscation(repetitive_text) is True

    # High alphanumeric ratio check
    alphanum_text = "a" * 150
    assert SecurityUtils._detect_obfuscation(alphanum_text) is True

def test_validate_path_drive_letter(tmp_path, monkeypatch):
    # Only really triggers on Windows, but we can simulate value error from commonpath
    import os
    def mock_commonpath(*args, **kwargs):
        raise ValueError("Paths are on different drives")

    monkeypatch.setattr(os.path, "commonpath", mock_commonpath)

    is_valid, msg = SecurityUtils.validate_path(str(tmp_path), base_dir=str(tmp_path))
    assert is_valid is False
    assert "different drive" in msg

def test_validate_path_exception(monkeypatch):
    import os
    def mock_realpath(*args, **kwargs):
        raise Exception("Mock error")
    monkeypatch.setattr(os.path, "realpath", mock_realpath)
    is_valid, msg = SecurityUtils.validate_path("test")
    assert is_valid is False
    assert "Invalid path" in msg

def test_detect_obfuscation_entropy_exception(monkeypatch):
    def mock_log(*args, **kwargs):
        raise Exception("Mock log error")
    import math
    monkeypatch.setattr(math, "log", mock_log)

    # Needs to be > 100 chars to trigger entropy check
    content = "a" * 150
    # Because entropy check fails, it falls back to alphanumeric which will return True
    assert SecurityUtils._detect_obfuscation(content) is True
