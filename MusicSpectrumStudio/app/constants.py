"""Constants and default values used across the app."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _user_data_dir() -> Path:
    """Return a per-user writable directory for app data."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    p = Path(base) / "MusicSpectrumStudio"
    p.mkdir(parents=True, exist_ok=True)
    return p


USER_DATA_DIR = _user_data_dir()
CONFIG_PATH = USER_DATA_DIR / "config.json"
API_KEYS_PATH = USER_DATA_DIR / "api_keys.json"
CACHE_DIR = USER_DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_FPS = 30
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080

# Supported render resolutions (width, height, label)
RESOLUTIONS: list[tuple[int, int, str]] = [
    (1280, 720, "HD 720p (1280x720)"),
    (1920, 1080, "Full HD 1080p (1920x1080)"),
    (2560, 1440, "QHD 1440p (2560x1440)"),
    (2048, 1080, "2K DCI (2048x1080)"),
    (1080, 1920, "Vertical 1080x1920 (TikTok/Reels)"),
    (1080, 1350, "Portrait 1080x1350 (IG)"),
    (1080, 1080, "Square 1080x1080"),
]

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".opus", ".wma"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_TRANSCRIBE_MODELS = ["whisper-large-v3-turbo", "whisper-large-v3"]
GROQ_DEFAULT_LLM = "llama-3.3-70b-versatile"
GROQ_FALLBACK_LLM = "llama-3.1-8b-instant"
