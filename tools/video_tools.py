"""
MCP Tools for video generation (Veo 3.1 & Omni) with keyframe, preference integration,
non-blocking async tracking, and active operations discovery.
"""

import os
from datetime import datetime
from typing import Optional, List
from config.constants import MODEL_SPECIFICATIONS
from config.preferences import PreferencesManager
from services.client import (
    get_genai_client,
    format_api_error,
    ActiveOperationsManager,
    GENERATED_HISTORY,
)
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
        wait_for_completion: bool = False,
        poll_interval_seconds: int = 10,
        max_wait_seconds: int = 360
    ) -> str:
        """Generic video generation command with model selection and preference persistence.

        By default, wait_for_completion=False: returns immediately with an Operation ID so the LLM
        can track progress using 'check_video_operation' without hitting tool timeouts.

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
            wait_for_completion: Whether to wait for generation to finish synchronously (default False to prevent timeouts).
            poll_interval_seconds: Polling interval in seconds if waiting synchronously (default 10).
            max_wait_seconds: Maximum wait timeout if waiting synchronously (default 360).
        """
        try:
            prefs = PreferencesManager.load()
            v_prefs = prefs.get("video") or {}

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
        except Exception as exc:
            return format_api_error(exc, context="generate_video")

    @mcp.tool()
    def check_video_operation(
        operation_name: str,
        output_path: Optional[str] = None
    ) -> str:
        """Check the status of an ongoing video generation operation and download when ready.

        Returns immediately in < 1s with either IN PROGRESS, COMPLETE (and saved path), or detailed error.

        Args:
            operation_name: The operation identifier from generate_video.
            output_path: Optional path to save the .mp4 video if completed.
        """
        try:
            return check_veo_operation(operation_name=operation_name, output_path=output_path)
        except Exception as exc:
            return format_api_error(exc, context=f"check_video_operation for '{operation_name}'")

    @mcp.tool()
    def list_active_operations(
        status_filter: Optional[str] = None
    ) -> str:
        """List all tracked video & media operations from disk, with status, elapsed times, and file paths.

        Args:
            status_filter: Optional filter ('IN_PROGRESS', 'COMPLETED', or 'FAILED').
        """
        try:
            ops = ActiveOperationsManager.list(status_filter=status_filter)
            if not ops:
                filter_str = f" with status '{status_filter}'" if status_filter else ""
                return f"No tracked operations found{filter_str}."

            lines = [f"=== Tracked Media Operations ({len(ops)} total) ==="]
            for op in ops:
                op_id = op.get("operation_name", "Unknown")
                status = op.get("status", "UNKNOWN")
                model = op.get("model", "Unknown")
                created = op.get("created_at", "N/A")
                prompt_snippet = op.get("prompt", "")[:50] + ("..." if len(op.get("prompt", "")) > 50 else "")

                # Calculate elapsed
                elapsed_str = ""
                if created != "N/A":
                    try:
                        st = datetime.fromisoformat(created)
                        sec = int((datetime.now() - st).total_seconds())
                        elapsed_str = f" | Elapsed: {sec}s"
                    except Exception:
                        pass

                lines.append(f"\n[{status}] {op_id}")
                lines.append(f"  Model: {model} | Started: {created}{elapsed_str}")
                lines.append(f"  Prompt: \"{prompt_snippet}\"")
                if status == "COMPLETED" and op.get("output_path"):
                    lines.append(f"  Output File: {op.get('output_path')}")
                elif status == "FAILED" and op.get("error"):
                    lines.append(f"  Error: {op.get('error')}")
                elif status == "IN_PROGRESS":
                    lines.append(f"  Action: Poll using 'check_video_operation(operation_name=\"{op_id}\")'")

            return "\n".join(lines)
        except Exception as exc:
            return format_api_error(exc, context="list_active_operations")

    @mcp.tool()
    def check_api_status() -> str:
        """Diagnostic pre-flight health check verifying API key format, connectivity, output directories, and quota readiness."""
        try:
            api_key = os.environ.get("GEMINI_API_KEY", "")
            key_status = "Not Set"
            key_format_hint = ""

            if api_key:
                masked_key = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
                if api_key.startswith("AIzaSy"):
                    key_status = f"Configured ({masked_key}) - Standard Google AI Studio Key"
                elif api_key == "gemini-api-key":
                    key_status = "Default Placeholder (INVALID)"
                    key_format_hint = "Warning: Replace with your actual Gemini API key."
                else:
                    key_status = f"Configured ({masked_key})"
                    key_format_hint = "Note: Standard Google AI Studio keys typically start with 'AIzaSy'."

            # Test client initialization
            client_status = "Client factory ready"
            try:
                client = get_genai_client()
            except Exception as e:
                client_status = f"Client initialization error: {e}"

            # Directory permissions
            effective_dir = PreferencesManager.get_effective_output_dir()
            try:
                effective_dir.mkdir(parents=True, exist_ok=True)
                dir_status = f"Writable ({effective_dir})"
            except Exception as e:
                dir_status = f"Error creating output directory: {e}"

            # Active operations stats
            all_ops = ActiveOperationsManager.list()
            in_prog = len([o for o in all_ops if o.get("status") == "IN_PROGRESS"])
            completed = len([o for o in all_ops if o.get("status") == "COMPLETED"])
            failed = len([o for o in all_ops if o.get("status") == "FAILED"])

            prefs = PreferencesManager.load()
            default_v = (prefs.get("video") or {}).get("model", "Not configured (veo-3.1-generate-preview recommended)")
            default_i = (prefs.get("image") or {}).get("model", "Not configured (gemini-nano-banana-2.1 recommended)")

            return (
                "=== Gemini & Veo Media Server Health Check ===\n\n"
                f"[API Key Status]: {key_status}\n"
                + (f"  {key_format_hint}\n" if key_format_hint else "")
                + f"[GenAI Client]: {client_status}\n"
                f"[Output Storage]: {dir_status}\n"
                f"[Operations Tracker]: {in_prog} In Progress, {completed} Completed, {failed} Failed\n"
                f"[Default Video Model]: {default_v}\n"
                f"[Default Image Model]: {default_i}\n\n"
                "System is ready to handle non-blocking generation and tracking."
            )
        except Exception as exc:
            return format_api_error(exc, context="check_api_status")
