"""
Constants and model specifications for Gemini & Veo media server.
"""

import sys
from pathlib import Path
from typing import Dict, Any

# When packaged as a frozen binary (e.g. PyInstaller), resolve paths relative to executable
if getattr(sys, "frozen", False):
    WORKSPACE_DIR = Path(sys.executable).resolve().parent
else:
    WORKSPACE_DIR = Path(__file__).resolve().parent.parent

OUTPUTS_DIR = WORKSPACE_DIR / "outputs"
PREFERENCES_FILE = WORKSPACE_DIR / "user_preferences.json"
ACTIVE_OPERATIONS_FILE = WORKSPACE_DIR / "active_operations.json"

# ==============================================================================
# MODEL SPECIFICATIONS CATALOG
# ==============================================================================

MODEL_SPECIFICATIONS: Dict[str, Dict[str, Any]] = {
    # Video Models
    "gemini-omni-1.1-flash": {
        "name": "Gemini Omni 1.1 Flash (Recommended Video)",
        "media_type": "video",
        "supported_resolutions": ["standard"],
        "supported_aspect_ratios": ["16:9"],
        "default_duration_seconds": 8,
        "supported_durations": [5, 8],
        "max_reference_images": 1,
        "supports_keyframes": False,
        "native_audio": True,
        "notes": "High-velocity multimodal conversational video generation via Interactions API."
    },
    "veo-3.1-generate-preview": {
        "name": "Veo 3.1",
        "media_type": "video",
        "supported_resolutions": ["720p", "1080p", "4k"],
        "supported_aspect_ratios": ["16:9", "9:16"],
        "default_duration_seconds": 8,
        "supported_durations": [8],
        "max_reference_images": 3,
        "supports_keyframes": True,
        "native_audio": True,
        "notes": "State-of-the-art 8-second video with native sound. Supports 0, 1, or 2 keyframes. 4k resolution has higher latency."
    },
    "veo-3.0-generate-001": {
        "name": "Veo 3.0",
        "media_type": "video",
        "supported_resolutions": ["720p", "1080p"],
        "supported_aspect_ratios": ["16:9"],
        "default_duration_seconds": 8,
        "supported_durations": [8],
        "max_reference_images": 1,
        "supports_keyframes": False,
        "native_audio": True,
        "notes": "Previous-generation standard Veo model."
    },
    "veo-3.0-fast-generate-001": {
        "name": "Veo 3.0 Fast",
        "media_type": "video",
        "supported_resolutions": ["720p"],
        "supported_aspect_ratios": ["16:9"],
        "default_duration_seconds": 8,
        "supported_durations": [8],
        "max_reference_images": 1,
        "supports_keyframes": False,
        "native_audio": True,
        "notes": "Optimized for velocity and rapid creative testing."
    },

    # Image Models (Nano Banana)
    "gemini-nano-banana-2.1": {
        "name": "Nano Banana 2.1 (Recommended Image)",
        "media_type": "image",
        "supported_sizes": ["1K", "2K", "4K"],
        "supported_aspect_ratios": ["1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        "supports_google_search": True,
        "max_reference_images": 14,
        "max_character_references": 4,
        "notes": "Primary high-efficiency model with Google Search/Image Search grounding, multi-turn consistency, and 4K."
    },
    "gemini-3-pro-image": {
        "name": "Nano Banana Pro",
        "media_type": "image",
        "supported_sizes": ["1K", "2K", "4K"],
        "supported_aspect_ratios": ["1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        "supports_google_search": True,
        "max_reference_images": 14,
        "max_character_references": 5,
        "notes": "Premium model for complex tasks, precise typography, brand consistency, and style references."
    },
    "gemini-3.1-flash-image": {
        "name": "Nano Banana 2 (Flash Image)",
        "media_type": "image",
        "supported_sizes": ["512px", "1K", "2K", "4K"],
        "supported_aspect_ratios": ["1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        "supports_google_search": True,
        "max_reference_images": 14,
        "max_character_references": 4,
        "notes": "Balanced workhorse supporting fast 512px preview through 4K."
    },
    "gemini-3.1-flash-lite-image": {
        "name": "Nano Banana 2 Lite",
        "media_type": "image",
        "supported_sizes": ["1K"],
        "supported_aspect_ratios": ["1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        "supports_google_search": False,
        "max_reference_images": 14,
        "max_character_references": 0,
        "notes": "Fastest and lowest-cost model. Fixed to 1K resolution, no search grounding."
    },
    "gemini-2.5-flash-image": {
        "name": "Nano Banana Legacy (Gemini 2.5)",
        "media_type": "image",
        "supported_sizes": ["1K"],
        "supported_aspect_ratios": ["1:1", "16:9", "9:16"],
        "supports_google_search": False,
        "max_reference_images": 4,
        "max_character_references": 1,
        "notes": "Legacy pioneer model."
    }
}

DEFAULT_PREFERENCES: Dict[str, Any] = {
    "output_dir": None,
    "video": None,
    "image": None,
}
