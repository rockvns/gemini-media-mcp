"""
MCP Prompts for media generation, preferences, and director guidance.
"""


def configure_preferences_prompt(media_type: str = "video") -> str:
    """Interactive prompt template to guide the user in selecting their default model and parameters."""
    return f"""Let's configure your default preferences for {media_type.upper()} generation.

Available Options:
- Video Models:
  • 'veo-3.1-generate-preview': 720p, 1080p, 4k | 16:9, 9:16 | 8 seconds | Keyframes & Characters
  • 'gemini-omni-1.1-flash': Ultra-fast | 16:9 | 5s or 8s
- Image Models (Nano Banana):
  • 'gemini-nano-banana-2.1': 1K, 2K, 4K | 16:9, 1:1, 9:16, etc. | Search Grounding
  • 'gemini-3-pro-image': Premium quality, text rendering, and brand consistency
  • 'gemini-3.1-flash-lite-image': Ultra fast, 1K only

Please specify:
1. Preferred default model
2. Preferred aspect ratio (e.g. '16:9')
3. Preferred resolution (e.g. '720p' or '2K')
4. Preferred output directory (e.g. 'outputs/' or a custom folder; can also be configured via MEDIA_OUTPUT_DIR in .env)
5. Would you like to save this permanently to user_preferences.json?"""


def select_model_prompt(media_type: str = "video", goal_description: str = "") -> str:
    """Ask for and select the best model based on the user's specific media generation goal."""
    return f"""Evaluate the best model to use for the following {media_type.upper()} generation task:

Goal: {goal_description or "General generation"}

Review specifications via 'get_model_specifications()' and suggest:
1. Recommended Model code
2. Recommended Aspect Ratio & Resolution
3. Keyframe strategy (0, 1, or 2 frames)
4. Confirm if user wants to update default preferences."""


def veo_director_prompt(concept: str, mood: str = "cinematic", camera_motion: str = "drone shot") -> str:
    """Create a structured, high-detail director prompt optimized for Veo 3.1 video generation."""
    return f"""Act as a cinematographer and director. Expand the following concept into a prompt for Google Veo 3.1 video generation.

Concept: {concept}
Desired Mood: {mood}
Camera Motion: {camera_motion}

Structure the prompt to include:
1. Opening shot & composition (angle, framing, focal length)
2. Subject action & motion dynamics
3. Environmental atmosphere & lighting (e.g. golden hour, volumetric lighting, reflections)
4. Audio & sound design (dialogue, ambient sounds, sound effects, music)
Make the prompt vivid, concise, and direct."""


def veo_keyframe_storyboard_prompt(
    start_scene_desc: str,
    end_scene_desc: str,
    character_name: str = "the character"
) -> str:
    """Create a prompt tailored for interpolating between a starting keyframe and an ending keyframe."""
    return f"""Act as a VFX and storyboard director. Formulate a smooth transition prompt for Veo 3.1 connecting two keyframes:

Starting Keyframe: {start_scene_desc}
Ending Keyframe: {end_scene_desc}
Subject / Character: {character_name}

Describe:
1. Continuous camera movement linking the start frame to the end frame.
2. Character movement and intermediate poses.
3. Environmental shifts (lighting, weather, particle effects).
4. Audio cue progression bridging the scene."""


def character_consistency_prompt(character_description: str, new_scene: str, action: str) -> str:
    """Create a prompt for placing an attached reference character into a new scene while preserving consistency."""
    return f"""Using the attached character reference image(s), generate a new scene maintaining 100% character identity and appearance.

Character Identity: {character_description}
New Setting / Environment: {new_scene}
Action / Pose: {action}

Keep facial structure, clothing details, hairstyles, and signature accessories consistent with the reference image."""
