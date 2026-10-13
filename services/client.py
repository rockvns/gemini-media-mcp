"""
GenAI Client factory, path helper utilities, error formatting, and persistent operation tracking.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from google import genai

from config.constants import WORKSPACE_DIR, ACTIVE_OPERATIONS_FILE, OUTPUTS_DIR
from config.preferences import PreferencesManager

# Ensure .env is loaded
load_dotenv(dotenv_path=WORKSPACE_DIR / ".env")

# In-memory history tracking for recent session generations
GENERATED_HISTORY: List[Dict[str, Any]] = []


# ==============================================================================
# ERROR FORMATTING & RESILIENCE
# ==============================================================================

def format_api_error(err: Exception, context: str = "") -> str:
    """Format exceptions into human- and LLM-friendly diagnostic explanations without crashing."""
    err_str = str(err)
    err_type = type(err).__name__
    prefix = f"Error during {context}: " if context else "Error: "

    # 1. API Key missing or default placeholder
    if isinstance(err, ValueError) and "GEMINI_API_KEY" in err_str:
        return (
            f"{prefix}Invalid or missing Gemini API Key.\n"
            f"Details: {err_str}\n"
            f"Action Required: Set your GEMINI_API_KEY in your environment or in d:\\work\\MCP\\google-flow\\.env.\n"
            f"Google AI Studio keys start with 'AIzaSy...'."
        )

    # 2. Authentication / Permission errors (401 / 403)
    if any(code in err_str for code in ["401", "403", "PERMISSION_DENIED", "UNAUTHENTICATED"]):
        return (
            f"{prefix}Authentication / Permission Denied (HTTP 401/403).\n"
            f"Details: {err_str}\n"
            f"Possible Causes:\n"
            f"1. The configured GEMINI_API_KEY is invalid, expired, or has a typo.\n"
            f"2. The API key does not have access permissions enabled for this generative media model in Google AI Studio / Google Cloud.\n"
            f"Action Required: Verify GEMINI_API_KEY in your MCP config (c:\\Users\\chand\\.gemini\\config\\mcp_config.json) or .env file."
        )

    # 3. Quota Exceeded / Rate Limit (429 / RESOURCE_EXHAUSTED)
    if any(code in err_str for code in ["429", "RESOURCE_EXHAUSTED", "Quota", "quota"]):
        return (
            f"{prefix}API Quota / Rate Limit Exceeded (HTTP 429 / RESOURCE_EXHAUSTED).\n"
            f"Details: {err_str}\n"
            f"Explanation: You have reached the rate limit (RPM/TPM) for this generative model on your API tier.\n"
            f"Action Required:\n"
            f"- Wait 30-60 seconds before retrying.\n"
            f"- If generating video or 4K images continuously, space requests apart or request a quota tier increase in Google AI Studio / Cloud Console."
        )

    # 4. Model Not Found / Unsupported (404 / NOT_FOUND)
    if any(code in err_str for code in ["404", "NOT_FOUND", "not found"]):
        return (
            f"{prefix}Model Not Found or Unavailable (HTTP 404).\n"
            f"Details: {err_str}\n"
            f"Explanation: The requested model identifier is either unavailable on your account/region or requires private preview access.\n"
            f"Action Required: Call 'list_available_models' to inspect available models and their supported configurations."
        )

    # 5. Bad Request / Invalid Parameters (400 / INVALID_ARGUMENT)
    if any(code in err_str for code in ["400", "INVALID_ARGUMENT"]):
        return (
            f"{prefix}Invalid Request Parameter (HTTP 400).\n"
            f"Details: {err_str}\n"
            f"Explanation: One or more parameters (aspect ratio, resolution, duration, or image format) are invalid for the chosen model.\n"
            f"Action Required: Inspect supported options via 'get_model_specifications(model_name=...)'."
        )

    # 6. Safety Filter / Content Policy Violation
    if any(term in err_str.lower() for term in ["safety", "blocked", "harm_category"]):
        return (
            f"{prefix}Generation Blocked by Safety Filters.\n"
            f"Details: {err_str}\n"
            f"Explanation: Google's generative safety filter flagged the prompt or reference image as potentially sensitive or violating safety guidelines.\n"
            f"Action Required: Modify the prompt wording to avoid sensitive, violent, or copyrighted concepts."
        )

    # 7. File not found
    if isinstance(err, FileNotFoundError) or "No such file" in err_str:
        return (
            f"{prefix}Required file not found.\n"
            f"Details: {err_str}\n"
            f"Action Required: Verify that reference or keyframe image paths exist and are accessible."
        )

    # Generic catch-all
    return (
        f"{prefix}An unexpected error occurred ({err_type}).\n"
        f"Details: {err_str}\n"
        f"Troubleshooting: Use 'check_api_status' to verify connectivity and configuration."
    )


# ==============================================================================
# PERSISTENT OPERATIONS TRACKER
# ==============================================================================

class ActiveOperationsManager:
    """Disk-backed storage and lifecycle tracker for asynchronous media operations."""

    @classmethod
    def _load_all(cls) -> Dict[str, Dict[str, Any]]:
        if ACTIVE_OPERATIONS_FILE.exists():
            try:
                with open(ACTIVE_OPERATIONS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    @classmethod
    def _save_all(cls, ops: Dict[str, Dict[str, Any]]) -> None:
        try:
            with open(ACTIVE_OPERATIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(ops, f, indent=2)
        except Exception:
            pass

    @classmethod
    def register(
        cls,
        operation_name: str,
        media_type: str,
        model: str,
        prompt: str,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register a new long-running generation operation."""
        ops = cls._load_all()
        now_iso = datetime.now().isoformat()
        entry = {
            "operation_name": operation_name,
            "media_type": media_type,
            "model": model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "status": "IN_PROGRESS",
            "created_at": now_iso,
            "updated_at": now_iso,
            "output_path": output_path,
            "error": None,
        }
        ops[operation_name] = entry
        cls._save_all(ops)
        return entry

    @classmethod
    def update(
        cls,
        operation_name: str,
        status: str,
        output_path: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update the status of an existing operation."""
        ops = cls._load_all()
        if operation_name in ops:
            ops[operation_name]["status"] = status
            ops[operation_name]["updated_at"] = datetime.now().isoformat()
            if output_path:
                ops[operation_name]["output_path"] = str(output_path)
            if error:
                ops[operation_name]["error"] = str(error)
            cls._save_all(ops)
            return ops[operation_name]
        return None

    @classmethod
    def get(cls, operation_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific operation by identifier."""
        return cls._load_all().get(operation_name)

    @classmethod
    def list(cls, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all tracked operations, optionally filtered by status ('IN_PROGRESS', 'COMPLETED', 'FAILED')."""
        ops = cls._load_all()
        result = list(ops.values())
        if status_filter:
            result = [op for op in result if op.get("status", "").upper() == status_filter.upper()]
        return sorted(result, key=lambda x: x.get("created_at", ""), reverse=True)


# ==============================================================================
# CLIENT FACTORY & FILE HELPERS
# ==============================================================================

def get_genai_client() -> genai.Client:
    """Initialize and return the Google GenAI client using GEMINI_API_KEY."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "gemini-api-key":
        raise ValueError(
            "GEMINI_API_KEY is not set or contains the default placeholder. "
            "Please configure your real Gemini API key in your environment or d:\\work\\MCP\\google-flow\\.env"
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
