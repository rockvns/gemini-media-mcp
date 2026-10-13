"""
Tools package.
"""

from .preference_tools import register_preference_tools
from .video_tools import register_video_tools
from .image_tools import register_image_tools


def register_all_tools(mcp):
    """Register all tools on the MCP server instance."""
    register_preference_tools(mcp)
    register_video_tools(mcp)
    register_image_tools(mcp)


__all__ = [
    "register_all_tools",
    "register_preference_tools",
    "register_video_tools",
    "register_image_tools",
]
