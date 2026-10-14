"""
Gemini & Veo MCP Server Entrypoint.

Modularized architecture:
- config/      : Model specifications, constants, and persistent user preferences.
- services/    : Model-specific APIs (Veo 3.1, Omni Flash, Nano Banana).
- tools/       : MCP tool registrations (Video, Image, Keyframes, Preferences).
- prompts/     : MCP prompt templates (Director, Keyframe, Consistency, Preferences).
"""

import sys
import logging

# Strictly ensure all logging and warnings go to stderr so stdout remains 100% clean for MCP JSON-RPC
logging.basicConfig(stream=sys.stderr, level=logging.WARNING, force=True)
for name in ["google", "google.genai", "httpx", "httpcore", "mcp"]:
    _l = logging.getLogger(name)
    _l.setLevel(logging.WARNING)
    _l.handlers = [logging.StreamHandler(sys.stderr)]
    _l.propagate = False

from mcp.server.mcpserver import MCPServer

from config.constants import MODEL_SPECIFICATIONS
from config.preferences import PreferencesManager
from services.client import GENERATED_HISTORY
from tools import register_all_tools
from prompts import (
    configure_preferences_prompt,
    select_model_prompt,
    veo_director_prompt,
    veo_keyframe_storyboard_prompt,
    character_consistency_prompt,
)

# Initialize MCP Server
mcp = MCPServer(
    name="GeminiMediaServer",
    version="2.2.0",
    description="Modular MCP server for video & image generation with model discovery and user preference persistence."
)

# 1. Register all tools (Video, Image, Keyframes, Preferences)
register_all_tools(mcp)


# 2. Register MCP Resources
@mcp.resource("media://preferences")
def get_preferences_resource() -> str:
    """Resource returning user saved preferences for video and image generation."""
    return PreferencesManager.get_summary()


@mcp.resource("media://models")
def get_models_resource() -> str:
    """Resource listing supported video and image models and their capabilities."""
    lines = ["=== Available Models Catalog ==="]
    for mid, spec in MODEL_SPECIFICATIONS.items():
        lines.append(f"\n[{spec['name']}] ({mid})")
        if spec["media_type"] == "video":
            lines.append(f"  Resolutions: {spec.get('supported_resolutions')} | Ratios: {spec.get('supported_aspect_ratios')} | Audio: {spec.get('native_audio')}")
        else:
            lines.append(f"  Sizes: {spec.get('supported_sizes')} | Search Grounding: {spec.get('supports_google_search')} | Max References: {spec.get('max_reference_images')}")
        lines.append(f"  Notes: {spec.get('notes')}")
    return "\n".join(lines)


@mcp.resource("media://outputs")
def get_outputs_resource() -> str:
    """Resource returning metadata about recently generated images and videos."""
    if not GENERATED_HISTORY:
        return "No media files generated in this session yet."
    lines = ["Recent Generated Media Files:"]
    for item in reversed(GENERATED_HISTORY[-20:]):
        lines.append(f"- [{item['type'].upper()}] {item['path']} (Model: {item['model']}) Prompt: '{item['prompt'][:60]}...'")
    return "\n".join(lines)


# 3. Register MCP Prompts
mcp.prompt()(configure_preferences_prompt)
mcp.prompt()(select_model_prompt)
mcp.prompt()(veo_director_prompt)
mcp.prompt()(veo_keyframe_storyboard_prompt)
mcp.prompt()(character_consistency_prompt)


def main():
    # Start embedded web studio server in background daemon thread (localhost:8989 or PORT env)
    try:
        from services.web_server import start_web_server_thread
        start_web_server_thread()
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to start web studio server: {e}\n")

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
