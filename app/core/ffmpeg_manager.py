"""FFmpeg detection + opt-in auto-installer.

The manager looks for FFmpeg in three places, in order:
1. The path stored in :class:`AppConfig` (``ffmpeg_path``).
2. ``app/assets/ffmpeg/bin/ffmpeg[.exe]`` -- the local download target.
3. The system ``PATH``.

When the binary is missing, :meth:`auto_install` downloads a static build for
the current OS/architecture from a well-known mirror, extracts it under
``app/assets/ffmpeg/`` and updates the config. The download URL is controlled
by :data:`FFMPEG_BUILDS` and can be overridden by callers.
"""
from __future__ import annotations

import os
import platform
import shutil
import stat
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Tuple

from app.utils import file_utils
from app.utils.config import AppConfig
from app.utils.logger import get_logger

logger = get_logger("ffmpeg_manager")

ProgressCallback = Callable[[float, str], None]


# Static FFmpeg builds. These URLs are public, official binaries.
FFMPEG_BUILDS: dict[str, str] = {
    # Windows: gyan.dev essentials build (zip)
    "windows-x86_64": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    # macOS: evermeet.cx (zip with single ffmpeg binary)
    "darwin-x86_64": "https://evermeet.cx/ffmpeg/getrelease/zip",
    "darwin-arm64": "https://evermeet.cx/ffmpeg/getrelease/zip",
    # Linux: johnvansickle.com static build (tar.xz)
    "linux-x86_64": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
    "linux-aarch64": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz",
}


@dataclass
class FFmpegStatus:
    installed: bool
    path: Optional[Path]
    version: Optional[str] = None
    source: str = "missing"  # config / bundled / path / missing


class FFmpegManager:
    """Detect, locate, and auto-install FFmpeg."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._cached: Optional[FFmpegStatus] = None

    # ------------------------------------------------------------------ paths

    @staticmethod
    def bundled_dir() -> Path:
        return file_utils.project_root() / "app" / "assets" / "ffmpeg"

    @classmethod
    def bundled_binary(cls) -> Path:
        suffix = ".exe" if platform.system().lower() == "windows" else ""
        return cls.bundled_dir() / "bin" / f"ffmpeg{suffix}"

    # ------------------------------------------------------------------ detect

    def status(self, refresh: bool = False) -> FFmpegStatus:
        if self._cached is not None and not refresh:
            return self._cached

        path, source = self._locate()
        if path is None:
            self._cached = FFmpegStatus(installed=False, path=None, source="missing")
            return self._cached

        version = _query_version(path)
        self._cached = FFmpegStatus(
            installed=True, path=path, version=version, source=source
        )
        return self._cached

    def get_path(self) -> Optional[Path]:
        return self.status().path

    def _locate(self) -> Tuple[Optional[Path], str]:
        # 1. Explicit config path
        configured = (self.config.get("ffmpeg_path") or "").strip()
        if configured:
            p = Path(configured)
            if p.is_file() and os.access(p, os.X_OK):
                return p, "config"

        # 2. Bundled binary
        bundled = self.bundled_binary()
        if bundled.is_file() and os.access(bundled, os.X_OK):
            return bundled, "bundled"

        # 3. PATH lookup
        path_str = shutil.which("ffmpeg")
        if path_str:
            return Path(path_str), "path"

        return None, "missing"

    # ------------------------------------------------------------------ install

    def auto_install(self, progress: Optional[ProgressCallback] = None) -> FFmpegStatus:
        """Download & install a static FFmpeg build for the current platform."""
        platform_key = _detect_platform_key()
        if platform_key not in FFMPEG_BUILDS:
            raise RuntimeError(
                f"Automatic FFmpeg install is not supported on '{platform_key}'. "
                "Please install FFmpeg manually and configure its path."
            )

        url = FFMPEG_BUILDS[platform_key]
        target_dir = self.bundled_dir()
        file_utils.ensure_dir(target_dir / "bin")

        with tempfile.TemporaryDirectory() as tmp:
            archive_name = url.rsplit("/", 1)[-1] or "ffmpeg.archive"
            if "." not in archive_name:
                archive_name += ".zip" if "zip" in url else ".tar.xz"
            archive_path = Path(tmp) / archive_name

            logger.info("Downloading FFmpeg from %s", url)
            _download(url, archive_path, progress)

            logger.info("Extracting FFmpeg archive")
            extracted = _extract_archive(archive_path, Path(tmp))

            ffmpeg_bin = _find_ffmpeg_in(extracted)
            if ffmpeg_bin is None:
                raise RuntimeError(
                    "Could not find an 'ffmpeg' binary inside the downloaded archive."
                )

            destination = self.bundled_binary()
            file_utils.ensure_dir(destination.parent)
            shutil.copy2(ffmpeg_bin, destination)

            ffprobe_bin = _find_named_in(extracted, "ffprobe")
            if ffprobe_bin is not None:
                shutil.copy2(ffprobe_bin, destination.parent / ffprobe_bin.name)

            if platform.system().lower() != "windows":
                _make_executable(destination)
                if ffprobe_bin is not None:
                    _make_executable(destination.parent / ffprobe_bin.name)

        self.config.set("ffmpeg_path", str(destination))
        try:
            self.config.save()
        except OSError:
            logger.warning("Could not persist ffmpeg path to config.")
        return self.status(refresh=True)


# --------------------------------------------------------------------------- helpers


def _detect_platform_key() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    if machine in ("amd64", "x86_64"):
        machine = "x86_64"
    elif machine in ("arm64", "aarch64"):
        machine = "arm64" if system == "darwin" else "aarch64"
    return f"{system}-{machine}"


def _download(url: str, dest: Path, progress: Optional[ProgressCallback]) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "SLVM/1.0"})
    with urllib.request.urlopen(request) as response:  # noqa: S310 - public binaries
        total = int(response.headers.get("Content-Length") or 0)
        downloaded = 0
        with dest.open("wb") as fh:
            while True:
                chunk = response.read(64 * 1024)
                if not chunk:
                    break
                fh.write(chunk)
                downloaded += len(chunk)
                if progress and total > 0:
                    progress(downloaded / total, f"Downloading FFmpeg ({downloaded // 1024} KB)")


def _extract_archive(archive: Path, target: Path) -> Path:
    if archive.suffix.lower() == ".zip" or archive.name.lower().endswith(".zip"):
        with zipfile.ZipFile(archive, "r") as zf:
            zf.extractall(target)
    else:
        with tarfile.open(archive, "r:*") as tf:
            tf.extractall(target)
    return target


def _find_ffmpeg_in(root: Path) -> Optional[Path]:
    return _find_named_in(root, "ffmpeg")


def _find_named_in(root: Path, name: str) -> Optional[Path]:
    candidates = [name, f"{name}.exe"]
    for path in root.rglob("*"):
        if path.is_file() and path.name.lower() in candidates:
            return path
    return None


def _make_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _query_version(path: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            [str(path), "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        first_line = (result.stdout or result.stderr or "").splitlines()[:1]
        if first_line:
            return first_line[0].strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def manual_install_instructions() -> str:
    return (
        "FFmpeg auto-install failed. You can still install it manually:\n"
        "  • Windows: https://www.gyan.dev/ffmpeg/builds/  (extract and add bin/ to PATH)\n"
        "  • macOS:   brew install ffmpeg\n"
        "  • Linux:   sudo apt install ffmpeg  (Debian/Ubuntu) or your distro's equivalent\n"
        "Then point the application to the binary in Settings → FFmpeg path."
    )
