# Gemini Flow Studio (Next.js MCP Web Application)

A full-featured creative media generation studio built with **Next.js 16**, **React 19**, **Tailwind CSS**, and the official **`@modelcontextprotocol/sdk`**, connecting directly to the **Gemini & Veo MCP Server**.

---

## Features

### 1. 🎬 Video Generation Studio (`/video`)
- **Full Model Support**: Google Veo 3.1 (`veo-3.1-generate-preview`), Gemini Omni 1.1 Flash (`gemini-omni-1.1-flash`), Veo 3.0 Standard, and Veo 3.0 Fast.
- **Keyframe Modes**:
  - **0 Frames**: Pure text-to-video with native audio synthesis.
  - **1 Frame**: Image-to-video animation starting from an uploaded image or gallery asset.
  - **2 Frames**: Smooth keyframe interpolation bridging start and end frames.
- **Character Consistency Anchors**: Attach up to 3 character photos to preserve identity.
- **Cinematography Controls**: Aspect ratio (`16:9`, `9:16`), resolution (`standard`, `720p`, `1080p`, `4k`), duration (`5s`, `8s`), and negative prompts.
- **Veo Director Assistant**: Interactive modal to construct cinematographic shot compositions with camera motion, lighting atmosphere, and sound design.
- **Zero-Timeout Asynchronous Execution**: Non-blocking dispatch with sub-second return, background polling, and real-time elapsed second counter.

### 2. 🎨 Image Studio (`/image`)
- **Full Model Support**: Gemini Nano Banana 2.1 (`gemini-nano-banana-2.1`), Nano Banana Pro (`gemini-3-pro-image`), Flash Image (`gemini-3.1-flash-image`), Flash Lite (`gemini-3.1-flash-lite-image`), and Legacy.
- **Aspect Ratio Matrix**: 10 ratios (`1:1`, `3:2`, `2:3`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`).
- **Resolutions & Sizes**: `512px`, `1K`, `2K`, and `4K`.
- **Google Search Grounding**: Live factual web grounding toggle for accurate real-time data.
- **Multi-Reference Anchors**: Up to 4-5 character references and up to 14 style references.
- **Specialized Workflows**:
  - **Standard Generation**: Text + reference images.
  - **Keyframe Pair Generator**: Start prompt + end prompt to produce consistent opening and ending frames for Veo interpolation, with one-click "Use as Keyframe" handoff.
  - **Conversational Image Editor**: Select any image, describe natural language modifications, and compare before/after.

### 3. ⚡ Operations & Task Monitor (`/operations`)
- Live dashboard backed by `active_operations.json` and MCP tool `list_active_operations`.
- Status filtering: `ALL`, `IN_PROGRESS`, `COMPLETED`, `FAILED`.
- Direct polling trigger, elapsed timer, copyable operation IDs, and embedded video playback.

### 4. 🖼️ Media Gallery (`/gallery`)
- Real-time asset browser reading generated files from `outputs/`.
- Video player and image lightbox with zoom and metadata viewer.
- Quick actions: "Use as Starting Keyframe", "Use as Ending Keyframe", "Edit Image", and Download.

### 5. ⚙️ Preferences & Diagnostics Menu (`/settings`)
- Interactive manager for `user_preferences.json`:
  - Default video model, resolution, aspect ratio, duration.
  - Default image model, size, aspect ratio, search grounding.
  - Custom output directory configuration.
- **Pre-flight Health Diagnostics**: Runs `check_api_status` to verify API key validity, GenAI client readiness, output folder permissions, and operation stats.
- **Reset Defaults** button to restore baseline settings.

---

## Getting Started

### Prerequisites
- Node.js (v20+ or v24+)
- `pnpm.cmd`
- Python 3.10+ virtual environment in `../.venv` with MCP server dependencies

### Run Development Server
```powershell
pnpm.cmd dev
```

### Run Production Server
```powershell
pnpm.cmd build
pnpm.cmd start --port 3000
```

Open [http://localhost:3000](http://localhost:3000) in your browser.
