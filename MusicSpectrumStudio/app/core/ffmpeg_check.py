"""FFmpeg availability + online install helper.

Strategy:
- If a system ffmpeg is on PATH, use it.
- Otherwise try the bundled binary from `imageio-ffmpeg` (auto-downloaded).
- Provide an `install_online` method that downloads via `imageio-ffmpeg` explicitly
  and emits progress via callbacks.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FFmpegStatus:
    available: bool
    path: str | None
    version: str | None
    source: str  # "system", "bundled", "missing"


def _probe(path: str) -> str | None:
    try:
        out = subprocess.run(
            [path, "-version"], capture_output=True, text=True, timeout=5, check=False
        )
        if out.returncode != 0:
            return None
        first_line = (out.stdout or out.stderr).splitlines()[0] if (out.stdout or out.stderr) else ""
        return first_line.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def check_ffmpeg() -> FFmpegStatus:
    """Return current ffmpeg status without triggering a download."""
    system_path = shutil.which("ffmpeg")
    if system_path:
        version = _probe(system_path)
        if version:
            return FFmpegStatus(True, system_path, version, "system")

    bundled = _bundled_ffmpeg_if_present()
    if bundled:
        version = _probe(bundled)
        if version:
            return FFmpegStatus(True, bundled, version, "bundled")

    return FFmpegStatus(False, None, None, "missing")


def _bundled_ffmpeg_if_present() -> str | None:
    """Return the bundled ffmpeg path *only* if it has already been downloaded."""
    try:
        import imageio_ffmpeg
    except ImportError:
        return None
    try:
        # imageio_ffmpeg downloads on demand; we want to avoid that here.
        # Inspect cached path directly.
        from imageio_ffmpeg._utils import get_ffmpeg_exe_for_platform  # type: ignore

        candidate = get_ffmpeg_exe_for_platform()
        if candidate and os.path.isfile(candidate):
            return candidate
    except Exception:  # pragma: no cover - private API; fall back
        pass
    # Last resort: check by calling get_ffmpeg_version (does NOT download)
    try:
        ver = imageio_ffmpeg.get_ffmpeg_version()
        if ver:
            return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None
    return None


def install_ffmpeg_online(progress: Callable[[str], None] | None = None) -> FFmpegStatus:
    """Download ffmpeg via imageio-ffmpeg."""

    def emit(msg: str) -> None:
        if progress:
            try:
                progress(msg)
            except Exception:  # pragma: no cover
                pass
        logger.info("ffmpeg installer: %s", msg)

    try:
        import imageio_ffmpeg
    except ImportError as exc:
        emit(f"imageio-ffmpeg is not installed: {exc}")
        return FFmpegStatus(False, None, None, "missing")
    try:
        emit("Mengecek paket ffmpeg dari imageio-ffmpeg...")
        path = imageio_ffmpeg.get_ffmpeg_exe()
        emit(f"FFmpeg tersedia di: {path}")
        version = _probe(path) or "unknown"
        return FFmpegStatus(True, path, version, "bundled")
    except Exception as exc:  # pragma: no cover - network/io failure
        emit(f"Gagal mengunduh ffmpeg: {exc}")
        return FFmpegStatus(False, None, None, "missing")


def resolve_ffmpeg_path() -> str:
    """Return a usable ffmpeg path or raise."""
    status = check_ffmpeg()
    if status.available and status.path:
        return status.path
    status = install_ffmpeg_online()
    if status.available and status.path:
        return status.path
    raise RuntimeError("FFmpeg tidak tersedia. Jalankan setup atau klik tombol install FFmpeg di UI.")
