"""
Prompts package.
"""

from .media_prompts import (
    configure_preferences_prompt,
    select_model_prompt,
    veo_director_prompt,
    veo_keyframe_storyboard_prompt,
    character_consistency_prompt,
)

__all__ = [
    "configure_preferences_prompt",
    "select_model_prompt",
    "veo_director_prompt",
    "veo_keyframe_storyboard_prompt",
    "character_consistency_prompt",
]
