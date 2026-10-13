"""
GenAI Client factory and path helper utilities.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from google import genai

from config.constants import WORKSPACE_DIR
from config.preferences import PreferencesManager

# Ensure .env is loaded
load_dotenv(dotenv_path=WORKSPACE_DIR / ".env")

# In-memory history tracking
GENERATED_HISTORY: List[Dict[str, Any]] = []


def get_genai_client() -> genai.Client:
    """Initialize and return the Google GenAI client using GEMINI_API_KEY."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "gemini-api-key":
        raise ValueError(
            "GEMINI_API_KEY is not set or contains the default placeholder. "
            "Please configure your real Gemini API key in d:\\work\\MCP\\google-flow\\.env"
        )
    return genai.Client(api_key=api_key)


def resolve_file_path(path_str: str) -> Path:
    """Resolve file path relative to workspace directory if not absolute."""
    p = Path(path_str)
    if not p.is_absolute():
        p = WORKSPACE_DIR / p
    return p


def resolve_output_path(output_path: Optional[str], default_prefix: str, extension: str) -> Path:
    """Resolve destination file path:
    - If output_path is provided:
        * If absolute: respects it directly.
        * If relative: resolves relative to effective output directory.
    - If output_path is None:
        * Resolves timestamped filename in effective output directory.

    Effective output directory order of precedence:
    1. user_preferences.json ('output_dir')
    2. .env (MEDIA_OUTPUT_DIR or OUTPUT_DIR)
    3. Default workspace 'outputs/' folder
    """
    effective_dir = PreferencesManager.get_effective_output_dir()

    if output_path:
        p = Path(output_path)
        if not p.is_absolute():
            p = effective_dir / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    effective_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return effective_dir / f"{default_prefix}_{timestamp}.{extension}"


def detect_mime_type(file_path: Path) -> str:
    """Detect image MIME type from file suffix."""
    suffix = file_path.suffix.lower()
    if suffix in [".jpg", ".jpeg"]:
        return "image/jpeg"
    elif suffix == ".webp":
        return "image/webp"
    return "image/png"
