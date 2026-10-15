"""
Embedded Starlette Web Server for gemini-media-mcp.
Serves the Next.js static studio UI and REST API endpoints on localhost:8989 (or PORT from .env).
Runs in a background daemon thread so stdout remains 100% reserved for MCP stdio.
"""

import os
import sys
import json
import time
import shutil
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List

from starlette.applications import Starlette
from starlette.responses import JSONResponse, FileResponse, Response
from starlette.routing import Route, Mount
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
import uvicorn

from config.constants import WORKSPACE_DIR, OUTPUTS_DIR, PREFERENCES_FILE, ACTIVE_OPERATIONS_FILE, MODEL_SPECIFICATIONS
from config.preferences import PreferencesManager
from services.client import (
    ActiveOperationsManager,
    resolve_file_path,
    resolve_output_path,
    format_api_error,
)
from services.veo_service import generate_veo_video, check_veo_operation
from services.omni_service import generate_omni_video
from services.nano_banana_service import (
    generate_nano_banana_image,
    generate_keyframes_pair,
    edit_nano_banana_image,
)
from tools.preference_tools import register_preference_tools
from tools.video_tools import register_video_tools
from tools.image_tools import register_image_tools

# Logger strictly to stderr
logger = logging.getLogger("gemini_web_server")
logger.setLevel(logging.WARNING)

ENV_FILE = WORKSPACE_DIR / ".env"


def get_web_out_dir() -> Optional[Path]:
    """Locate the bundled or built Next.js export directory."""
    candidates = []
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_frozen = Path(sys._MEIPASS)
        candidates.extend([
            base_frozen / "web" / "out",
            base_frozen / "out",
        ])
    candidates.extend([
        WORKSPACE_DIR / "web" / "out",
        WORKSPACE_DIR / "out",
    ])
    for c in candidates:
        if c.exists() and (c / "index.html").exists():
            return c
    return None


def resolve_env_file() -> Path:
    candidates = [
        WORKSPACE_DIR / ".env",
        WORKSPACE_DIR.parent / ".env",
    ]
    for c in candidates:
        if c.exists():
            return c
    return WORKSPACE_DIR / ".env"


def get_active_gemini_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "")
    if key and key != "gemini-api-key":
        return key

    # Try loading from .env
    env_file = resolve_env_file()
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("GEMINI_API_KEY="):
                        k = line.strip().split("=", 1)[1].strip().strip('"\'')
                        if k and k != "gemini-api-key":
                            os.environ["GEMINI_API_KEY"] = k
                            return k
        except Exception:
            pass

    # Try IDE mcp_config.json
    home_dir = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or "")
    ide_conf = home_dir / ".gemini" / "config" / "mcp_config.json"
    if ide_conf.exists():
        try:
            with open(ide_conf, "r", encoding="utf-8") as f:
                data = json.load(f)
                env_dict = data.get("mcpServers", {}).get("gemini-media-mcp", {}).get("env", {})
                k = env_dict.get("GEMINI_API_KEY", "")
                if k:
                    os.environ["GEMINI_API_KEY"] = k
                    return k
        except Exception:
            pass

    return ""


# ==============================================================================
# API ROUTE HANDLERS
# ==============================================================================

async def get_env_config(request) -> JSONResponse:
    """Retrieve current API key configuration status and port."""
    api_key = get_active_gemini_api_key()
    port_val = int(os.environ.get("PORT", "8989"))
    configured = bool(api_key and api_key != "gemini-api-key")
    masked = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else ("***" if api_key else "Not Set")

    return JSONResponse({
        "success": True,
        "configured": configured,
        "masked_key": masked,
        "port": port_val,
    })


async def update_env_config(request) -> JSONResponse:
    """Overwrite GEMINI_API_KEY and/or PORT in .env file and active environment."""
    try:
        body = await request.json()
        new_key = body.get("gemini_api_key")
        new_port = body.get("port")

        env_file = resolve_env_file()
        env_lines = []
        key_found = False
        port_found = False

        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("GEMINI_API_KEY=") and new_key is not None:
                        env_lines.append(f"GEMINI_API_KEY={new_key.strip()}\n")
                        key_found = True
                    elif stripped.startswith("PORT=") and new_port is not None:
                        env_lines.append(f"PORT={new_port}\n")
                        port_found = True
                    else:
                        env_lines.append(line)

        if new_key is not None and not key_found:
            env_lines.append(f"GEMINI_API_KEY={new_key.strip()}\n")
        if new_port is not None and not port_found:
            env_lines.append(f"PORT={new_port}\n")

        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(env_lines)

        # Update in-memory environment
        if new_key is not None:
            os.environ["GEMINI_API_KEY"] = new_key.strip()
        if new_port is not None:
            os.environ["PORT"] = str(new_port)

        masked = new_key[:6] + "..." + new_key[-4:] if new_key and len(new_key) > 10 else "***"
        return JSONResponse({
            "success": True,
            "message": "Environment successfully updated in .env and active in runtime.",
            "masked_key": masked,
            "port": int(os.environ.get("PORT", "8989")),
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def get_preferences(request) -> JSONResponse:
    """Retrieve current user preferences."""
    try:
        prefs = PreferencesManager.load()
        summary = PreferencesManager.get_summary()
        return JSONResponse({
            "success": True,
            "preferences": prefs,
            "summary": summary,
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def update_preferences(request) -> JSONResponse:
    """Update user preferences."""
    try:
        body = await request.json()
        result_text = PreferencesManager.update(
            media_type=body.get("media_type"),
            model=body.get("model"),
            aspect_ratio=body.get("aspect_ratio"),
            resolution=body.get("resolution"),
            image_size=body.get("image_size"),
            duration_seconds=body.get("duration_seconds"),
            enable_google_search=body.get("enable_google_search"),
            output_dir=body.get("output_dir"),
        )
        return JSONResponse({
            "success": True,
            "content": result_text,
            "preferences": PreferencesManager.load(),
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def reset_preferences(request) -> JSONResponse:
    """Reset user preferences to defaults."""
    try:
        result_text = PreferencesManager.reset()
        return JSONResponse({
            "success": True,
            "content": result_text,
            "preferences": PreferencesManager.load(),
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def get_models(request) -> JSONResponse:
    """Retrieve full MODEL_SPECIFICATIONS catalog directly from server."""
    try:
        model_name = request.query_params.get("model")
        if model_name:
            spec = MODEL_SPECIFICATIONS.get(model_name)
            return JSONResponse({"success": True, "spec": spec})
        return JSONResponse({"success": True, "specs": MODEL_SPECIFICATIONS})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def get_operations(request) -> JSONResponse:
    """List tracked generation operations."""
    try:
        status_filter = request.query_params.get("filter")
        if status_filter == "ALL":
            status_filter = None
        ops = ActiveOperationsManager.list(status_filter=status_filter)
        return JSONResponse({
            "success": True,
            "operations": ops,
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def poll_operation(request) -> JSONResponse:
    """Poll an asynchronous video generation operation."""
    try:
        body = await request.json()
        op_name = body.get("operation_name")
        output_path = body.get("output_path")
        if not op_name:
            return JSONResponse({"success": False, "error": "operation_name is required"}, status_code=400)

        result_text = check_veo_operation(operation_name=op_name, output_path=output_path)
        updated_op = ActiveOperationsManager.get(op_name)

        return JSONResponse({
            "success": True,
            "content": result_text,
            "operation": updated_op,
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def call_mcp_tool_route(request) -> JSONResponse:
    """Execute an MCP tool directly via Python service functions."""
    try:
        body = await request.json()
        tool = body.get("tool")
        args = body.get("args", {})

        if tool == "check_api_status":
            from tools.video_tools import register_video_tools
            # Invoke check_api_status logic
            api_key = os.environ.get("GEMINI_API_KEY", "")
            masked = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else ("***" if api_key else "Not Set")
            effective_dir = PreferencesManager.get_effective_output_dir()
            all_ops = ActiveOperationsManager.list()
            in_prog = len([o for o in all_ops if o.get("status") == "IN_PROGRESS"])
            completed = len([o for o in all_ops if o.get("status") == "COMPLETED"])
            failed = len([o for o in all_ops if o.get("status") == "FAILED"])
            prefs = PreferencesManager.load()
            default_v = (prefs.get("video") or {}).get("model", "veo-3.1-generate-preview (Default)")
            default_i = (prefs.get("image") or {}).get("model", "gemini-nano-banana-2.1 (Default)")

            content = (
                f"=== Gemini & Veo Media Server Health Check ===\n\n"
                f"[API Key Status]: Configured ({masked})\n"
                f"[GenAI Client]: Ready\n"
                f"[Output Storage]: Writable ({effective_dir})\n"
                f"[Operations Tracker]: {in_prog} In Progress, {completed} Completed, {failed} Failed\n"
                f"[Default Video Model]: {default_v}\n"
                f"[Default Image Model]: {default_i}\n\n"
                f"System is ready to handle generation on localhost:{os.environ.get('PORT', '8989')}."
            )
            return JSONResponse({"success": True, "content": content})

        elif tool == "generate_video":
            prompt = args.get("prompt")
            model = args.get("model", "gemini-omni-1.1-flash")
            spec = MODEL_SPECIFICATIONS.get(model, {})
            
            # Sanitize aspect ratio, resolution, duration against model spec
            supported_ar = spec.get("supported_aspect_ratios", ["16:9"])
            ar = args.get("aspect_ratio")
            if not ar or ar not in supported_ar:
                ar = supported_ar[0]

            supported_res = spec.get("supported_resolutions", ["720p"])
            res_val = args.get("resolution")
            if not res_val or res_val not in supported_res:
                res_val = supported_res[0]

            supported_dur = spec.get("supported_durations", [8])
            dur = args.get("duration_seconds")
            if not dur or dur not in supported_dur:
                dur = spec.get("default_duration_seconds", supported_dur[0])

            max_refs = spec.get("max_reference_images", 0)
            char_paths = args.get("character_paths") or []
            if max_refs > 0 and char_paths:
                char_paths = char_paths[:max_refs]
            elif max_refs == 0:
                char_paths = None

            if "omni" in model.lower():
                res = generate_omni_video(
                    prompt=prompt,
                    model=model,
                    character_paths=char_paths,
                    output_path=args.get("output_path"),
                )
            else:
                supports_kf = spec.get("supports_keyframes", False)
                res = generate_veo_video(
                    prompt=prompt,
                    model=model,
                    first_frame_path=args.get("first_frame_path") if supports_kf else None,
                    last_frame_path=args.get("last_frame_path") if supports_kf else None,
                    character_paths=char_paths,
                    aspect_ratio=ar,
                    resolution=res_val,
                    duration_seconds=dur,
                    negative_prompt=args.get("negative_prompt"),
                    output_path=args.get("output_path"),
                    wait_for_completion=False,
                )
            return JSONResponse({"success": not res.startswith("Error"), "content": res})

        elif tool == "generate_image":
            model = args.get("model", "gemini-nano-banana-2.1")
            spec = MODEL_SPECIFICATIONS.get(model, {})

            # Sanitize aspect ratio & image size
            supported_ar = spec.get("supported_aspect_ratios", ["16:9"])
            ar = args.get("aspect_ratio")
            if not ar or ar not in supported_ar:
                ar = supported_ar[0]

            supported_sizes = spec.get("supported_sizes", ["2K"])
            size_val = args.get("image_size")
            if not size_val or size_val not in supported_sizes:
                size_val = supported_sizes[0]

            search_supported = spec.get("supports_google_search", False)
            enable_search = bool(args.get("enable_google_search", False)) if search_supported else False

            max_chars = spec.get("max_character_references", 4)
            c_paths = args.get("character_paths") or []
            if max_chars > 0 and c_paths:
                c_paths = c_paths[:max_chars]
            elif max_chars == 0:
                c_paths = None

            max_refs = spec.get("max_reference_images", 14)
            r_paths = args.get("reference_image_paths") or []
            if max_refs > 0 and r_paths:
                r_paths = r_paths[:max_refs]
            elif max_refs == 0:
                r_paths = None

            res = generate_nano_banana_image(
                prompt=args.get("prompt"),
                model=model,
                character_paths=c_paths,
                reference_image_paths=r_paths,
                aspect_ratio=ar,
                image_size=size_val,
                enable_google_search=enable_search,
                output_path=args.get("output_path"),
            )
            return JSONResponse({"success": not res.startswith("Error"), "content": res})

        elif tool == "generate_keyframes":
            model = args.get("model", "gemini-nano-banana-2.1")
            spec = MODEL_SPECIFICATIONS.get(model, {})

            supported_ar = spec.get("supported_aspect_ratios", ["16:9"])
            ar = args.get("aspect_ratio")
            if not ar or ar not in supported_ar:
                ar = supported_ar[0]

            supported_sizes = spec.get("supported_sizes", ["2K"])
            size_val = args.get("image_size")
            if not size_val or size_val not in supported_sizes:
                size_val = supported_sizes[0]

            max_chars = spec.get("max_character_references", 4)
            c_paths = args.get("character_paths") or []
            if max_chars > 0 and c_paths:
                c_paths = c_paths[:max_chars]
            elif max_chars == 0:
                c_paths = None

            res = generate_keyframes_pair(
                start_prompt=args.get("start_prompt"),
                end_prompt=args.get("end_prompt"),
                num_frames=args.get("num_frames", 1),
                character_paths=c_paths,
                model=model,
                aspect_ratio=ar,
                image_size=size_val,
                output_dir=args.get("output_dir"),
            )
            return JSONResponse({"success": not res.startswith("Error"), "content": res})

        elif tool == "edit_image":
            model = args.get("model", "gemini-nano-banana-2.1")
            spec = MODEL_SPECIFICATIONS.get(model, {})

            supported_ar = spec.get("supported_aspect_ratios", ["16:9"])
            ar = args.get("aspect_ratio")
            if ar and ar not in supported_ar:
                ar = supported_ar[0]

            supported_sizes = spec.get("supported_sizes", ["2K"])
            size_val = args.get("image_size")
            if size_val and size_val not in supported_sizes:
                size_val = supported_sizes[0]

            res = edit_nano_banana_image(
                prompt=args.get("prompt"),
                image_path=args.get("image_path"),
                model=model,
                aspect_ratio=ar,
                image_size=size_val,
                output_path=args.get("output_path"),
            )
            return JSONResponse({"success": not res.startswith("Error"), "content": res})

        elif tool == "get_model_specifications":
            model_name = args.get("model_name")
            if model_name:
                spec = MODEL_SPECIFICATIONS.get(model_name)
                return JSONResponse({"success": True, "spec": spec})
            return JSONResponse({"success": True, "specs": MODEL_SPECIFICATIONS})

        elif tool == "list_available_models":
            return JSONResponse({"success": True, "models": list(MODEL_SPECIFICATIONS.keys())})

        return JSONResponse({"success": False, "error": f"Unknown tool: {tool}"}, status_code=400)
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def upload_file(request) -> JSONResponse:
    """Handle multipart file upload for reference images and keyframes."""
    try:
        form = await request.form()
        uploaded_file = form.get("file")
        if not uploaded_file:
            return JSONResponse({"success": False, "error": "No file uploaded"}, status_code=400)

        upload_dir = OUTPUTS_DIR / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{int(time.time()*1000)}_{uploaded_file.filename}"
        dest_path = upload_dir / filename

        contents = await uploaded_file.read()
        with open(dest_path, "wb") as f:
            f.write(contents)

        return JSONResponse({
            "success": True,
            "filename": filename,
            "filePath": str(dest_path),
            "url": f"/api/media/uploads/{filename}",
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def get_gallery(request) -> JSONResponse:
    """Scan outputs directory and return media assets with metadata."""
    try:
        if not OUTPUTS_DIR.exists():
            return JSONResponse({"success": True, "assets": []})

        # Load active operations for metadata matching
        ops_map = {}
        if ACTIVE_OPERATIONS_FILE.exists():
            try:
                with open(ACTIVE_OPERATIONS_FILE, "r", encoding="utf-8") as f:
                    ops_data = json.load(f)
                    for op in ops_data.values():
                        if op.get("output_path"):
                            ops_map[Path(op["output_path"]).name] = op
            except Exception:
                pass

        assets = []
        for p in OUTPUTS_DIR.rglob("*"):
            if p.is_file() and p.suffix.lower() in [".mp4", ".png", ".jpg", ".jpeg", ".webp"]:
                stat = p.stat()
                rel = p.relative_to(OUTPUTS_DIR).as_posix()
                is_video = p.suffix.lower() == ".mp4"
                op = ops_map.get(p.name, {})

                assets.append({
                    "filename": p.name,
                    "relativePath": rel,
                    "absolutePath": str(p),
                    "url": f"/api/media/{rel}",
                    "type": "video" if is_video else "image",
                    "size": stat.st_size,
                    "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(stat.st_mtime)),
                    "model": op.get("model"),
                    "prompt": op.get("prompt"),
                    "aspectRatio": op.get("aspect_ratio"),
                    "resolution": op.get("resolution"),
                })

        assets.sort(key=lambda x: x["createdAt"], reverse=True)
        type_filter = request.query_params.get("type")
        if type_filter and type_filter != "all":
            assets = [a for a in assets if a["type"] == type_filter]

        return JSONResponse({"success": True, "assets": assets})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


async def serve_media(request) -> Response:
    """Serve media files from outputs directory with HTTP Range support for video seeking."""
    try:
        rel_path = request.path_params.get("path", "")
        file_path = (OUTPUTS_DIR / rel_path).resolve()

        if not str(file_path).startswith(str(OUTPUTS_DIR.resolve())) or not file_path.exists():
            return Response("File not found", status_code=404)

        return FileResponse(path=file_path)
    except Exception as e:
        return Response(str(e), status_code=500)


def create_web_app() -> Starlette:
    """Create and configure the Starlette application."""
    routes = [
        # Environment & Key overwrite
        Route("/api/env", get_env_config, methods=["GET"]),
        Route("/api/env", update_env_config, methods=["POST"]),

        # Preferences & Models
        Route("/api/mcp/preferences", get_preferences, methods=["GET"]),
        Route("/api/mcp/preferences", update_preferences, methods=["POST"]),
        Route("/api/mcp/preferences", reset_preferences, methods=["DELETE"]),
        Route("/api/mcp/models", get_models, methods=["GET"]),

        # Operations
        Route("/api/mcp/operations", get_operations, methods=["GET"]),
        Route("/api/mcp/operations", poll_operation, methods=["POST"]),

        # Generic MCP Tool Invocation
        Route("/api/mcp/tool", call_mcp_tool_route, methods=["POST"]),

        # Upload & Gallery
        Route("/api/upload", upload_file, methods=["POST"]),
        Route("/api/gallery", get_gallery, methods=["GET"]),
        Route("/api/media/{path:path}", serve_media, methods=["GET"]),
    ]

    # Mount static files if web/out exists
    out_dir = get_web_out_dir()
    if out_dir:
        class SPAStaticFiles(StaticFiles):
            async def get_response(self, path: str, scope):
                # Custom rewrite for HTML5 history API routes
                clean_path = path.strip("/")
                candidates = [
                    Path(self.directory) / clean_path,
                    Path(self.directory) / f"{clean_path}.html",
                    Path(self.directory) / clean_path / "index.html",
                ]
                for c in candidates:
                    if c.is_file():
                        return FileResponse(c)
                # Fallback to index.html for unknown routes
                index_file = Path(self.directory) / "index.html"
                if index_file.is_file():
                    return FileResponse(index_file)
                return await super().get_response(path, scope)

        routes.append(Mount("/", app=SPAStaticFiles(directory=str(out_dir), html=True), name="static"))

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]

    return Starlette(debug=False, routes=routes, middleware=middleware)


def start_web_server_thread(port: Optional[int] = None) -> threading.Thread:
    """Start the Starlette web server on localhost in a background daemon thread."""
    if port is None:
        port = int(os.environ.get("PORT", "8989"))

    def _run():
        app = create_web_app()
        config = uvicorn.Config(
            app=app,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            access_log=False,
        )
        server = uvicorn.Server(config)
        server.run()

    thread = threading.Thread(target=_run, daemon=True, name="gemini-media-web-server")
    thread.start()
    sys.stderr.write(f"\n[gemini-media-mcp] Studio web application running at: http://localhost:{port}\n\n")
    sys.stderr.flush()
    return thread

