"""Path-related helpers."""

from __future__ import annotations

import os
from pathlib import Path

from ..constants import AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS


def is_audio(path: str | os.PathLike) -> bool:
    return Path(path).suffix.lower() in AUDIO_EXTENSIONS


def is_image(path: str | os.PathLike) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


def is_video(path: str | os.PathLike) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTENSIONS


def list_audio_files(folder: str) -> list[str]:
    p = Path(folder)
    if not p.is_dir():
        return []
    return sorted(str(x) for x in p.iterdir() if x.is_file() and is_audio(x))


def list_visual_files(folder: str) -> list[str]:
    p = Path(folder)
    if not p.is_dir():
        return []
    return sorted(str(x) for x in p.iterdir() if x.is_file() and (is_image(x) or is_video(x)))


def safe_stem(path: str) -> str:
    return Path(path).stem
