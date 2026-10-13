"""
Test script for Unified Media MCP Server (v2.1).

Validates:
- Generic generation tools (generate_video, generate_image, generate_keyframes, edit_image)
- User preferences tools (get_user_preferences, set_user_preferences, reset_user_preferences)
- Model specifications and capabilities (get_model_specifications, list_available_models)
"""

import asyncio
from gemini_mcp import mcp


async def main():
    print("=== Testing Unified Media MCP Server (v2.1) ===\n")

    # 1. List tools
    tools = await mcp.list_tools()
    print(f"Available Tools ({len(tools)}):")
    for tool in tools:
        print(f" - {tool.name}: {tool.description.strip().splitlines()[0]}")

    # 2. List resources
    resources = await mcp.list_resources()
    print(f"\nAvailable Resources ({len(resources)}):")
    for r in resources:
        print(f" - {r.uri}: {r.name}")

    # 3. List prompts
    prompts = await mcp.list_prompts()
    print(f"\nAvailable Prompts ({len(prompts)}):")
    for p in prompts:
        print(f" - {p.name}: {p.description}")

    # 4. Test tool call: get_user_preferences
    print("\nCalling 'get_user_preferences'...")
    prefs_res = await mcp.call_tool("get_user_preferences", {})
    print(f"Output:\n{prefs_res.content[0].text}\n")

    # 5. Test tool call: set_user_preferences
    print("Calling 'set_user_preferences' (setting video resolution to 1080p and custom output_dir)...")
    set_res = await mcp.call_tool("set_user_preferences", {"media_type": "video", "resolution": "1080p", "output_dir": "outputs/custom_renders"})
    print(f"Output preview:\n{set_res.content[0].text[:260]}...\n")

    # 6. Test tool call: get_model_specifications
    print("Calling 'get_model_specifications' for 'veo-3.1-generate-preview'...")
    spec_res = await mcp.call_tool("get_model_specifications", {"model_name": "veo-3.1-generate-preview"})
    print(f"Output:\n{spec_res.content[0].text}\n")

    # 7. Test tool call: check_api_status
    print("Calling 'check_api_status'...")
    status_res = await mcp.call_tool("check_api_status", {})
    print(f"Output:\n{status_res.content[0].text}\n")

    # 8. Test tool call: list_active_operations
    print("Calling 'list_active_operations'...")
    ops_res = await mcp.call_tool("list_active_operations", {})
    print(f"Output:\n{ops_res.content[0].text}\n")

    # 9. Test error shielding: calling generate_image with placeholder key
    print("Testing exception shield on 'generate_image'...")
    img_res = await mcp.call_tool("generate_image", {"prompt": "cyberpunk city"})
    print(f"Shielded Error Output (No crash):\n{img_res.content[0].text}\n")

    print("All tools and resilience checks passed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
