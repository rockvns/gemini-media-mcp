"""
MCP Tools for image generation, keyframe pair generation, and image editing.
"""

from typing import Optional, List
from config.constants import MODEL_SPECIFICATIONS
from config.preferences import PreferencesManager
from services.nano_banana_service import (
    generate_nano_banana_image,
    generate_keyframes_pair,
    edit_nano_banana_image,
)


def register_image_tools(mcp):
    """Register image and keyframe tools on the MCP server instance."""

    @mcp.tool()
    def generate_image(
        prompt: str,
        model: Optional[str] = None,
        character_paths: Optional[List[str]] = None,
        reference_image_paths: Optional[List[str]] = None,
        aspect_ratio: Optional[str] = None,
        image_size: Optional[str] = None,
        enable_google_search: Optional[bool] = None,
        output_path: Optional[str] = None,
        save_as_preference: bool = False
    ) -> str:
        """Generic image generation command using Gemini Nano Banana models.

        If model, aspect_ratio, or image_size are omitted, automatically uses your saved preferences.
        Set save_as_preference=True to update your defaults with the parameters provided.

        Available Models:
        - 'gemini-nano-banana-2.1' (Recommended): Primary high-efficiency model with search grounding & 1K/2K/4K.
        - 'gemini-3-pro-image': Premium choice for maximum knowledge, text rendering, and brand consistency.
        - 'gemini-3.1-flash-image': Balanced workhorse (supports 512px, 1K, 2K, 4K).
        - 'gemini-3.1-flash-lite-image': Fastest & cheapest (1K only).
        - 'gemini-2.5-flash-image': Legacy model.

        Supports attaching character reference images and object images to preserve identity.

        Args:
            prompt: Detailed description of the image.
            model: Gemini model identifier (defaults to saved preference).
            character_paths: Optional paths to character reference images (preserves character consistency).
            reference_image_paths: Optional paths to reference images (up to 14 total reference images).
            aspect_ratio: '1:1', '3:2', '2:3', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9' (defaults to saved preference).
            image_size: '1K', '2K', or '4K' (and '512px' on Flash, defaults to saved preference).
            enable_google_search: Grounding with Google Search for real-time facts/weather/data (defaults to saved preference).
            output_path: Optional destination .png path.
            save_as_preference: If True, saves these parameters as your default image preferences.
        """
        prefs = PreferencesManager.load()
        i_prefs = prefs.get("image", {})

        chosen_model = model or i_prefs.get("model", "gemini-nano-banana-2.1")
        chosen_aspect = aspect_ratio or i_prefs.get("aspect_ratio", "16:9")
        chosen_size = image_size or i_prefs.get("image_size", "2K")
        chosen_search = enable_google_search if enable_google_search is not None else i_prefs.get("enable_google_search", False)

        if save_as_preference:
            PreferencesManager.update(
                media_type="image",
                model=chosen_model,
                aspect_ratio=chosen_aspect,
                image_size=chosen_size,
                enable_google_search=chosen_search
            )

        if chosen_model not in MODEL_SPECIFICATIONS or MODEL_SPECIFICATIONS[chosen_model]["media_type"] != "image":
            return (
                f"Error: Unknown image model '{chosen_model}'.\n"
                f"Available Image Models:\n"
                f"- 'gemini-nano-banana-2.1' (Recommended)\n"
                f"- 'gemini-3-pro-image'\n"
                f"- 'gemini-3.1-flash-image'\n"
                f"- 'gemini-3.1-flash-lite-image'\n"
                f"Use 'get_model_specifications(model_name=\"{chosen_model}\")' to inspect capabilities."
            )

        return generate_nano_banana_image(
            prompt=prompt,
            model=chosen_model,
            character_paths=character_paths,
            reference_image_paths=reference_image_paths,
            aspect_ratio=chosen_aspect,
            image_size=chosen_size,
            enable_google_search=chosen_search,
            output_path=output_path,
        )

    @mcp.tool()
    def generate_keyframes(
        start_prompt: str,
        end_prompt: Optional[str] = None,
        num_frames: int = 1,
        character_paths: Optional[List[str]] = None,
        model: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        image_size: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """Generate keyframe images for video production. Supports 1-frame or 2-frame generation.

        Options available:
        - 1-Frame Option: Generates the opening keyframe (for image-to-video).
        - 2-Frames Option: Generates both start and end keyframes with character & environmental consistency using multi-turn generation (for video interpolation).

        Args:
            start_prompt: Description of opening keyframe / starting scene.
            end_prompt: Description of ending keyframe / final scene (triggers 2-frame generation).
            num_frames: 1 or 2 frames (automatically set to 2 if end_prompt is given).
            character_paths: Optional paths to character reference images.
            model: Nano Banana model identifier (defaults to saved preference).
            aspect_ratio: '16:9' or '9:16' (defaults to saved preference).
            image_size: '1K', '2K', or '4K' (defaults to saved preference).
            output_dir: Optional directory to save keyframes.
        """
        prefs = PreferencesManager.load()
        i_prefs = prefs.get("image", {})

        chosen_model = model or i_prefs.get("model", "gemini-nano-banana-2.1")
        chosen_aspect = aspect_ratio or i_prefs.get("aspect_ratio", "16:9")
        chosen_size = image_size or i_prefs.get("image_size", "2K")

        return generate_keyframes_pair(
            start_prompt=start_prompt,
            end_prompt=end_prompt,
            num_frames=num_frames,
            character_paths=character_paths,
            model=chosen_model,
            aspect_ratio=chosen_aspect,
            image_size=chosen_size,
            output_dir=output_dir,
        )

    @mcp.tool()
    def edit_image(
        prompt: str,
        image_path: str,
        model: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        image_size: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """Edit or modify an existing image conversationally using Gemini Nano Banana models.

        Args:
            prompt: Description of changes (add, remove, restyle, color grade).
            image_path: Path to the original image file.
            model: Nano Banana model identifier (defaults to saved preference).
            aspect_ratio: Optional target aspect ratio.
            image_size: Optional target size ('1K', '2K', '4K').
            output_path: Optional destination .png path.
        """
        prefs = PreferencesManager.load()
        chosen_model = model or prefs.get("image", {}).get("model", "gemini-nano-banana-2.1")

        return edit_nano_banana_image(
            prompt=prompt,
            image_path=image_path,
            model=chosen_model,
            aspect_ratio=aspect_ratio,
            image_size=image_size,
            output_path=output_path,
        )
