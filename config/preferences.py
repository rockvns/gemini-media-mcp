"""
User Preferences persistence and management.
Supports persisting output_dir, video settings, and image settings.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from .constants import (
    WORKSPACE_DIR,
    OUTPUTS_DIR,
    PREFERENCES_FILE,
    DEFAULT_PREFERENCES,
    MODEL_SPECIFICATIONS,
)


class PreferencesManager:
    """Manages reading, writing, and validating user generation preferences."""

    @classmethod
    def load(cls) -> Dict[str, Any]:
        """Load user preferences from JSON, falling back to default."""
        if PREFERENCES_FILE.exists():
            try:
                with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    prefs = {
                        "output_dir": data.get("output_dir", DEFAULT_PREFERENCES["output_dir"]),
                        "video": DEFAULT_PREFERENCES["video"].copy(),
                        "image": DEFAULT_PREFERENCES["image"].copy()
                    }
                    if "video" in data:
                        prefs["video"].update(data["video"])
                    if "image" in data:
                        prefs["image"].update(data["image"])
                    return prefs
            except Exception:
                pass
        cls.save(DEFAULT_PREFERENCES)
        return DEFAULT_PREFERENCES.copy()

    @classmethod
    def save(cls, prefs: Dict[str, Any]) -> None:
        """Save preferences dictionary to disk."""
        with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
            json.dump(prefs, f, indent=2)

    @classmethod
    def get_effective_output_dir(cls) -> Path:
        """Resolve output directory by checking:
        1. user_preferences.json ('output_dir')
        2. Environment variables (MEDIA_OUTPUT_DIR or OUTPUT_DIR)
        3. Default WORKSPACE_DIR / 'outputs'
        """
        # 1. Check user preferences
        prefs = cls.load()
        pref_dir = prefs.get("output_dir")
        if pref_dir:
            p = Path(pref_dir)
            if not p.is_absolute():
                p = WORKSPACE_DIR / p
            p.mkdir(parents=True, exist_ok=True)
            return p

        # 2. Check environment variable
        env_dir = os.environ.get("MEDIA_OUTPUT_DIR") or os.environ.get("OUTPUT_DIR")
        if env_dir:
            p = Path(env_dir)
            if not p.is_absolute():
                p = WORKSPACE_DIR / p
            p.mkdir(parents=True, exist_ok=True)
            return p

        # 3. Default fallback
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        return OUTPUTS_DIR

    @classmethod
    def get_summary(cls) -> str:
        """Return formatted human-readable summary of saved preferences and active output path."""
        prefs = cls.load()
        vp = prefs.get("video", {})
        ip = prefs.get("image", {})
        effective_out = cls.get_effective_output_dir()

        # Identify source of output dir
        if prefs.get("output_dir"):
            out_source = f"user_preferences.json ('{prefs['output_dir']}')"
        elif os.environ.get("MEDIA_OUTPUT_DIR") or os.environ.get("OUTPUT_DIR"):
            env_var = "MEDIA_OUTPUT_DIR" if os.environ.get("MEDIA_OUTPUT_DIR") else "OUTPUT_DIR"
            out_source = f".env ({env_var})"
        else:
            out_source = "default (./outputs)"

        return f"""=== Current User Preferences ===

[General & Storage]
- Effective Output Directory: {effective_out} (Source: {out_source})

[Video Preferences]
- Default Model: {vp.get('model', 'veo-3.1-generate-preview')}
- Aspect Ratio: {vp.get('aspect_ratio', '16:9')}
- Resolution: {vp.get('resolution', '720p')}
- Duration: {vp.get('duration_seconds', 8)} seconds

[Image Preferences (Nano Banana)]
- Default Model: {ip.get('model', 'gemini-nano-banana-2.1')}
- Aspect Ratio: {ip.get('aspect_ratio', '16:9')}
- Resolution Size: {ip.get('image_size', '2K')}
- Google Search Grounding: {ip.get('enable_google_search', False)}

Preferences file: {PREFERENCES_FILE}"""

    @classmethod
    def update(
        cls,
        media_type: Optional[str] = None,
        model: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        image_size: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        enable_google_search: Optional[bool] = None,
        output_dir: Optional[str] = None,
    ) -> str:
        """Update preferences for video, image, or output directory."""
        prefs = cls.load()

        # Update output_dir if specified
        if output_dir is not None:
            if output_dir.strip() == "" or output_dir.lower() == "default":
                prefs["output_dir"] = None
            else:
                prefs["output_dir"] = output_dir.strip()

        m_type = media_type.lower().strip() if media_type else None

        if m_type == "video":
            target = prefs["video"]
            if model:
                if model not in MODEL_SPECIFICATIONS or MODEL_SPECIFICATIONS[model]["media_type"] != "video":
                    return f"Error: Unknown video model '{model}'."
                target["model"] = model
            if aspect_ratio:
                target["aspect_ratio"] = aspect_ratio
            if resolution:
                target["resolution"] = resolution
            if duration_seconds:
                target["duration_seconds"] = duration_seconds

        elif m_type == "image":
            target = prefs["image"]
            if model:
                if model not in MODEL_SPECIFICATIONS or MODEL_SPECIFICATIONS[model]["media_type"] != "image":
                    return f"Error: Unknown image model '{model}'."
                target["model"] = model
            if aspect_ratio:
                target["aspect_ratio"] = aspect_ratio
            if image_size or resolution:
                target["image_size"] = image_size or resolution
            if enable_google_search is not None:
                target["enable_google_search"] = enable_google_search

        cls.save(prefs)
        return "Preferences updated successfully!\n\n" + cls.get_summary()

    @classmethod
    def reset(cls) -> str:
        """Reset preferences back to recommended defaults."""
        cls.save(DEFAULT_PREFERENCES)
        return "User preferences reset to default recommendations.\n\n" + cls.get_summary()
