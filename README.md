# Gemini & Veo Media MCP Server

A comprehensive [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server providing seamless integration with Google's state-of-the-art generative media models:
- **Google Veo 3.1 & Gemini Omni**: Native cinematic video generation with audio, keyframe interpolation, and character consistency.
- **Gemini Nano Banana (2.1 / Pro / Flash / Lite)**: High-resolution image generation, Google Search grounding, multi-turn editing, and reference mixing.
- **Persistent Preferences**: Remembers your preferred default models, aspect ratios, and resolutions across sessions.

---

## Features

### 1. Video Generation (`generate_video`)
* **Veo 3.1 (`veo-3.1-generate-preview`)**:
  - High-fidelity 8-second video with native sound effects and dialogue.
  - Resolutions: `720p`, `1080p`, and `4k`.
  - Aspect ratios: `16:9` (landscape) and `9:16` (portrait).
  - Flexible keyframe modes:
    - **0 Frames**: Text-to-video.
    - **1 Frame**: Image-to-video (starting keyframe).
    - **2 Frames**: Smooth transition interpolation between a start frame and end frame.
  - Character consistency: Attach up to 3 character/asset reference images.
* **Gemini Omni (`gemini-omni-1.1-flash`)**:
  - Ultra-fast multimodal video generation via the Interactions API.
* **Veo 3.0 Standard & Fast (`veo-3.0-generate-001`, `veo-3.0-fast-generate-001`)**:
  - Rapid iteration and testing.

### 2. Image Generation & Editing (`generate_image`, `edit_image`)
* **Nano Banana 2.1 (`gemini-nano-banana-2.1`)**:
  - Resolutions: `1K`, `2K`, and `4K`.
  - Aspect ratios: `1:1`, `3:2`, `2:3`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`.
  - Grounding: Optional real-time Google Web & Image Search grounding.
  - Reference mixing: Attach up to 14 references (up to 4 character reference images for identity consistency).
* **Nano Banana Pro (`gemini-3-pro-image`)**:
  - Premium precision for typography, complex layouts, and brand assets.
* **Nano Banana 2 Lite & Flash (`gemini-3.1-flash-lite-image`, `gemini-3.1-flash-image`)**:
  - High velocity, low latency image generation.
* **Conversational Editing (`edit_image`)**:
  - Describe edits in natural language to modify existing images conversationally.

### 3. Keyframe Storyboarding (`generate_keyframes`)
* Generates **1 frame** (start keyframe) or **2 frames** (start + end keyframes) with guaranteed character and scene continuity using the multi-turn Interactions API.
* Produced keyframes can be fed directly into `generate_video` for video interpolation.

### 4. Persistent User Preferences & Configurable Output Path
* **Output Path Precedence**:
  1. Explicit parameter `output_path` in tool call.
  2. Persisted preference `output_dir` in `user_preferences.json` (configurable via `set_user_preferences(output_dir="...")`).
  3. Environment variable `MEDIA_OUTPUT_DIR` or `OUTPUT_DIR` in `.env`.
  4. Default fallback: `./outputs/`
* Defaults for video models, image models, aspect ratios, and resolutions are saved in `user_preferences.json`.
* Pass `save_as_preference=True` on any generation call to update and remember those parameters for next time.

---

## Directory Structure

```text
google-flow/
├── .github/workflows/
│   └── build.yml              # CI/CD: Automated testing, PyInstaller builds & releases
├── gemini_mcp.py              # Main MCP server entrypoint
├── setup.py                   # Setuptools package configuration & CLI script
├── user_preferences.json     # Persisted user preferences
├── test_gemini_server.py      # Verification test suite
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (GEMINI_API_KEY)
├── .env.example               # Template environment file
├── .gitignore                 # Git ignore rules
│
├── config/                    # Configurations & preferences
│   ├── constants.py           # Model specifications & supported dimensions
│   └── preferences.py         # PreferencesManager (load, update, reset)
│
├── services/                  # Model execution services
│   ├── client.py              # GenAI client factory & path helpers
│   ├── veo_service.py         # Veo 3.1 video generation & operation polling
│   ├── omni_service.py        # Gemini Omni Flash video generation
│   └── nano_banana_service.py # Nano Banana image & keyframe generation
│
├── tools/                     # MCP Tool endpoints
│   ├── video_tools.py         # generate_video, check_video_operation
│   ├── image_tools.py         # generate_image, generate_keyframes, edit_image
│   └── preference_tools.py    # get/set/reset preferences, specifications discovery
│
├── prompts/                   # MCP Prompts
│   └── media_prompts.py       # Director, storyboard, and preference prompts
│
└── outputs/                   # Auto-created output directory for media files
```

---

## Setup & Installation

### 1. Prerequisites
- **Python**: Version 3.10 or higher.
- **Gemini API Key**: Obtain a free or paid API key from [Google AI Studio](https://aistudio.google.com/).
- **MCP Host**: Any MCP-compliant client such as **Google Antigravity IDE**, **Claude Desktop**, **Cursor**, or **VS Code** (with Cline/Roo Code).

---

### 2. Step-by-Step Installation

#### Step 1: Navigate to the Project Directory
```bash
cd d:\work\MCP\google-flow
```

#### Step 2: Create a Virtual Environment
```bash
# Create a local virtual environment named .venv
python -m venv .venv
```

#### Step 3: Activate the Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
  *(If script execution is disabled on PowerShell, first run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

- **Windows (Command Prompt / CMD)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```

- **Linux / macOS**:
  ```bash
  source .venv/bin/activate
  ```

#### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 5: Configure Environment Variables
Copy the template `.env.example` to `.env`:
```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux / macOS / Git Bash
cp .env.example .env
```

Open `.env` in your editor and provide your Gemini API key:
```ini
# Required: Google Gemini API Key
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Optional: Directory for generated media (defaults to ./outputs/)
MEDIA_OUTPUT_DIR=outputs
```

---

### 3. Verification & Self-Test

Before integrating with your MCP host, verify that all dependencies and tool definitions load cleanly:

```bash
python test_gemini_server.py
```

You should see:
```text
=== Testing Unified Media MCP Server (v2.1) ===
Available Tools (10):
 - get_user_preferences
 - set_user_preferences
 - reset_user_preferences
 - get_model_specifications
 - list_available_models
 - generate_video
 - check_video_operation
 - generate_image
 - generate_keyframes
 - edit_image
...
All tools and preference management checks passed successfully!
```

---

## MCP Server Host Configuration

Add `gemini-media-mcp` to your MCP client configuration file so your AI assistant can discover and call its tools.

### A. Google Antigravity IDE

Open or create your Antigravity MCP configuration file:
- **Global Config Path (Windows)**: `%USERPROFILE%\.gemini\config\mcp_config.json`
- **Global Config Path (macOS/Linux)**: `~/.gemini/config/mcp_config.json`
- **Or Workspace Config**: `.agents/mcp_config.json` inside your project root.

Add the following entry under `mcpServers`:

```json
{
  "mcpServers": {
    "gemini-media-mcp": {
      "command": "D:\\work\\MCP\\google-flow\\.venv\\Scripts\\python.exe",
      "args": [
        "D:\\work\\MCP\\google-flow\\gemini_mcp.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_actual_gemini_api_key_here"
      }
    }
  }
}
```

> **Note**: On Windows, JSON strings require double backslashes (`\\`) in file paths.

---

### B. Claude Desktop

Configuration file locations:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the server definition:

```json
{
  "mcpServers": {
    "gemini-media-mcp": {
      "command": "D:\\work\\MCP\\google-flow\\.venv\\Scripts\\python.exe",
      "args": [
        "D:\\work\\MCP\\google-flow\\gemini_mcp.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_actual_gemini_api_key_here"
      }
    }
  }
}
```
*Restart Claude Desktop after updating the config.*

---

### C. Cursor / VS Code (Cline / Roo-Code)

In your client's MCP settings configuration (`cline_mcp_settings.json` or equivalent):

```json
{
  "mcpServers": {
    "gemini-media-mcp": {
      "command": "D:/work/MCP/google-flow/.venv/Scripts/python.exe",
      "args": [
        "D:/work/MCP/google-flow/gemini_mcp.py"
      ],
      "env": {
        "GEMINI_API_KEY": "your_actual_gemini_api_key_here"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

---

## Troubleshooting & Tips

- **`GEMINI_API_KEY is not set`**:
  Make sure your key is populated in `.env` within the `google-flow/` root directory, or explicitly passed in the `"env"` object of `mcp_config.json`.
- **PowerShell Script Restriction (`Activate.ps1 cannot be loaded`)**:
  Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in your PowerShell window, then retry `.venv\Scripts\Activate.ps1`.
- **Invalid JSON Escape Sequences**:
  In Windows paths inside JSON files, make sure to escape backslashes (e.g. `D:\\work\\...`) or use forward slashes (`D:/work/...`).
- **Python Path**:
  Ensure `command` points directly to the virtual environment's Python executable (`.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on Unix).

---

## Packaging as Standalone Executable (.exe)

You can package this server into a standalone Windows `.exe` using [PyInstaller](https://pyinstaller.org/) to ship and distribute it without requiring Python on the target machine.

### 1. Install PyInstaller
```powershell
pip install pyinstaller
```

### 2. Build the Executable

#### Option A: One-Directory Distribution (Recommended for lower startup latency)
```powershell
pyinstaller --noconfirm --onedir --console `
  --name "gemini_mcp" `
  --collect-all "mcp" `
  --collect-all "google.genai" `
  gemini_mcp.py
```
This generates a `dist/gemini_mcp/` directory containing `gemini_mcp.exe` and all bundled dependencies.

#### Option B: Single Standalone File
```powershell
pyinstaller --noconfirm --onefile --console `
  --name "gemini_mcp" `
  --collect-all "mcp" `
  --collect-all "google.genai" `
  gemini_mcp.py
```
This produces a single portable `dist/gemini_mcp.exe`.

### 3. Using the `.exe` in MCP Clients

In your client's `mcp_config.json`, simply set `command` to the executable path and pass `args` as an empty list:

```json
{
  "mcpServers": {
    "gemini-media-mcp": {
      "command": "D:\\work\\MCP\\google-flow\\dist\\gemini_mcp\\gemini_mcp.exe",
      "args": [],
      "env": {
        "GEMINI_API_KEY": "your_actual_gemini_api_key_here"
      }
    }
  }
}
```

> **Important Notes for Packaging**:
> - **Must use `--console`**: Do **not** use `--windowed` or `--noconsole`. MCP communicates over standard input / standard output (`stdio`) for JSON-RPC.
> - **Persistence**: When running as an `.exe`, `user_preferences.json` and generated `outputs/` are automatically saved in the folder alongside the executable.

---

## Automated CI/CD & GitHub Actions

This repository includes a continuous integration and release pipeline configured in [`.github/workflows/build.yml`](.github/workflows/build.yml):

### 1. Automated Matrix Testing
- Triggered on every `push` to `main` and all `pull_request` events.
- Executes the self-test validation suite (`test_gemini_server.py`) across **Python 3.10, 3.11, and 3.12** on Windows runners.

### 2. Automated Binary & Package Builds
- Automatically builds:
  - **Windows Directory Distribution**: `gemini-media-mcp-windows-x64.zip`
  - **Windows Single-File Standalone**: `gemini-media-mcp-standalone.exe`
  - **Python Package Wheels & Sdist**: `.whl` and `.tar.gz`
- Uploads all builds as downloadable GitHub workflow artifacts.

### 3. Automated GitHub Releases
Tagging a release automatically generates a new GitHub Release with all binary assets attached:

```bash
# Tag a new release version
git tag v2.2.0

# Push the tag to GitHub to trigger release workflow
git push origin v2.2.0
```

GitHub Actions will automatically test, compile, package, and attach the pre-built executables directly to the release page.

---

## MCP Tools Reference

| Tool | Description | Key Parameters |
| :--- | :--- | :--- |
| **`generate_video`** | Generates video with audio using Veo 3.1 or Omni | `prompt`, `model`, `first_frame_path`, `last_frame_path`, `character_paths`, `aspect_ratio`, `resolution`, `save_as_preference` |
| **`check_video_operation`**| Polls ongoing video generation and downloads video | `operation_name`, `output_path` |
| **`generate_image`** | Generates high-quality images using Nano Banana | `prompt`, `model`, `character_paths`, `aspect_ratio`, `image_size`, `enable_google_search`, `save_as_preference` |
| **`generate_keyframes`** | Generates 1 or 2 keyframes with continuity | `start_prompt`, `end_prompt`, `num_frames` (1 or 2), `character_paths`, `aspect_ratio` |
| **`edit_image`** | Modifies existing image conversationally | `prompt`, `image_path`, `model`, `aspect_ratio` |
| **`get_user_preferences`**| Displays current saved video & image defaults | *(None)* |
| **`set_user_preferences`**| Updates and saves default preferences | `media_type` ('video'/'image'), `model`, `aspect_ratio`, `resolution`, `image_size` |
| **`reset_user_preferences`**| Resets preferences back to defaults | *(None)* |
| **`get_model_specifications`**| Shows supported resolutions, ratios, and limits | `model_name` *(optional)* |
| **`list_available_models`**| Lists available video and image models | `media_type` ('all'/'video'/'image') |

---

## MCP Resources & Prompts

### Resources
- **`media://preferences`**: Read the user's active defaults.
- **`media://models`**: Comprehensive catalog of supported models, formats, and limits.
- **`media://outputs`**: History of recently generated files during the session.

### Prompts
- **`select_model_prompt`**: Interactively evaluates your goal and recommends the best model.
- **`configure_preferences_prompt`**: Guided questionnaire to customize and save your defaults.
- **`veo_director_prompt`**: Expands concepts into cinematography-grade prompts (camera angle, lighting, audio).
- **`veo_keyframe_storyboard_prompt`**: Crafts smooth transition prompts bridging two keyframes.
- **`character_consistency_prompt`**: Formulates prompts preserving identity with attached character images.

---

## Testing

Verify the server and tool registrations by running:

```bash
python test_gemini_server.py
```

Expected output:
```text
=== Testing Unified Media MCP Server (v2.1) ===

Available Tools (10):
 - get_user_preferences
 - set_user_preferences
 - reset_user_preferences
 - get_model_specifications
 - list_available_models
 - generate_video
 - check_video_operation
 - generate_image
 - generate_keyframes
 - edit_image

Available Resources (3):
 - media://preferences
 - media://models
 - media://outputs

Available Prompts (5):
 - configure_preferences_prompt
 - select_model_prompt
 - veo_director_prompt
 - veo_keyframe_storyboard_prompt
 - character_consistency_prompt

All tools and preference management checks passed successfully!
```

---

## License
MIT
