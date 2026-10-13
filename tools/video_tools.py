"""
MCP Tools for video generation (Veo 3.1 & Omni) with keyframe and preference integration.
"""

from typing import Optional, List
from config.constants import MODEL_SPECIFICATIONS
from config.preferences import PreferencesManager
from services.veo_service import generate_veo_video, check_veo_operation
from services.omni_service import generate_omni_video


def register_video_tools(mcp):
    """Register video tools on the MCP server instance."""

    @mcp.tool()
    def generate_video(
        prompt: str,
        model: Optional[str] = None,
        keyframe_paths: Optional[List[str]] = None,
        first_frame_path: Optional[str] = None,
        last_frame_path: Optional[str] = None,
        character_paths: Optional[List[str]] = None,
        aspect_ratio: Optional[str] = None,
        resolution: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        output_path: Optional[str] = None,
        save_as_preference: bool = False,
        wait_for_completion: bool = True,
        poll_interval_seconds: int = 10,
        max_wait_seconds: int = 360
    ) -> str:
        """Generic video generation command with model selection and preference persistence.

        If model, aspect_ratio, or resolution are omitted, automatically uses your saved preferences.
        Set save_as_preference=True to update your defaults with the parameters provided.

        Available Models:
        - 'veo-3.1-generate-preview' (Recommended): 8s video with sound, keyframe interpolation, 720p/1080p/4k, 16:9 & 9:16.
        - 'gemini-omni-1.1-flash': Ultra-fast multimodal video generation via Interactions API.
        - 'veo-3.0-generate-001': Standard Veo 3.0 model.
        - 'veo-3.0-fast-generate-001': Fast Veo 3.0 model.

        Keyframe Modes:
        - 0 Frames: Pure text-to-video.
        - 1 Frame: Animate starting from 'first_frame_path' (or keyframe_paths[0]).
        - 2 Frames: Smooth interpolation between 'first_frame_path' and 'last_frame_path'.

        Args:
            prompt: Scene, motion, lighting, and audio description.
            model: Video model code (defaults to saved user preference).
            keyframe_paths: Optional list containing 1 keyframe (start) or 2 keyframes (start + end).
            first_frame_path: Path to starting keyframe image.
            last_frame_path: Path to ending keyframe image (for 2-frame interpolation).
            character_paths: Optional list of character reference images (up to 3).
            aspect_ratio: '16:9' or '9:16' (defaults to saved user preference).
            resolution: '720p', '1080p', or '4k' (defaults to saved user preference).
            duration_seconds: Video duration in seconds (default 8s on Veo).
            negative_prompt: Elements to exclude from generation.
            output_path: Optional destination .mp4 path.
            save_as_preference: If True, saves these parameters as your default video preferences.
            wait_for_completion: Whether to wait for generation to finish and download.
            poll_interval_seconds: Polling interval in seconds (default 10).
            max_wait_seconds: Maximum wait timeout (default 360).
        """
        prefs = PreferencesManager.load()
        v_prefs = prefs.get("video", {})

        chosen_model = model or v_prefs.get("model", "veo-3.1-generate-preview")
        chosen_aspect = aspect_ratio or v_prefs.get("aspect_ratio", "16:9")
        chosen_resolution = resolution or v_prefs.get("resolution", "720p")
        chosen_duration = duration_seconds or v_prefs.get("duration_seconds", 8)

        if save_as_preference:
            PreferencesManager.update(
                media_type="video",
                model=chosen_model,
                aspect_ratio=chosen_aspect,
                resolution=chosen_resolution,
                duration_seconds=chosen_duration
            )

        if chosen_model not in MODEL_SPECIFICATIONS or MODEL_SPECIFICATIONS[chosen_model]["media_type"] != "video":
            return (
                f"Error: Unknown video model '{chosen_model}'.\n"
                f"Available Video Models:\n"
                f"- 'veo-3.1-generate-preview' (Recommended)\n"
                f"- 'gemini-omni-1.1-flash'\n"
                f"- 'veo-3.0-generate-001'\n"
                f"- 'veo-3.0-fast-generate-001'\n"
                f"Use 'get_model_specifications(model_name=\"{chosen_model}\")' to inspect requirements."
            )

        # Route to Omni
        if "omni" in chosen_model.lower():
            return generate_omni_video(
                prompt=prompt,
                model=chosen_model,
                character_paths=character_paths,
                output_path=output_path,
            )

        # Route to Veo
        start_frame = first_frame_path
        end_frame = last_frame_path

        if keyframe_paths:
            if len(keyframe_paths) >= 1 and not start_frame:
                start_frame = keyframe_paths[0]
            if len(keyframe_paths) >= 2 and not end_frame:
                end_frame = keyframe_paths[1]

        return generate_veo_video(
            prompt=prompt,
            model=chosen_model,
            first_frame_path=start_frame,
            last_frame_path=end_frame,
            character_paths=character_paths,
            aspect_ratio=chosen_aspect,
            resolution=chosen_resolution,
            duration_seconds=chosen_duration,
            negative_prompt=negative_prompt,
            output_path=output_path,
            wait_for_completion=wait_for_completion,
            poll_interval_seconds=poll_interval_seconds,
            max_wait_seconds=max_wait_seconds,
        )

    @mcp.tool()
    def check_video_operation(
        operation_name: str,
        output_path: Optional[str] = None
    ) -> str:
        """Check the status of an ongoing video generation operation and download when ready.

        Args:
            operation_name: The operation identifier from generate_video.
            output_path: Optional path to save the .mp4 video if completed.
        """
        return check_veo_operation(operation_name=operation_name, output_path=output_path)
