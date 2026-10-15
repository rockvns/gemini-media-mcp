"""
User Preferences persistence and management.
Supports persisting output_dir, video settings, and image settings.
Defaults are unset initially, prompting the LLM / user to configure them on first interaction.
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
        """Load user preferences from JSON, defaulting to unset."""
        if PREFERENCES_FILE.exists():
            try:
                with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {
                        "output_dir": data.get("output_dir", None),
                        "video": data.get("video") or dict(DEFAULT_PREFERENCES["video"]),
                        "image": data.get("image") or dict(DEFAULT_PREFERENCES["image"]),
                    }
            except Exception:
                pass
        return {
            "output_dir": None,
            "video": dict(DEFAULT_PREFERENCES["video"]),
            "image": dict(DEFAULT_PREFERENCES["image"]),
        }

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
        prefs = cls.load()
        pref_dir = prefs.get("output_dir")
        if pref_dir:
            p = Path(pref_dir)
            if not p.is_absolute():
                p = WORKSPACE_DIR / p
            p.mkdir(parents=True, exist_ok=True)
            return p

        env_dir = os.environ.get("MEDIA_OUTPUT_DIR") or os.environ.get("OUTPUT_DIR")
        if env_dir:
            p = Path(env_dir)
            if not p.is_absolute():
                p = WORKSPACE_DIR / p
            p.mkdir(parents=True, exist_ok=True)
            return p

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        return OUTPUTS_DIR

    @classmethod
    def get_summary(cls) -> str:
        """Return formatted human-readable summary of saved preferences and active output path."""
        prefs = cls.load()
        vp = prefs.get("video")
        ip = prefs.get("image")
        effective_out = cls.get_effective_output_dir()

        # Identify source of output dir
        if prefs.get("output_dir"):
            out_source = f"user_preferences.json ('{prefs['output_dir']}')"
        elif os.environ.get("MEDIA_OUTPUT_DIR") or os.environ.get("OUTPUT_DIR"):
            env_var = "MEDIA_OUTPUT_DIR" if os.environ.get("MEDIA_OUTPUT_DIR") else "OUTPUT_DIR"
            out_source = f".env ({env_var})"
        else:
            out_source = "default (./outputs)"

        if not vp:
            video_section = (
                "[Video Preferences]\n"
                "- Status: NOT CONFIGURED YET\n"
                "- Note: The LLM will ask you for your preferred model, resolution, and aspect ratio on first interaction,\n"
                "  or you can run 'set_user_preferences(media_type=\"video\", ...)'. (Default: gemini-omni-1.1-flash)"
            )
        else:
            video_section = (
                "[Video Preferences]\n"
                f"- Default Model: {vp.get('model', 'gemini-omni-1.1-flash')}\n"
                f"- Aspect Ratio: {vp.get('aspect_ratio', '16:9')}\n"
                f"- Resolution: {vp.get('resolution', 'standard')}\n"
                f"- Duration: {vp.get('duration_seconds', 8)} seconds"
            )

        if not ip:
            image_section = (
                "[Image Preferences]\n"
                "- Status: NOT CONFIGURED YET\n"
                "- Note: The LLM will ask you for your preferred image model and size on first interaction,\n"
                "  or you can run 'set_user_preferences(media_type=\"image\", ...)'."
            )
        else:
            image_section = (
                "[Image Preferences (Nano Banana)]\n"
                f"- Default Model: {ip.get('model', 'gemini-nano-banana-2.1')}\n"
                f"- Aspect Ratio: {ip.get('aspect_ratio', '16:9')}\n"
                f"- Resolution Size: {ip.get('image_size', '2K')}\n"
                f"- Google Search Grounding: {ip.get('enable_google_search', False)}"
            )

        return f"""=== Current User Preferences ===

[General & Storage]
- Effective Output Directory: {effective_out} (Source: {out_source})

{video_section}

{image_section}

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

        if output_dir is not None:
            if output_dir.strip() == "" or output_dir.lower() == "default":
                prefs["output_dir"] = None
            else:
                prefs["output_dir"] = output_dir.strip()

        m_type = media_type.lower().strip() if media_type else None

        if m_type == "video":
            if not prefs.get("video"):
                prefs["video"] = {
                    "model": "gemini-omni-1.1-flash",
                    "aspect_ratio": "16:9",
                    "resolution": "standard",
                    "duration_seconds": 8,
                }
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
            if not prefs.get("image"):
                prefs["image"] = {
                    "model": "gemini-nano-banana-2.1",
                    "aspect_ratio": "16:9",
                    "image_size": "2K",
                    "enable_google_search": False,
                }
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
        """Reset preferences back to unset defaults."""
        cls.save(DEFAULT_PREFERENCES)
        return "User preferences reset to unconfigured defaults.\n\n" + cls.get_summary()
