"""
Configuration package for Gemini & Veo Media MCP Server.
"""

from .constants import (
    WORKSPACE_DIR,
    OUTPUTS_DIR,
    PREFERENCES_FILE,
    MODEL_SPECIFICATIONS,
    DEFAULT_PREFERENCES,
)
from .preferences import PreferencesManager

__all__ = [
    "WORKSPACE_DIR",
    "OUTPUTS_DIR",
    "PREFERENCES_FILE",
    "MODEL_SPECIFICATIONS",
    "DEFAULT_PREFERENCES",
    "PreferencesManager",
]
