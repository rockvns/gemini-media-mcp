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

def _parse_error_details(err: Exception) -> Dict[str, Any]:
    """Extract structured error metadata from Google GenAI ClientError if available."""
    info: Dict[str, Any] = {
        "code": getattr(err, "code", None),
        "status": getattr(err, "status", None),
        "message": getattr(err, "message", str(err)),
        "retry_delay": None,
        "retry_in_text": None,
        "violations": [],
        "is_free_tier": False,
        "is_quota_zero": False,
    }

    # Extract retry delay from message text like 'Please retry in 14h32m17s'
    msg = info["message"] or ""
    import re
    retry_match = re.search(r"Please retry in ([^\.]+)", msg, re.IGNORECASE)
    if retry_match:
        info["retry_in_text"] = retry_match.group(1).strip()

    if "free_tier" in msg.lower() or "freetier" in msg.lower():
        info["is_free_tier"] = True
    if "limit: 0" in msg.lower() or "quota exceeded" in msg.lower():
        info["is_quota_zero"] = True

    # Parse details dictionary
    details_obj = getattr(err, "details", None)
    if isinstance(details_obj, dict):
        err_dict = details_obj.get("error", {})
        info["message"] = err_dict.get("message", info["message"])
        info["status"] = err_dict.get("status", info["status"])
        info["code"] = err_dict.get("code", info["code"])
        raw_details = err_dict.get("details", [])
        if isinstance(raw_details, list):
            for d in raw_details:
                if isinstance(d, dict):
                    dtype = d.get("@type", "")
                    if "RetryInfo" in dtype:
                        info["retry_delay"] = d.get("retryDelay")
                    elif "QuotaFailure" in dtype:
                        violations = d.get("violations", [])
                        info["violations"] = violations
                        for v in violations:
                            qid = str(v.get("quotaId", ""))
                            if "FreeTier" in qid:
                                info["is_free_tier"] = True

    return info


def format_api_error(err: Exception, context: str = "") -> str:
    """Format exceptions into human- and LLM-friendly diagnostic explanations without crashing."""
    err_str = str(err)
    err_type = type(err).__name__
    prefix = f"Error during {context}:\n" if context else "Error:\n"

    parsed = _parse_error_details(err)
    err_code = str(parsed.get("code") or "")
    err_status = str(parsed.get("status") or "")
    raw_message = parsed.get("message") or err_str

    # 1. API Key missing or default placeholder
    if isinstance(err, ValueError) and "GEMINI_API_KEY" in err_str:
        return (
            f"{prefix}[Authentication: Missing API Key]\n"
            f"- Details: {err_str}\n"
            f"- Action Required: Set your GEMINI_API_KEY in 'd:\\work\\MCP\\google-flow\\.env' or MCP configuration.\n"
            f"  Standard Google AI Studio API keys start with 'AIzaSy...'."
        )

    # 2. Quota Exceeded / Rate Limit (429 / RESOURCE_EXHAUSTED)
    if err_code == "429" or "429" in err_str or "RESOURCE_EXHAUSTED" in err_status or "quota" in err_str.lower():
        retry_time = parsed.get("retry_in_text")
        if not retry_time and parsed.get("retry_delay"):
            delay_sec = str(parsed.get("retry_delay")).rstrip("s")
            try:
                s = int(delay_sec)
                hours, rem = divmod(s, 3600)
                minutes, seconds = divmod(rem, 60)
                if hours > 0:
                    retry_time = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    retry_time = f"{minutes}m {seconds}s"
                else:
                    retry_time = f"{seconds}s"
            except Exception:
                retry_time = str(parsed.get("retry_delay"))

        # Check if this is a Free Tier limit (e.g. limit: 0 or daily quota exhaustion)
        if parsed.get("is_free_tier") or parsed.get("is_quota_zero") or "limit: 0" in raw_message:
            reset_msg = f"\n- Daily Quota Reset In: {retry_time}" if retry_time else ""
            return (
                f"{prefix}[429 RESOURCE_EXHAUSTED: Free Tier Quota Reached]\n"
                f"- Diagnosis: Your Google AI Studio API key is on the Free Tier, where generative media (image/video) quota is 0 or daily requests are exhausted.{reset_msg}\n"
                f"- Details: {raw_message.splitlines()[0] if raw_message else err_str}\n\n"
                f"How to resolve:\n"
                f"1. Enable Billing / Pay-As-You-Go in Google AI Studio:\n"
                f"   Go to https://aistudio.google.com/ -> Click on 'Get API key' / Project Settings -> Set up Pay-As-You-Go billing.\n"
                f"2. Generative media models (Gemini Image, Imagen, and Veo) require a billing-enabled Google Cloud project.\n"
                f"3. Once billing is enabled, update GEMINI_API_KEY in 'd:\\work\\MCP\\google-flow\\.env' and reload."
            )
        else:
            wait_msg = f"Wait {retry_time}" if retry_time else "Wait 30-60 seconds"
            return (
                f"{prefix}[429 TOO MANY REQUESTS: Rate Limit Exceeded]\n"
                f"- Diagnosis: You have exceeded the requests-per-minute (RPM) or tokens-per-minute (TPM) threshold.\n"
                f"- Recommended Action: {wait_msg} before sending the next generation request.\n"
                f"- Details: {raw_message.splitlines()[0] if raw_message else err_str}"
            )

    # 3. Authentication / Permission errors (401 / 403)
    if any(c in err_str for c in ["401", "403", "PERMISSION_DENIED", "UNAUTHENTICATED"]) or err_code in ["401", "403"]:
        return (
            f"{prefix}[Authentication / Permission Denied (HTTP {err_code or '401/403'})]\n"
            f"- Details: {raw_message.splitlines()[0] if raw_message else err_str}\n"
            f"- Possible Causes:\n"
            f"  1. The GEMINI_API_KEY configured is invalid, expired, or has a typo.\n"
            f"  2. The Google Cloud project does not have Generative Media APIs enabled.\n"
            f"- Action Required: Check your GEMINI_API_KEY in 'd:\\work\\MCP\\google-flow\\.env' or 'c:\\Users\\chand\\.gemini\\config\\mcp_config.json'."
        )

    # 4. Model Not Found / Unsupported (404 / NOT_FOUND)
    if any(c in err_str for c in ["404", "NOT_FOUND", "not found"]) or err_code == "404":
        return (
            f"{prefix}[Model Not Found or Unavailable (HTTP 404)]\n"
            f"- Details: {raw_message.splitlines()[0] if raw_message else err_str}\n"
            f"- Action Required: Call 'list_available_models' to inspect available models supported on your account tier."
        )

    # 5. Bad Request / Invalid Parameters (400 / INVALID_ARGUMENT)
    if any(c in err_str for c in ["400", "INVALID_ARGUMENT"]) or err_code == "400":
        return (
            f"{prefix}[Invalid Request Parameter (HTTP 400)]\n"
            f"- Details: {raw_message.splitlines()[0] if raw_message else err_str}\n"
            f"- Explanation: One or more parameters (aspect ratio, image size, resolution, or duration) are not accepted by this model.\n"
            f"- Action Required: Verify supported parameters via 'get_model_specifications(model_name=...)'."
        )

    # 6. Safety Filter / Content Policy Violation
    if any(term in err_str.lower() for term in ["safety", "blocked", "harm_category", "rai_filtered"]):
        return (
            f"{prefix}[Generation Blocked by Safety Filters]\n"
            f"- Details: {raw_message.splitlines()[0] if raw_message else err_str}\n"
            f"- Explanation: Google's safety filters flagged the prompt or reference image as potentially sensitive.\n"
            f"- Action Required: Adjust your prompt wording to avoid sensitive, violent, or trademarked terms."
        )

    # 7. Network Timeout / Connection Issues
    if any(term in err_str.lower() for term in ["timeout", "timed out", "deadline exceeded", "connection error"]):
        return (
            f"{prefix}[Network Timeout / Connection Error]\n"
            f"- Details: The request took longer than expected or was interrupted by network latency.\n"
            f"- Action Required: Verify your internet connection. For large 4K renders or video generation, use asynchronous mode ('wait_for_completion=False')."
        )

    # 8. File Not Found
    if isinstance(err, FileNotFoundError) or "No such file" in err_str:
        return (
            f"{prefix}[File Not Found]\n"
            f"- Details: {err_str}\n"
            f"- Action Required: Verify that reference or keyframe image paths exist and are accessible on disk."
        )

    # Generic catch-all
    return (
        f"{prefix}[Unexpected Error ({err_type})]\n"
        f"- Details: {err_str}\n"
        f"- Troubleshooting: Run 'check_api_status' to verify API key validity, output storage permissions, and active operations."
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
