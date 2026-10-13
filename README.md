# Gemini & Veo Media MCP Server

A high-performance [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server providing seamless integration with Google's state-of-the-art generative media models:
- **Google Veo 3.1 & Gemini Omni**: Cinematic video generation with audio, keyframe interpolation, and character consistency.
- **Gemini Nano Banana (2.1 / Pro / Flash / Lite)**: High-resolution image generation, Google Search grounding, multi-turn editing, and reference mixing.
- **Asynchronous Non-Blocking Engine**: Zero-timeout architecture with background long-running operation (LRO) polling and persistent disk tracking.
- **Interactive First-Time Configuration**: Default preferences are unset initially; your AI assistant will ask you for your preferred model, resolution, and aspect ratio on first interaction and save them.

---

## Quick Installation (Recommended: Standalone .EXE)

You do **not** need Python, Git, or any virtual environment installed. Simply download the precompiled Windows standalone binary:

### Step 1: Download or Update the Executable

Download `gemini-media-mcp-standalone.exe` from the latest GitHub Release:

> **[Download Latest Standalone Executable (.exe)](https://github.com/rockvns/gemini-media-mcp/releases/latest/download/gemini-media-mcp-standalone.exe)**

#### Self-Update Command (PowerShell)
You can run this one-liner anytime in PowerShell to fetch or update to the latest release binary:

```powershell
Invoke-WebRequest -Uri "https://github.com/rockvns/gemini-media-mcp/releases/latest/download/gemini-media-mcp-standalone.exe" -OutFile "$HOME\Downloads\gemini-media-mcp-standalone.exe"
```

*Or using `curl.exe`:*
```cmd
curl.exe -L "https://github.com/rockvns/gemini-media-mcp/releases/latest/download/gemini-media-mcp-standalone.exe" -o "%USERPROFILE%\Downloads\gemini-media-mcp-standalone.exe"
```

---

### Step 2: Configure Your MCP Host

Add the server to your MCP client configuration and supply your **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/):

#### A. Google Antigravity IDE
Add to `%USERPROFILE%\.gemini\config\mcp_config.json`:

```json
{
  "mcpServers": {
    "gemini-media-mcp": {
      "command": "C:\\Users\\your_user\\Downloads\\gemini-media-mcp-standalone.exe",
      "env": {
        "GEMINI_API_KEY": "AIzaSyYourActualGeminiApiKeyHere"
      }
    }
  }
}
```

#### B. Claude Desktop
Add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gemini-media-mcp": {
      "command": "C:\\Users\\your_user\\Downloads\\gemini-media-mcp-standalone.exe",
      "env": {
        "GEMINI_API_KEY": "AIzaSyYourActualGeminiApiKeyHere"
      }
    }
  }
}
```

#### C. Cursor / VS Code (Cline / Roo Code)
Add to your client's MCP configuration (`cline_mcp_settings.json`):

```json
{
  "mcpServers": {
    "gemini-media-mcp": {
      "command": "C:/Users/your_user/Downloads/gemini-media-mcp-standalone.exe",
      "env": {
        "GEMINI_API_KEY": "AIzaSyYourActualGeminiApiKeyHere"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

> **Note**: In JSON configuration files, remember to escape backslashes (`\\`) or use forward slashes (`/`).

---

## User Preferences & First-Interaction Setup

To give you complete control over your creative setup:
1. **Unconfigured by Default:** Fresh installations do not enforce preset defaults (`video: null`, `image: null`).
2. **First Interaction Prompt:** On your very first generation request, your AI assistant will ask you for your preferred defaults:
   - Preferred video model (e.g., `veo-3.1-generate-preview`)
   - Preferred video resolution (`720p`, `1080p`, or `4k`) and aspect ratio (`16:9` or `9:16`)
   - Preferred image model (e.g., `gemini-nano-banana-2.1`) and resolution (`1K`, `2K`, `4K`)
3. **Persistent Memory:** Once configured, your choices are stored in `user_preferences.json` and remembered across sessions.
4. **Manage Anytime:** You can view or change your preferences at any time using:
   - `get_user_preferences`: View current settings.
   - `set_user_preferences`: Change defaults (e.g. set resolution to 1080p or change output folder).
   - `reset_user_preferences`: Reset preferences to unset.

---

## Core Features & Architecture

### 1. Zero-Timeout Asynchronous Video Generation
Video rendering with models like Veo 3.1 typically takes 45–120 seconds. Standard synchronous MCP tool calls often hit 30s–60s client timeouts.

* **Instant Dispatch:** `generate_video` dispatches the generation task to Google Cloud and returns in **< 1 second** with an `operation_id`.
* **Lightweight Polling:** The LLM periodically polls progress via `check_video_operation(operation_name="...")` in sub-second calls.
* **Persistent Disk Store (`active_operations.json`):** Tracks ongoing, completed, and failed jobs. Survives IDE restarts and client reconnections.
* **Inspect Active Jobs:** Call `list_active_operations()` anytime to check running jobs, elapsed rendering times, and output file locations.

### 2. Universal Exception Shielding
All tool calls are protected by an exception shield:
- Unhandled API errors (such as quota limits or expired keys) will **not** crash the MCP process (`EOF`).
- Diagnostic errors clearly explain the root cause and next steps:
  - `HTTP 401/403`: Clarifies API key authentication issues.
  - `HTTP 429 / RESOURCE_EXHAUSTED`: Advises on rate limits, backoff, and quota upgrades.
  - `HTTP 400`: Explains invalid parameters or unsupported aspect ratios.
  - `Safety Filters`: Details content moderation triggers and provides prompt rewriting advice.

### 3. Pre-Flight Health Diagnostic (`check_api_status` & CLI Script)
Run a diagnostic health check before starting heavy generation tasks:
- Verifies `GEMINI_API_KEY` format.
- Checks client connectivity and model availability.
- Validates output directory write permissions.
- Summarizes currently active operations.

You can also run the quick standalone CLI diagnostic anytime:
```powershell
python check_key_and_image.py
```
This tests your API key authentication, lists all accessible image models, and runs a test image generation with full error diagnostics.

---

## Supported Models Catalog

### Video Models
| Model ID | Name | Duration | Resolutions | Aspect Ratios | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `veo-3.1-generate-preview` | **Veo 3.1** *(Recommended)* | 8s | 720p, 1080p, 4k | 16:9, 9:16 | State-of-the-art with native audio & keyframe interpolation (0, 1, or 2 frames). |
| `gemini-omni-1.1-flash` | **Gemini Omni Flash** | 5s, 8s | Standard | 16:9 | Ultra-fast multimodal video generation. |
| `veo-3.0-generate-001` | **Veo 3.0 Standard** | 8s | 720p, 1080p | 16:9 | Standard generation. |
| `veo-3.0-fast-generate-001` | **Veo 3.0 Fast** | 8s | 720p | 16:9 | Optimized for high-speed creative iteration. |

### Image Models (Nano Banana)
| Model ID | Name | Resolutions | Search Grounding | Max References | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `gemini-nano-banana-2.1` | **Nano Banana 2.1** *(Recommended)* | 1K, 2K, 4K | Yes | Up to 14 | High efficiency with search grounding and multi-turn consistency. |
| `gemini-3-pro-image` | **Nano Banana Pro** | 1K, 2K, 4K | Yes | Up to 14 | Premium model for typography and brand consistency. |
| `gemini-3.1-flash-image` | **Nano Banana 2 Flash** | 512px, 1K, 2K, 4K | Yes | Up to 14 | Balanced workhorse supporting fast preview through 4K. |
| `gemini-3.1-flash-lite-image`| **Nano Banana 2 Lite** | 1K | No | Up to 14 | Lowest cost, high-speed generation. |

---

## Available MCP Tools Summary

| Tool | Description |
| :--- | :--- |
| `check_api_status` | Pre-flight diagnostic checking API key validity, output folder, and operations status. |
| `generate_video` | Non-blocking video generation command with keyframe support. Returns `operation_id` immediately. |
| `check_video_operation` | Checks status of an ongoing video generation operation and downloads the `.mp4` when ready. |
| `list_active_operations` | Lists all active, completed, or failed generation operations with elapsed times and file paths. |
| `generate_image` | Image generation using Gemini Nano Banana models with aspect ratio and size options. |
| `generate_keyframes` | Generates 1 opening keyframe or 2 consistent keyframes (start + end) for video interpolation. |
| `edit_image` | Modifies existing images conversationally using natural language instructions. |
| `get_user_preferences` | Displays saved default models, resolutions, aspect ratios, and active output directory. |
| `set_user_preferences` | Updates and persists default generation preferences to disk. |
| `reset_user_preferences` | Resets preferences back to unconfigured state. |
| `list_available_models` | Lists all available video and image models along with descriptions and recommendations. |
| `get_model_specifications`| Inspects supported resolutions, aspect ratios, and durations for a specific model. |

---

## License

This project is licensed under the MIT License.
