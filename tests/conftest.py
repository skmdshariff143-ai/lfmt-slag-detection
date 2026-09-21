"""
Pytest configuration and pythonpath setup for lfmt-slag-detection test suite.
"""

import sys
from pathlib import Path

# Add repository root and src/ to sys.path for test discovery
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / "src"))
