"""
MCP Tools for user preferences and model specifications discovery.
"""

from typing import Optional
from config.constants import MODEL_SPECIFICATIONS
from config.preferences import PreferencesManager


def register_preference_tools(mcp):
    """Register preference and model catalog tools on the MCP server instance."""

    @mcp.tool()
    def get_user_preferences() -> str:
        """View current saved preferences for video and image generation."""
        return PreferencesManager.get_summary()

    @mcp.tool()
    def set_user_preferences(
        media_type: Optional[str] = None,
        model: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        image_size: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        enable_google_search: Optional[bool] = None,
        output_dir: Optional[str] = None,
    ) -> str:
        """Update and persist your default preferences for video, image generation, or output directory.

        Args:
            media_type: 'video' or 'image' (optional if only setting output_dir).
            model: Model code to set as default.
            aspect_ratio: Default aspect ratio ('16:9', '9:16', '1:1', etc.).
            resolution: Default video resolution ('720p', '1080p', '4k').
            image_size: Default image size ('1K', '2K', '4K', '512px').
            duration_seconds: Default video duration in seconds (e.g. 8).
            enable_google_search: Default search grounding for images (True/False).
            output_dir: Destination folder path for generated videos and images (persisted across sessions). Set to 'default' to clear.
        """
        return PreferencesManager.update(
            media_type=media_type,
            model=model,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            image_size=image_size,
            duration_seconds=duration_seconds,
            enable_google_search=enable_google_search,
            output_dir=output_dir,
        )

    @mcp.tool()
    def reset_user_preferences() -> str:
        """Reset user preferences back to the original recommended defaults."""
        return PreferencesManager.reset()

    @mcp.tool()
    def get_model_specifications(model_name: Optional[str] = None) -> str:
        """Get the supported video formats, resolutions, aspect ratios, and durations for a specific model or all models.

        Args:
            model_name: Optional model code (e.g. 'veo-3.1-generate-preview' or 'gemini-nano-banana-2.1'). If omitted, returns all.
        """
        if model_name:
            spec = MODEL_SPECIFICATIONS.get(model_name)
            if not spec:
                return f"Error: Unknown model '{model_name}'. Available: {list(MODEL_SPECIFICATIONS.keys())}"
            lines = [f"=== Specification for {spec['name']} ({model_name}) ==="]
            lines.append(f"Media Type: {spec['media_type'].upper()}")
            if spec["media_type"] == "video":
                lines.append(f"- Supported Resolutions: {', '.join(spec.get('supported_resolutions', []))}")
                lines.append(f"- Supported Aspect Ratios: {', '.join(spec.get('supported_aspect_ratios', []))}")
                lines.append(f"- Duration: {spec.get('default_duration_seconds', 8)}s (options: {spec.get('supported_durations', [])})")
                lines.append(f"- Supports Keyframes: {'Yes (0, 1, or 2 frames)' if spec.get('supports_keyframes') else 'No'}")
                lines.append(f"- Max Reference Images: {spec.get('max_reference_images', 0)}")
                lines.append(f"- Native Audio: {'Yes' if spec.get('native_audio') else 'No'}")
            else:
                lines.append(f"- Supported Sizes: {', '.join(spec.get('supported_sizes', []))}")
                lines.append(f"- Supported Aspect Ratios: {', '.join(spec.get('supported_aspect_ratios', []))}")
                lines.append(f"- Google Search Grounding: {'Yes' if spec.get('supports_google_search') else 'No'}")
                lines.append(f"- Max Reference Images: {spec.get('max_reference_images', 0)} (up to {spec.get('max_character_references', 0)} characters)")
            lines.append(f"Notes: {spec.get('notes', '')}")
            return "\n".join(lines)

        lines = ["=== Model Specifications & Capabilities Catalog ==="]
        for mid, spec in MODEL_SPECIFICATIONS.items():
            lines.append(f"\n[{spec['name']}] ({mid})")
            if spec["media_type"] == "video":
                lines.append(f"  Resolutions: {spec.get('supported_resolutions')} | Ratios: {spec.get('supported_aspect_ratios')} | Audio: {spec.get('native_audio')}")
            else:
                lines.append(f"  Sizes: {spec.get('supported_sizes')} | Search Grounding: {spec.get('supports_google_search')} | Max References: {spec.get('max_reference_images')}")
            lines.append(f"  Notes: {spec.get('notes')}")
        return "\n".join(lines)

    @mcp.tool()
    def list_available_models(media_type: str = "all") -> str:
        """List all available models for video and image generation along with descriptions and recommendations.

        Args:
            media_type: 'all', 'video', or 'image'.
        """
        output_lines = []

        if media_type in ["all", "video"]:
            output_lines.append("=== Available Video Models ===")
            for model_id, info in MODEL_SPECIFICATIONS.items():
                if info["media_type"] == "video":
                    rec = " (Recommended Default)" if model_id == "veo-3.1-generate-preview" else ""
                    output_lines.append(f"- {model_id}{rec}: {info['name']}")
                    output_lines.append(f"  Resolutions: {', '.join(info.get('supported_resolutions', []))} | Ratios: {', '.join(info.get('supported_aspect_ratios', []))}")
                    output_lines.append(f"  Details: {info.get('notes', '')}\n")

        if media_type in ["all", "image"]:
            output_lines.append("=== Available Image Models (Nano Banana) ===")
            for model_id, info in MODEL_SPECIFICATIONS.items():
                if info["media_type"] == "image":
                    rec = " (Recommended Default)" if model_id == "gemini-nano-banana-2.1" else ""
                    output_lines.append(f"- {model_id}{rec}: {info['name']}")
                    output_lines.append(f"  Sizes: {', '.join(info.get('supported_sizes', []))} | Search Grounding: {'Yes' if info.get('supports_google_search') else 'No'}")
                    output_lines.append(f"  Details: {info.get('notes', '')}\n")

        return "\n".join(output_lines)
