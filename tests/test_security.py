import os
import pytest
from src.security.security_utils import SecurityUtils

def test_is_safe_file_content():
    # Safe content
    is_safe, msg = SecurityUtils.is_safe_file_content("This is a safe string.")
    assert is_safe is True

    # Malicious patterns
    is_safe, msg = SecurityUtils.is_safe_file_content("import os\nos.system('rm -rf /')")
    assert is_safe is False
    assert "Found potentially unsafe pattern" in msg

    is_safe, msg = SecurityUtils.is_safe_file_content("eval('print(1)')")
    assert is_safe is False
    assert "Found potentially unsafe pattern" in msg

    # Emoji content
    is_safe, msg = SecurityUtils.is_safe_file_content("Hidden emoji data 🤫")
    assert is_safe is False
    assert "Found and sanitized" in msg

def test_validate_path(tmp_path):
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    # Normal safe path
    safe_file = base_dir / "safe.txt"
    safe_file.touch()

    is_valid, msg = SecurityUtils.validate_path(str(safe_file), base_dir=str(base_dir))
    assert is_valid is True

    # Traversal attack
    # E.g. base_dir is /tmp/base
    # requested path is /tmp/base_hacked
    base_hacked = tmp_path / "base_hacked"
    base_hacked.mkdir()
    hacked_file = base_hacked / "hacked.txt"
    hacked_file.touch()

    is_valid, msg = SecurityUtils.validate_path(str(hacked_file), base_dir=str(base_dir))
    assert is_valid is False
    assert "outside the base directory" in msg

    # Typical directory traversal
    is_valid, msg = SecurityUtils.validate_path(str(base_dir / ".." / "base_hacked" / "hacked.txt"), base_dir=str(base_dir))
    assert is_valid is False
    assert "outside the base directory" in msg
