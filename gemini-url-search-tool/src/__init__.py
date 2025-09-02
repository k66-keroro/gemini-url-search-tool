"""
Gemini URL Search Tool - Source Package

This package contains all the source code for the Gemini URL Search Tool.
"""

import sys
from pathlib import Path

# Add project root to Python path for absolute imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))