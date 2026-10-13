"""
Diagnostic script to test Gemini API key connection and image generation.
Usage:
    python check_key_and_image.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure workspace .env is loaded
WORKSPACE_DIR = Path(__file__).resolve().parent
load_dotenv(WORKSPACE_DIR / ".env")


def main():
    print("=" * 60)
    print("    Gemini API Key & Image Generation Diagnostic")
    print("=" * 60)

    # 1. Check API Key configuration
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "gemini-api-key":
        print("\n[FAILED] GEMINI_API_KEY is not set or is using a placeholder.")
        print(f"Please configure your API key in: {WORKSPACE_DIR / '.env'}")
        print("Standard Google AI Studio keys start with 'AIzaSy...'.")
        sys.exit(1)

    masked_key = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
    key_type = "Standard Google AI Studio Key" if api_key.startswith("AIzaSy") else "Custom / Service Key format"
    print(f"\n[OK] API Key found: {masked_key} ({key_type})")

    # 2. Test Client Initialization & Connectivity
    print("\n[Step 1/3] Testing Google GenAI Client connection...")
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        # Test basic connection by fetching model info
        models = list(client.models.list())
        print(f"[OK] Connection successful! Found {len(models)} accessible models.")
    except Exception as exc:
        print(f"\n[FAILED] Could not connect to Google GenAI API.")
        print(f"Error: {exc}")
        sys.exit(1)

    # 3. Discover Image Models
    print("\n[Step 2/3] Checking available image generation models...")
    image_models = [
        m.name.replace("models/", "")
        for m in models
        if any(term in m.name.lower() for term in ["image", "banana", "imagen"])
    ]

    if image_models:
        print(f"[OK] Available Image Models ({len(image_models)}):")
        for m in image_models:
            print(f"  - {m}")
    else:
        print("  - No models explicitly tagged 'image' found; will use 'gemini-nano-banana-2.1'.")

    # Choose primary model
    test_model = "gemini-nano-banana-2.1" if "gemini-nano-banana-2.1" in image_models else (image_models[0] if image_models else "gemini-nano-banana-2.1")
    print(f"\n[Step 3/3] Testing image generation using '{test_model}'...")
    print("Prompt: 'A cute miniature cartoon fox sitting on green grass, vibrant Disney Pixar style'")

    try:
        from services.nano_banana_service import generate_nano_banana_image
        from config.preferences import PreferencesManager

        effective_dir = PreferencesManager.get_effective_output_dir()
        effective_dir.mkdir(parents=True, exist_ok=True)
        test_out = str(effective_dir / "test_generation.jpg")

        result = generate_nano_banana_image(
            prompt="A cute miniature cartoon fox sitting on green grass, vibrant Disney Pixar style",
            model=test_model,
            aspect_ratio="1:1",
            image_size="1K",
            output_path=test_out,
        )

        print("\n" + "-" * 60)
        print("Result from Image Generation Service:")
        print(result)
        print("-" * 60)

        out_path = Path(test_out)
        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"\n>>> SUCCESS! Image generated and saved to: {out_path.resolve()}")
            print(f">>> File size: {out_path.stat().st_size / 1024:.1f} KB")
        else:
            if "Error" in result or "429" in result or "Notice" in result:
                print("\n>>> Image generation did not produce a file.")
                print(">>> Review the diagnostic guidance printed above.")

    except Exception as exc:
        print(f"\n[FAILED] Image generation encountered an error:")
        from services.client import format_api_error
        print(format_api_error(exc, context="test image generation"))


if __name__ == "__main__":
    main()
