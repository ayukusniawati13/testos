"""Filesystem helpers used across the application."""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

AUDIO_EXTS: tuple[str, ...] = (".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac")
IMAGE_EXTS: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
VIDEO_EXTS: tuple[str, ...] = (".mp4", ".mov", ".webm", ".mkv", ".avi", ".gif")


def project_root() -> Path:
    """Return the on-disk project root.

    When running from source the project root is two parents above this file
    (``app/utils/file_utils.py``). When frozen by PyInstaller, the executable
    lives in the bundle root.
    """
    if getattr(sys, "frozen", False):  # PyInstaller bundle
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def ensure_dir(path: Path | str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_filename(name: str, replacement: str = "_") -> str:
    """Sanitize a string so it is safe to use as a file name on every OS."""
    cleaned = re.sub(r'[\\/:*?"<>|\r\n\t]+', replacement, name).strip()
    cleaned = cleaned.rstrip(". ")
    return cleaned or "untitled"


def list_files(folder: Path | str, exts: Sequence[str], recursive: bool = False) -> List[Path]:
    folder = Path(folder)
    if not folder.is_dir():
        return []
    iterator: Iterable[Path] = folder.rglob("*") if recursive else folder.iterdir()
    out: List[Path] = []
    lowered = {e.lower() for e in exts}
    for entry in iterator:
        if entry.is_file() and entry.suffix.lower() in lowered:
            out.append(entry)
    out.sort()
    return out


def list_audio_files(folder: Path | str, recursive: bool = False) -> List[Path]:
    return list_files(folder, AUDIO_EXTS, recursive=recursive)


def list_background_files(folder: Path | str, recursive: bool = False) -> List[Path]:
    return list_files(folder, IMAGE_EXTS + VIDEO_EXTS, recursive=recursive)


def unique_path(target: Path) -> Path:
    """Return ``target`` if it doesn't exist, otherwise append ``_1``, ``_2``..."""
    if not target.exists():
        return target
    stem, suffix = target.stem, target.suffix
    parent = target.parent
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def human_size(num_bytes: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    size = float(num_bytes)
    for unit in units:
        if size < 1024.0:
            return f"{size:0.1f} {unit}"
        size /= 1024.0
    return f"{size:0.1f} PB"


def copy_file(src: Path | str, dst: Path | str, overwrite: bool = False) -> Path:
    src_p, dst_p = Path(src), Path(dst)
    if dst_p.exists() and not overwrite:
        dst_p = unique_path(dst_p)
    ensure_dir(dst_p.parent)
    shutil.copy2(src_p, dst_p)
    return dst_p
