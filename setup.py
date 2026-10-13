import sys
from pathlib import Path
from setuptools import setup, find_packages

this_directory = Path(__file__).parent
readme_path = this_directory / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="gemini-media-mcp",
    version="2.2.0",
    description="MCP server for Google Veo 3.1 video and Gemini Nano Banana image generation.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    py_modules=["gemini_mcp"],
    python_requires=">=3.10",
    install_requires=[
        "mcp>=2.3.0",
        "python-dotenv>=1.2.0",
        "google-genai>=2.30.0",
        "pillow>=12.0.0",
        "pyinstaller>=6.11.0",
    ],
    entry_points={
        "console_scripts": [
            "gemini-media-mcp = gemini_mcp:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Multimedia :: Video",
    ],
)
