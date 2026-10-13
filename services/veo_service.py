"""
Google Veo video generation service.
Handles text-to-video, image-to-video, 2-keyframe interpolation, and reference images.
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
    GENERATED_HISTORY,
)


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
    wait_for_completion: bool = True,
    poll_interval_seconds: int = 10,
    max_wait_seconds: int = 360,
) -> str:
    """Generate video using Google Veo models."""
    client = get_genai_client()

    primary_input_image = None
    if first_frame_path:
        start_p = resolve_file_path(first_frame_path)
        if not start_p.exists():
            return f"Error: Starting keyframe image not found at '{start_p}'"
        primary_input_image = Image.open(start_p)

    last_frame_img = None
    if last_frame_path:
        last_p = resolve_file_path(last_frame_path)
        if not last_p.exists():
            return f"Error: Ending keyframe image not found at '{last_p}'"
        last_frame_img = Image.open(last_p)

    ref_objects = []
    if character_paths:
        if len(character_paths) > 3:
            return f"Error: Veo supports up to 3 reference images maximum. Provided {len(character_paths)}."
        for c_path in character_paths:
            resolved_c = resolve_file_path(c_path)
            if not resolved_c.exists():
                return f"Error: Character reference image not found at '{resolved_c}'"
            ref_objects.append(
                types.VideoGenerationReferenceImage(
                    image=Image.open(resolved_c),
                    reference_type="asset"
                )
            )

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

    if not wait_for_completion:
        mode_desc = "2 Keyframes" if (primary_input_image and last_frame_img) else ("1 Keyframe" if primary_input_image else "Text-to-Video")
        return (
            f"Video generation started with model '{model}' ({mode_desc}).\n"
            f"Operation Name: {op_name}\n"
            f"Use 'check_video_operation' to poll status."
        )

    start_time = time.time()
    while not operation.done:
        if (time.time() - start_time) > max_wait_seconds:
            return (
                f"Generation is still in progress after {max_wait_seconds} seconds.\n"
                f"Operation Name: {op_name}\n"
                f"Check later using 'check_video_operation'."
            )
        time.sleep(poll_interval_seconds)
        operation = client.operations.get(operation)

    if hasattr(operation, "error") and operation.error:
        return f"Error during video generation: {operation.error}"

    dest_file = resolve_output_path(output_path, "veo_video", "mp4")
    generated_video = operation.response.generated_videos[0]
    client.files.download(file=generated_video.video, destination=str(dest_file))

    GENERATED_HISTORY.append({
        "type": "video",
        "model": model,
        "prompt": prompt,
        "path": str(dest_file),
        "created_at": datetime.now().isoformat(),
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
    })

    mode_info = "2 Keyframes (Interpolation)" if (primary_input_image and last_frame_img) else ("1 Keyframe (Start)" if primary_input_image else "Text-to-Video")
    char_info = f", {len(ref_objects)} Character(s)" if ref_objects else ""

    return (
        f"Video successfully generated!\n"
        f"Saved to: {dest_file}\n"
        f"Model: {model} | Mode: {mode_info}{char_info}\n"
        f"Resolution: {resolution} | Aspect Ratio: {aspect_ratio} | Duration: {duration_seconds}s"
    )


def check_veo_operation(operation_name: str, output_path: Optional[str] = None) -> str:
    """Check status of a Veo long-running operation."""
    client = get_genai_client()
    operation = client.operations.get(operation_name)

    if not operation.done:
        metadata = getattr(operation, "metadata", None)
        return f"Operation '{operation_name}' is IN PROGRESS. Metadata: {metadata}"

    if hasattr(operation, "error") and operation.error:
        return f"Operation '{operation_name}' failed: {operation.error}"

    dest_file = resolve_output_path(output_path, "veo_operation", "mp4")
    generated_video = operation.response.generated_videos[0]
    client.files.download(file=generated_video.video, destination=str(dest_file))

    return f"Operation '{operation_name}' is COMPLETE!\nVideo saved to: {dest_file}"
