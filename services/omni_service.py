"""
Gemini Omni video generation service via Interactions API.
"""

import base64
from datetime import datetime
from typing import Optional, List, Dict, Any

from services.client import (
    get_genai_client,
    resolve_file_path,
    resolve_output_path,
    detect_mime_type,
    GENERATED_HISTORY,
)


def generate_omni_video(
    prompt: str,
    model: str = "gemini-omni-1.1-flash",
    character_paths: Optional[List[str]] = None,
    output_path: Optional[str] = None,
) -> str:
    """Generate high-velocity video using Gemini Omni via Interactions API."""
    client = get_genai_client()

    if character_paths:
        inputs: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        for c_path in character_paths:
            resolved_c = resolve_file_path(c_path)
            if not resolved_c.exists():
                return f"Error: Character reference image not found at '{resolved_c}'"
            with open(resolved_c, "rb") as f:
                c_bytes = f.read()
            mime = detect_mime_type(resolved_c)
            inputs.append({
                "type": "image",
                "data": base64.b64encode(c_bytes).decode("utf-8"),
                "mime_type": mime
            })
        omni_input = inputs
    else:
        omni_input = prompt

    interaction = client.interactions.create(model=model, input=omni_input)
    if not hasattr(interaction, "output_video") or not interaction.output_video or not interaction.output_video.data:
        return "Error: No video returned from Gemini Omni model."

    dest_file = resolve_output_path(output_path, "omni_video", "mp4")
    video_bytes = base64.b64decode(interaction.output_video.data)
    with open(dest_file, "wb") as f:
        f.write(video_bytes)

    GENERATED_HISTORY.append({
        "type": "video",
        "model": model,
        "prompt": prompt,
        "path": str(dest_file),
        "created_at": datetime.now().isoformat(),
    })

    return f"Video successfully generated with {model}!\nSaved to: {dest_file}"
