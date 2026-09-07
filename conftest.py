"""Shared test fixtures and utilities."""
import sys
from pathlib import Path

# Ensure project root is on sys.path so `src.*` imports work
_project_root = str(Path(__file__).parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
