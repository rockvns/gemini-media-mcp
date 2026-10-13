"""
Gemini Nano Banana image generation & editing service.
Handles single image generation, 1-frame or 2-frame keyframe generation, and image editing.
Uses direct generate_content with response_modalities=['IMAGE'] for single-call efficiency,
with robust error handling, fallback to interactions API, and guaranteed file persistence in the configured output directory.
"""

import io
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from PIL import Image
from google.genai import types

from config.constants import OUTPUTS_DIR
from services.client import (
    get_genai_client,
    resolve_file_path,
    resolve_output_path,
    detect_mime_type,
    format_api_error,
    GENERATED_HISTORY,
)


def _save_image_data(img_bytes: bytes, dest_file: Path) -> int:
    """Save image bytes to file, converting to PNG if requested by destination suffix.
    Returns the file size in bytes.
    """
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    if dest_file.suffix.lower() == ".png":
        try:
            pil_img = Image.open(io.BytesIO(img_bytes))
            pil_img.save(dest_file, format="PNG")
            return dest_file.stat().st_size
        except Exception:
            pass
    with open(dest_file, "wb") as f:
        f.write(img_bytes)
    return dest_file.stat().st_size


def _format_size(size_bytes: int) -> str:
    """Format bytes into readable KB/MB string."""
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    return f"{size_bytes / 1024:.1f} KB"


def _extract_image_bytes(response: Any) -> Tuple[Optional[bytes], Optional[str]]:
    """Extract image bytes and mime type from GenerateContent response."""
    if not response or not hasattr(response, "candidates") or not response.candidates:
        return None, None

    for cand in response.candidates:
        if not cand.content or not cand.content.parts:
            continue
        for part in cand.content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                blob = part.inline_data
                data = blob.data
                mime = getattr(blob, "mime_type", "image/jpeg")
                if isinstance(data, str):
                    try:
                        data = base64.b64decode(data)
                    except Exception:
                        pass
                return data, mime
    return None, None


def _extract_text_content(response: Any) -> str:
    """Extract any textual response or refusal reason from candidate parts."""
    texts = []
    if hasattr(response, "candidates") and response.candidates:
        for cand in response.candidates:
            if cand.content and cand.content.parts:
                for part in cand.content.parts:
                    if hasattr(part, "text") and part.text:
                        texts.append(part.text)
    return " ".join(texts).strip()


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
    """Generate image using Gemini Nano Banana models with optional character/reference attachments.
    Uses generate_content for high reliability (single API request) with fallback to Interactions API.
    """
    try:
        client = get_genai_client()
        attached_images = (character_paths or []) + (reference_image_paths or [])

        # ------------------------------------------------------------------
        # Primary Path: client.models.generate_content (1 API call)
        # ------------------------------------------------------------------
        try:
            image_config_args: Dict[str, Any] = {}
            if aspect_ratio:
                image_config_args["aspect_ratio"] = aspect_ratio
            if image_size:
                image_config_args["image_size"] = image_size

            content_config = types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(**image_config_args) if image_config_args else None,
            )
            if enable_google_search:
                content_config.tools = [types.Tool(google_search=types.GoogleSearch())]

            contents: List[Any] = []
            for img_p in attached_images:
                resolved_p = resolve_file_path(img_p)
                if not resolved_p.exists():
                    return f"Error: Attached image file not found at '{resolved_p}'"
                with open(resolved_p, "rb") as f:
                    img_raw = f.read()
                mime = detect_mime_type(resolved_p)
                contents.append(types.Part.from_bytes(data=img_raw, mime_type=mime))

            contents.append(prompt)

            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=content_config,
            )

            img_bytes, mime = _extract_image_bytes(response)
            if img_bytes:
                ext = "png" if (output_path and output_path.lower().endswith(".png")) else "jpg"
                dest_file = resolve_output_path(output_path, "gemini_image", ext)
                file_size = _save_image_data(img_bytes, dest_file)

                GENERATED_HISTORY.append({
                    "type": "image",
                    "model": model,
                    "prompt": prompt,
                    "path": str(dest_file),
                    "created_at": datetime.now().isoformat(),
                    "aspect_ratio": aspect_ratio,
                    "image_size": image_size,
                    "file_size_bytes": file_size,
                    "attached_images_count": len(attached_images),
                })

                char_str = f" [Attached {len(attached_images)} Character/Reference Image(s)]" if attached_images else ""
                return (
                    f"[Image Generated Successfully!]{char_str}\n"
                    f"- Saved to: {dest_file}\n"
                    f"- File Size: {_format_size(file_size)}\n"
                    f"- Model: {model} | Aspect Ratio: {aspect_ratio} | Size: {image_size}"
                )

            # If no image bytes returned, check if model sent explanatory text
            alt_text = _extract_text_content(response)
            if alt_text:
                return (
                    f"Notice: The model completed without returning image data.\n"
                    f"Model explanation: {alt_text}\n"
                    f"Recommendation: Adjust prompt wording or verify that your project tier supports image output."
                )

        except Exception as primary_exc:
            # If the error is a quota/rate limit error (429) or authentication error (401/403),
            # return immediately without making wasteful secondary calls.
            err_code = getattr(primary_exc, "code", None)
            err_str = str(primary_exc)
            if err_code in [401, 403, 429] or any(k in err_str for k in ["429", "RESOURCE_EXHAUSTED", "quota"]):
                return format_api_error(primary_exc, context=f"image generation with model '{model}'")

            # Fallback to Interactions API if generate_content failed for other reasons
            pass

        # ------------------------------------------------------------------
        # Secondary Path: client.interactions.create with strict timeout
        # ------------------------------------------------------------------
        response_format = {
            "type": "image",
            "mime_type": "image/jpeg",
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
        }
        tools = [{"type": "google_search"}] if enable_google_search else None

        if attached_images:
            inputs: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
            for img_p in attached_images:
                resolved_p = resolve_file_path(img_p)
                if not resolved_p.exists():
                    return f"Error: Attached image file not found at '{resolved_p}'"
                with open(resolved_p, "rb") as f:
                    img_raw = f.read()
                mime = detect_mime_type(resolved_p)
                inputs.append({
                    "type": "image",
                    "data": base64.b64encode(img_raw).decode("utf-8"),
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
            timeout=45.0,
        )

        img_data = None
        if hasattr(interaction, "output_image") and interaction.output_image and getattr(interaction.output_image, "data", None):
            img_data = interaction.output_image.data
        elif hasattr(interaction, "steps") and interaction.steps:
            for step in reversed(interaction.steps):
                content = getattr(step, "content", None) or (step.get("content") if isinstance(step, dict) else None)
                if isinstance(content, list):
                    for item in content:
                        itype = getattr(item, "type", None) or (item.get("type") if isinstance(item, dict) else None)
                        if itype == "image":
                            img_data = getattr(item, "data", None) or (item.get("data") if isinstance(item, dict) else None)
                            if img_data:
                                break
                if img_data:
                    break

        if not img_data:
            return "Error: No image was returned by the model after execution."

        ext = "png" if (output_path and output_path.lower().endswith(".png")) else "jpg"
        dest_file = resolve_output_path(output_path, "gemini_image", ext)
        img_bytes = base64.b64decode(img_data)
        file_size = _save_image_data(img_bytes, dest_file)

        GENERATED_HISTORY.append({
            "type": "image",
            "model": model,
            "prompt": prompt,
            "path": str(dest_file),
            "created_at": datetime.now().isoformat(),
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
            "file_size_bytes": file_size,
        })

        return (
            f"[Image Generated Successfully!]\n"
            f"- Saved to: {dest_file}\n"
            f"- File Size: {_format_size(file_size)}\n"
            f"- Model: {model} | Aspect Ratio: {aspect_ratio} | Size: {image_size}"
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

        content_config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=aspect_ratio, image_size=image_size),
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Step 1: Generate Frame 1 (Start Keyframe)
        inputs_1: List[Any] = []
        if character_paths:
            for c_path in character_paths:
                resolved_c = resolve_file_path(c_path)
                if not resolved_c.exists():
                    return f"Error: Character reference image not found at '{resolved_c}'"
                with open(resolved_c, "rb") as f:
                    c_bytes = f.read()
                mime = detect_mime_type(resolved_c)
                inputs_1.append(types.Part.from_bytes(data=c_bytes, mime_type=mime))
        inputs_1.append(start_prompt)

        response_1 = client.models.generate_content(
            model=model,
            contents=inputs_1,
            config=content_config,
        )

        img_bytes_1, _ = _extract_image_bytes(response_1)
        if not img_bytes_1:
            alt = _extract_text_content(response_1)
            return f"Error: Failed to generate starting keyframe. {alt}".strip()

        dest_prefix = f"keyframe_start_{timestamp}"
        frame_1_path = resolve_output_path(
            str(Path(output_dir) / f"{dest_prefix}.jpg") if output_dir else None,
            dest_prefix,
            "jpg"
        )
        file_size_1 = _save_image_data(img_bytes_1, frame_1_path)

        GENERATED_HISTORY.append({
            "type": "keyframe_start",
            "model": model,
            "prompt": start_prompt,
            "path": str(frame_1_path),
            "created_at": datetime.now().isoformat(),
            "aspect_ratio": aspect_ratio,
            "file_size_bytes": file_size_1,
        })

        if target_num_frames == 1:
            return (
                f"[1 Keyframe Successfully Generated!]\n"
                f"- Starting Keyframe: {frame_1_path} ({_format_size(file_size_1)})\n"
                f"- Model: {model} | Aspect Ratio: {aspect_ratio}\n\n"
                f"Next step: Feed this frame into 'generate_video(prompt=\"...\", first_frame_path=\"{frame_1_path}\")'."
            )

        # Step 2: Generate Frame 2 (End Keyframe) continuing from Frame 1
        second_prompt = end_prompt or f"Ending frame continuing from previous scene: {start_prompt} with camera progression and evolved character pose."
        inputs_2 = [
            types.Part.from_bytes(data=img_bytes_1, mime_type="image/jpeg"),
            second_prompt
        ]

        response_2 = client.models.generate_content(
            model=model,
            contents=inputs_2,
            config=content_config,
        )

        img_bytes_2, _ = _extract_image_bytes(response_2)
        if not img_bytes_2:
            return (
                f"Starting keyframe generated at: {frame_1_path}\n"
                f"Error: Failed to generate ending keyframe: {_extract_text_content(response_2)}"
            )

        dest_prefix_2 = f"keyframe_end_{timestamp}"
        frame_2_path = resolve_output_path(
            str(Path(output_dir) / f"{dest_prefix_2}.jpg") if output_dir else None,
            dest_prefix_2,
            "jpg"
        )
        file_size_2 = _save_image_data(img_bytes_2, frame_2_path)

        GENERATED_HISTORY.append({
            "type": "keyframe_end",
            "model": model,
            "prompt": second_prompt,
            "path": str(frame_2_path),
            "created_at": datetime.now().isoformat(),
            "aspect_ratio": aspect_ratio,
            "file_size_bytes": file_size_2,
        })

        return (
            f"[2 Keyframes Generated with Continuity!]\n"
            f"1. Starting Keyframe: {frame_1_path} ({_format_size(file_size_1)})\n"
            f"2. Ending Keyframe:   {frame_2_path} ({_format_size(file_size_2)})\n"
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
    """Edit image conversationally using Nano Banana models."""
    try:
        resolved_img = resolve_file_path(image_path)
        if not resolved_img.exists():
            return f"Error: Source image file not found at '{resolved_img}'"

        client = get_genai_client()

        with open(resolved_img, "rb") as f:
            img_raw = f.read()
        mime = detect_mime_type(resolved_img)

        image_config_args: Dict[str, Any] = {}
        if aspect_ratio:
            image_config_args["aspect_ratio"] = aspect_ratio
        if image_size:
            image_config_args["image_size"] = image_size

        content_config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(**image_config_args) if image_config_args else None,
        )

        contents = [
            types.Part.from_bytes(data=img_raw, mime_type=mime),
            prompt
        ]

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=content_config,
        )

        img_bytes, _ = _extract_image_bytes(response)
        if not img_bytes:
            alt = _extract_text_content(response)
            return f"Error: No image returned by the editing model. {alt}".strip()

        ext = "png" if (output_path and output_path.lower().endswith(".png")) else "jpg"
        dest_file = resolve_output_path(output_path, "gemini_edited_image", ext)
        file_size = _save_image_data(img_bytes, dest_file)

        GENERATED_HISTORY.append({
            "type": "image_edit",
            "model": model,
            "prompt": prompt,
            "source_image": str(resolved_img),
            "path": str(dest_file),
            "created_at": datetime.now().isoformat(),
            "file_size_bytes": file_size,
        })

        return (
            f"[Image Edited Successfully!]\n"
            f"- Saved to: {dest_file}\n"
            f"- File Size: {_format_size(file_size)}\n"
            f"- Model: {model}\n"
            f"- Source Image: {resolved_img}"
        )
    except Exception as exc:
        return format_api_error(exc, context=f"image editing with model '{model}'")
