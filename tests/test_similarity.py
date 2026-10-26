import pytest
import os
import shutil
from src.similarity.code_similarity import CodeSimilarityAnalyzer, CodeSimilarity

@pytest.fixture
def dummy_codebase(tmp_path):
    """Create a temporary dummy codebase for testing."""
    code_dir = tmp_path / "src"
    code_dir.mkdir()

    # File 1
    file1 = code_dir / "file1.py"
    file1.write_text("""
def calculate_sum(a, b):
    # This is a test function
    result = a + b
    print(f"The result is {result}")
    return result
""")

    # File 2 (duplicate of file 1 but renamed)
    file2 = code_dir / "file2.py"
    file2.write_text("""
def compute_addition(x, y):
    # This is a test function
    result = x + y
    print(f"The result is {result}")
    return result
""")

    # File 3 (unique)
    file3 = code_dir / "file3.py"
    file3.write_text("""
def completely_unique_function():
    print("Nothing similar here")
    return True
""")

    return str(tmp_path)

def test_code_similarity_analyzer(dummy_codebase):
    """Test the core CodeSimilarityAnalyzer logic."""
    analyzer = CodeSimilarityAnalyzer(base_directory=dummy_codebase, min_clone_size=5)
    results = analyzer.analyze_codebase()

    assert "clone_groups" in results
    clone_groups = results["clone_groups"]
    assert len(clone_groups) >= 1

    # Check that file1.py and file2.py are in the clone group
    found_file1 = False
    found_file2 = False
    for group in clone_groups:
        for frag in group["fragments"]:
            if "file1.py" in frag["file_path"]:
                found_file1 = True
            elif "file2.py" in frag["file_path"]:
                found_file2 = True

    assert found_file1 and found_file2

def test_code_similarity_wrapper(dummy_codebase):
    """Test the CodeSimilarity wrapper."""
    wrapper = CodeSimilarity(base_directory=dummy_codebase, min_clone_size=5)
    results = wrapper.analyze()

    assert isinstance(results, list)
    assert len(results) >= 1

    # The wrapper results should be a list of dictionaries with specific keys
    first_result = results[0]
    assert "file1" in first_result
    assert "file2" in first_result
    assert "score" in first_result
    assert "refactoring_suggestion" in first_result
