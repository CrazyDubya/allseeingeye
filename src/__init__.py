"""
AllSeeingEye - Directory analyzer optimized for LLM understanding
"""

# Version information
__version__ = '2.0.0'

# Import core modules
from src.core.analyzer import Analyzer
from src.core.file_category import FileCategory

# Import formatters
from src.formatters.output_format import OutputFormat

# Import security tools
from src.security.security_utils import SecurityUtils

# Import performance-optimized modules
from src.performance.efficient_analyzer import EfficientAnalyzer
from src.performance.profiler import Profiler, profile

# Convenience function
def analyze_directory(directory=None, efficient=True, **kwargs):
    """
    Analyze a directory and return the output file path.
    
    Args:
        directory: Directory to analyze (default: current directory)
        efficient: Whether to use the efficient analyzer (default: True)
        **kwargs: Additional arguments to pass to the analyzer
        
    Returns:
        Path to the output file
    """
    if efficient:
        analyzer = EfficientAnalyzer(directory=directory, **kwargs)
    else:
        analyzer = Analyzer(directory=directory, **kwargs)
    return analyzer.run()
