"""
Gemini Nano Banana image generation & editing service.
Handles single image generation, 1-frame or 2-frame keyframe generation, and image editing.
Wrapped with comprehensive exception shielding to keep the MCP process resilient.
"""

import base64
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from config.constants import OUTPUTS_DIR
from services.client import (
    get_genai_client,
    resolve_file_path,
    resolve_output_path,
    detect_mime_type,
    format_api_error,
    GENERATED_HISTORY,
)


def generate_nano_banana_image(
    prompt: str,
    model: str = "gemini-nano-banana-2.1",
    character_paths: Optional[List[str]] = None,
    reference_image_paths: Optional[List[str]] = None,
    aspect_ratio: str = "16:9",
    image_size: str = "2K",
    enable_google_search: bool = False,
    output_path: Optional[str] = None,
) -> str:
    """Generate image using Gemini Nano Banana models with optional character/reference attachments."""
    try:
        client = get_genai_client()

        tools = [{"type": "google_search"}] if enable_google_search else None

        response_format = {
            "type": "image",
            "mime_type": "image/png",
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
        }

        attached_images = (character_paths or []) + (reference_image_paths or [])

        if attached_images:
            inputs: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
            for img_p in attached_images:
                resolved_p = resolve_file_path(img_p)
                if not resolved_p.exists():
                    return f"Error: Attached image file not found at '{resolved_p}'"
                with open(resolved_p, "rb") as f:
                    img_bytes = f.read()
                mime = detect_mime_type(resolved_p)
                inputs.append({
                    "type": "image",
                    "data": base64.b64encode(img_bytes).decode("utf-8"),
                    "mime_type": mime
                })
            interaction_input = inputs
        else:
            interaction_input = prompt

        interaction = client.interactions.create(
            model=model,
            input=interaction_input,
            tools=tools,
            response_format=response_format,
        )

        if not interaction.output_image or not interaction.output_image.data:
            return "Error: No image was returned by the model."

        dest_file = resolve_output_path(output_path, "gemini_image", "png")
        img_bytes = base64.b64decode(interaction.output_image.data)
        with open(dest_file, "wb") as f:
            f.write(img_bytes)

        GENERATED_HISTORY.append({
            "type": "image",
            "model": model,
            "prompt": prompt,
            "path": str(dest_file),
            "created_at": datetime.now().isoformat(),
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
            "attached_images_count": len(attached_images),
        })

        char_str = f" [Attached {len(attached_images)} Character/Reference Image(s)]" if attached_images else ""

        return (
            f"[Image Generated Successfully!]{char_str}\n"
            f"- Saved to: {dest_file}\n"
            f"- Model: {model} | Aspect Ratio: {aspect_ratio} | Size: {image_size}\n"
            f"- Interaction ID: {getattr(interaction, 'id', 'N/A')}"
        )
    except Exception as exc:
        return format_api_error(exc, context=f"image generation with model '{model}'")


def generate_keyframes_pair(
    start_prompt: str,
    end_prompt: Optional[str] = None,
    num_frames: int = 1,
    character_paths: Optional[List[str]] = None,
    model: str = "gemini-nano-banana-2.1",
    aspect_ratio: str = "16:9",
    image_size: str = "2K",
    output_dir: Optional[str] = None,
) -> str:
    """Generate 1 or 2 keyframes with continuity for video generation."""
    try:
        client = get_genai_client()

        target_num_frames = 2 if (end_prompt is not None or num_frames == 2) else 1
        base_dir = resolve_file_path(output_dir) if output_dir else OUTPUTS_DIR
        base_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        response_format = {
            "type": "image",
            "mime_type": "image/png",
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
        }

        # Step 1: Generate Frame 1 (Start Keyframe)
        if character_paths:
            inputs_1: List[Dict[str, Any]] = [{"type": "text", "text": start_prompt}]
            for c_path in character_paths:
                resolved_c = resolve_file_path(c_path)
                if not resolved_c.exists():
                    return f"Error: Character reference image not found at '{resolved_c}'"
                with open(resolved_c, "rb") as f:
                    c_bytes = f.read()
                mime = detect_mime_type(resolved_c)
                inputs_1.append({
                    "type": "image",
                    "data": base64.b64encode(c_bytes).decode("utf-8"),
                    "mime_type": mime
                })
            first_input = inputs_1
        else:
            first_input = start_prompt

        interaction_1 = client.interactions.create(
            model=model,
            input=first_input,
            response_format=response_format,
        )

        if not interaction_1.output_image or not interaction_1.output_image.data:
            return "Error: Failed to generate starting keyframe."

        frame_1_path = base_dir / f"keyframe_start_{timestamp}.png"
        with open(frame_1_path, "wb") as f:
            f.write(base64.b64decode(interaction_1.output_image.data))

        GENERATED_HISTORY.append({
            "type": "keyframe_start",
            "model": model,
            "prompt": start_prompt,
            "path": str(frame_1_path),
            "created_at": datetime.now().isoformat(),
            "aspect_ratio": aspect_ratio,
        })

        if target_num_frames == 1:
            return (
                f"[1 Keyframe Successfully Generated!]\n"
                f"- Starting Keyframe: {frame_1_path}\n"
                f"- Model: {model} | Aspect Ratio: {aspect_ratio}\n\n"
                f"Next step: Feed this frame into 'generate_video(prompt=\"...\", first_frame_path=\"{frame_1_path}\")'."
            )

        # Step 2: Generate Frame 2 (End Keyframe)
        second_prompt = end_prompt or f"Ending frame continuing from previous scene: {start_prompt} with camera progression and evolved character pose."

        interaction_2 = client.interactions.create(
            model=model,
            input=second_prompt,
            previous_interaction_id=interaction_1.id,
            response_format=response_format,
        )

        if not interaction_2.output_image or not interaction_2.output_image.data:
            return (
                f"Starting keyframe generated at: {frame_1_path}\n"
                f"Error: Failed to generate ending keyframe."
            )

        frame_2_path = base_dir / f"keyframe_end_{timestamp}.png"
        with open(frame_2_path, "wb") as f:
            f.write(base64.b64decode(interaction_2.output_image.data))

        GENERATED_HISTORY.append({
            "type": "keyframe_end",
            "model": model,
            "prompt": second_prompt,
            "path": str(frame_2_path),
            "created_at": datetime.now().isoformat(),
            "aspect_ratio": aspect_ratio,
            "previous_interaction_id": interaction_1.id,
        })

        return (
            f"[2 Keyframes Generated with Continuity!]\n"
            f"1. Starting Keyframe: {frame_1_path}\n"
            f"2. Ending Keyframe:   {frame_2_path}\n"
            f"- Model: {model} | Aspect Ratio: {aspect_ratio}\n\n"
            f"Next step: Interpolate smoothly between both frames with:\n"
            f"- generate_video(prompt=\"...\", first_frame_path=\"{frame_1_path}\", last_frame_path=\"{frame_2_path}\")"
        )
    except Exception as exc:
        return format_api_error(exc, context="keyframe pair generation")


def edit_nano_banana_image(
    prompt: str,
    image_path: str,
    model: str = "gemini-nano-banana-2.1",
    aspect_ratio: Optional[str] = None,
    image_size: Optional[str] = None,
    output_path: Optional[str] = None,
) -> str:
    """Edit image conversationally using Nano Banana."""
    try:
        resolved_img = resolve_file_path(image_path)
        if not resolved_img.exists():
            return f"Error: Source image file not found at '{resolved_img}'"

        client = get_genai_client()

        with open(resolved_img, "rb") as f:
            img_raw = f.read()
        b64_img = base64.b64encode(img_raw).decode("utf-8")
        mime = detect_mime_type(resolved_img)

        inputs = [
            {"type": "text", "text": prompt},
            {"type": "image", "data": b64_img, "mime_type": mime}
        ]

        response_format = {"type": "image", "mime_type": "image/png"}
        if aspect_ratio:
            response_format["aspect_ratio"] = aspect_ratio
        if image_size:
            response_format["image_size"] = image_size

        interaction = client.interactions.create(
            model=model,
            input=inputs,
            response_format=response_format,
        )

        if not interaction.output_image or not interaction.output_image.data:
            return "Error: No image returned by the editing model."

        dest_file = resolve_output_path(output_path, "gemini_edited_image", "png")
        img_bytes = base64.b64decode(interaction.output_image.data)
        with open(dest_file, "wb") as f:
            f.write(img_bytes)

        GENERATED_HISTORY.append({
            "type": "image_edit",
            "model": model,
            "prompt": prompt,
            "source_image": str(resolved_img),
            "path": str(dest_file),
            "created_at": datetime.now().isoformat(),
        })

        return (
            f"[Image Edited Successfully!]\n"
            f"- Saved to: {dest_file}\n"
            f"- Model: {model}\n"
            f"- Source Image: {resolved_img}"
        )
    except Exception as exc:
        return format_api_error(exc, context=f"image editing with model '{model}'")
