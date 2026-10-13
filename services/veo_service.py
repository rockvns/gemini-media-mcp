"""
Google Veo video generation service.
Handles text-to-video, image-to-video, 2-keyframe interpolation, and reference images.
Features non-blocking async dispatch, persistent operation tracking, and comprehensive error formatting.
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from PIL import Image
from google.genai import types

from services.client import (
    get_genai_client,
    resolve_file_path,
    resolve_output_path,
    format_api_error,
    ActiveOperationsManager,
    GENERATED_HISTORY,
)


def _format_size(size_bytes: int) -> str:
    """Format bytes into readable KB/MB string."""
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    return f"{size_bytes / 1024:.1f} KB"


def _save_downloaded_video(client, video_ref, dest_file: Path) -> int:
    """Download and save video safely to destination path, verifying file existence and size."""
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    result = client.files.download(file=video_ref, destination=str(dest_file))
    if isinstance(result, (bytes, bytearray)) and not (dest_file.exists() and dest_file.stat().st_size > 0):
        with open(dest_file, "wb") as f:
            f.write(result)
    if not dest_file.exists() or dest_file.stat().st_size == 0:
        raise IOError(f"Video file at '{dest_file}' is missing or empty after download.")
    return dest_file.stat().st_size


def generate_veo_video(
    prompt: str,
    model: str = "veo-3.1-generate-preview",
    first_frame_path: Optional[str] = None,
    last_frame_path: Optional[str] = None,
    character_paths: Optional[List[str]] = None,
    aspect_ratio: str = "16:9",
    resolution: str = "720p",
    duration_seconds: int = 8,
    negative_prompt: Optional[str] = None,
    output_path: Optional[str] = None,
    wait_for_completion: bool = False,
    poll_interval_seconds: int = 10,
    max_wait_seconds: int = 360,
) -> str:
    """Generate video using Google Veo models with safe error handling and async tracking."""
    try:
        client = get_genai_client()

        primary_input_image = None
        if first_frame_path:
            start_p = resolve_file_path(first_frame_path)
            if not start_p.exists():
                return f"Error: Starting keyframe image not found at '{start_p}'"
            try:
                primary_input_image = Image.open(start_p)
            except Exception as e:
                return f"Error opening starting keyframe image '{start_p}': {e}"

        last_frame_img = None
        if last_frame_path:
            last_p = resolve_file_path(last_frame_path)
            if not last_p.exists():
                return f"Error: Ending keyframe image not found at '{last_p}'"
            try:
                last_frame_img = Image.open(last_p)
            except Exception as e:
                return f"Error opening ending keyframe image '{last_p}': {e}"

        ref_objects = []
        if character_paths:
            if len(character_paths) > 3:
                return f"Error: Veo supports up to 3 reference images maximum. Provided {len(character_paths)}."
            for c_path in character_paths:
                resolved_c = resolve_file_path(c_path)
                if not resolved_c.exists():
                    return f"Error: Character reference image not found at '{resolved_c}'"
                try:
                    ref_objects.append(
                        types.VideoGenerationReferenceImage(
                            image=Image.open(resolved_c),
                            reference_type="asset"
                        )
                    )
                except Exception as e:
                    return f"Error opening character reference image '{resolved_c}': {e}"

        video_config = types.GenerateVideosConfig(
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            last_frame=last_frame_img,
            reference_images=ref_objects if ref_objects else None,
            duration_seconds=duration_seconds,
            negative_prompt=negative_prompt,
        )

        operation = client.models.generate_videos(
            model=model,
            prompt=prompt,
            image=primary_input_image,
            config=video_config,
        )

        op_name = getattr(operation, "name", str(operation))

        # Register operation in persistent disk store
        ActiveOperationsManager.register(
            operation_name=op_name,
            media_type="video",
            model=model,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            output_path=output_path,
        )

        mode_desc = (
            "2 Keyframes (Interpolation)"
            if (primary_input_image and last_frame_img)
            else ("1 Keyframe (Start)" if primary_input_image else "Text-to-Video")
        )

        # 1. Non-blocking Async Dispatch (Default)
        if not wait_for_completion:
            return (
                f"[Video Generation Started]\n"
                f"- Operation ID: {op_name}\n"
                f"- Model: {model} | Mode: {mode_desc}\n"
                f"- Resolution: {resolution} | Aspect Ratio: {aspect_ratio} | Duration: {duration_seconds}s\n"
                f"- Status: IN_PROGRESS\n\n"
                f"Next Steps for LLM:\n"
                f"1. Inform the user that generation has started with Operation ID '{op_name}'.\n"
                f"2. Poll progress every 15-20s using 'check_video_operation(operation_name=\"{op_name}\")'.\n"
                f"3. Zero timeout risk: each check call completes in < 1 second."
            )

        # 2. Synchronous Wait (if explicitly requested)
        start_time = time.time()
        while not operation.done:
            elapsed = int(time.time() - start_time)
            if elapsed > max_wait_seconds:
                return (
                    f"[Video Generation In Progress - Timeout Limit Reached]\n"
                    f"Generation has been running for {elapsed} seconds (max wait: {max_wait_seconds}s).\n"
                    f"Operation ID: {op_name}\n"
                    f"Action: Generation continues on Google servers. Check later with 'check_video_operation(operation_name=\"{op_name}\")'."
                )
            time.sleep(poll_interval_seconds)
            operation = client.operations.get(operation)

        if hasattr(operation, "error") and operation.error:
            ActiveOperationsManager.update(op_name, status="FAILED", error=str(operation.error))
            return f"Error during video generation ({op_name}): {operation.error}"

        dest_file = resolve_output_path(output_path, "veo_video", "mp4")
        generated_video = operation.response.generated_videos[0]
        file_size = _save_downloaded_video(client, generated_video.video, dest_file)

        total_elapsed = int(time.time() - start_time)
        ActiveOperationsManager.update(op_name, status="COMPLETED", output_path=str(dest_file))

        GENERATED_HISTORY.append({
            "type": "video",
            "model": model,
            "prompt": prompt,
            "path": str(dest_file),
            "created_at": datetime.now().isoformat(),
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "duration_seconds": total_elapsed,
            "file_size_bytes": file_size,
        })

        char_info = f", {len(ref_objects)} Character(s)" if ref_objects else ""
        return (
            f"[Video Successfully Generated!]\n"
            f"- Saved to: {dest_file}\n"
            f"- File Size: {_format_size(file_size)}\n"
            f"- Operation ID: {op_name}\n"
            f"- Model: {model} | Mode: {mode_desc}{char_info}\n"
            f"- Resolution: {resolution} | Aspect Ratio: {aspect_ratio} | Duration: {duration_seconds}s\n"
            f"- Generation Time: {total_elapsed}s"
        )

    except Exception as exc:
        return format_api_error(exc, context="Veo video generation")


def check_veo_operation(operation_name: str, output_path: Optional[str] = None) -> str:
    """Check status of a Veo long-running operation, updating persistence and downloading when ready."""
    try:
        client = get_genai_client()
        operation = client.operations.get(operation_name)

        op_data = ActiveOperationsManager.get(operation_name) or {}
        created_at_str = op_data.get("created_at")
        elapsed_str = ""
        if created_at_str:
            try:
                start_dt = datetime.fromisoformat(created_at_str)
                elapsed_sec = int((datetime.now() - start_dt).total_seconds())
                elapsed_str = f" | Elapsed Time: {elapsed_sec}s"
            except Exception:
                pass

        if not operation.done:
            ActiveOperationsManager.update(operation_name, status="IN_PROGRESS")
            metadata = getattr(operation, "metadata", None)
            meta_info = f" | Metadata: {metadata}" if metadata else ""
            return (
                f"[Video Generation IN PROGRESS]\n"
                f"- Operation ID: {operation_name}{elapsed_str}{meta_info}\n"
                f"- Status: Rendering on Google Cloud\n"
                f"- Recommendation: Check again in 15-20 seconds using 'check_video_operation(operation_name=\"{operation_name}\")'."
            )

        if hasattr(operation, "error") and operation.error:
            ActiveOperationsManager.update(operation_name, status="FAILED", error=str(operation.error))
            return (
                f"[Video Generation FAILED]\n"
                f"- Operation ID: {operation_name}{elapsed_str}\n"
                f"- Error: {operation.error}\n"
                f"- Status: Marked as FAILED in active operations tracker."
            )

        # Download result
        target_path = output_path or op_data.get("output_path")
        dest_file = resolve_output_path(target_path, "veo_operation", "mp4")
        generated_video = operation.response.generated_videos[0]
        file_size = _save_downloaded_video(client, generated_video.video, dest_file)

        ActiveOperationsManager.update(operation_name, status="COMPLETED", output_path=str(dest_file))

        GENERATED_HISTORY.append({
            "type": "video",
            "model": op_data.get("model", "veo-3.1-generate-preview"),
            "prompt": op_data.get("prompt", "N/A"),
            "path": str(dest_file),
            "created_at": datetime.now().isoformat(),
            "aspect_ratio": op_data.get("aspect_ratio", "16:9"),
            "resolution": op_data.get("resolution", "720p"),
            "file_size_bytes": file_size,
        })

        return (
            f"[Video Generation COMPLETE!]\n"
            f"- Operation ID: {operation_name}{elapsed_str}\n"
            f"- File Saved to: {dest_file}\n"
            f"- File Size: {_format_size(file_size)}\n"
            f"- Status: COMPLETED (saved to history and disk)"
        )

    except Exception as exc:
        return format_api_error(exc, context=f"checking video operation '{operation_name}'")
