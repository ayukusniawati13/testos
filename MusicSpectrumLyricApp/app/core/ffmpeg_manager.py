"""FFmpeg detection, download, and management."""

import os
import platform
import shutil
import subprocess
import sys
import zipfile
import tarfile
import urllib.request
from pathlib import Path


class FFmpegManager:
    TOOLS_DIR = Path(__file__).resolve().parent.parent.parent / "tools" / "ffmpeg"
    DOWNLOAD_URLS = {
        "Windows": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
        "Linux": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz",
        "Darwin": "https://evermeet.cx/ffmpeg/getrelease/zip",
    }

    def __init__(self) -> None:
        self._ffmpeg_path: str | None = None
        self._ffprobe_path: str | None = None
        self._detect()

    def _detect(self) -> None:
        local = self._find_local()
        if local:
            self._ffmpeg_path = local
            probe = local.replace("ffmpeg", "ffprobe")
            if os.path.isfile(probe):
                self._ffprobe_path = probe
            return
        system = shutil.which("ffmpeg")
        if system:
            self._ffmpeg_path = system
            probe = shutil.which("ffprobe")
            if probe:
                self._ffprobe_path = probe

    def _find_local(self) -> str | None:
        if not self.TOOLS_DIR.exists():
            return None
        ext = ".exe" if platform.system() == "Windows" else ""
        for root, _dirs, files in os.walk(self.TOOLS_DIR):
            if f"ffmpeg{ext}" in files:
                return os.path.join(root, f"ffmpeg{ext}")
        return None

    @property
    def is_available(self) -> bool:
        return self._ffmpeg_path is not None

    @property
    def ffmpeg_path(self) -> str:
        if self._ffmpeg_path:
            return self._ffmpeg_path
        return "ffmpeg"

    @property
    def ffprobe_path(self) -> str:
        if self._ffprobe_path:
            return self._ffprobe_path
        return "ffprobe"

    @property
    def version(self) -> str:
        if not self.is_available:
            return "Not installed"
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-version"],
                capture_output=True, text=True, timeout=10
            )
            first_line = result.stdout.split("\n")[0]
            return first_line
        except Exception:
            return "Unknown"

    def download_and_install(self, progress_callback=None) -> bool:
        system = platform.system()
        url = self.DOWNLOAD_URLS.get(system)
        if not url:
            raise RuntimeError(f"Unsupported platform: {system}")

        self.TOOLS_DIR.mkdir(parents=True, exist_ok=True)
        ext = ".zip" if system in ("Windows", "Darwin") else ".tar.xz"
        archive_path = self.TOOLS_DIR / f"ffmpeg_download{ext}"

        try:
            if progress_callback:
                progress_callback("Downloading FFmpeg...")

            def _report(block_num, block_size, total_size):
                if progress_callback and total_size > 0:
                    pct = min(100, int(block_num * block_size / total_size * 100))
                    progress_callback(f"Downloading FFmpeg... {pct}%")

            urllib.request.urlretrieve(url, str(archive_path), reporthook=_report)

            if progress_callback:
                progress_callback("Extracting FFmpeg...")

            if ext == ".zip":
                with zipfile.ZipFile(archive_path, "r") as zf:
                    zf.extractall(self.TOOLS_DIR)
            else:
                with tarfile.open(archive_path, "r:xz") as tf:
                    tf.extractall(self.TOOLS_DIR)

            archive_path.unlink(missing_ok=True)

            if system != "Windows":
                ffmpeg_bin = self._find_local()
                if ffmpeg_bin:
                    os.chmod(ffmpeg_bin, 0o755)
                    probe = ffmpeg_bin.replace("ffmpeg", "ffprobe")
                    if os.path.isfile(probe):
                        os.chmod(probe, 0o755)

            self._detect()

            if progress_callback:
                progress_callback("FFmpeg installed successfully!")

            return self.is_available

        except Exception as e:
            archive_path.unlink(missing_ok=True)
            if progress_callback:
                progress_callback(f"Error: {e}")
            raise

    def get_audio_duration(self, filepath: str) -> float:
        try:
            result = subprocess.run(
                [self.ffprobe_path, "-v", "quiet", "-show_entries",
                 "format=duration", "-of", "csv=p=0", filepath],
                capture_output=True, text=True, timeout=30
            )
            return float(result.stdout.strip())
        except Exception:
            return 0.0

    def get_video_duration(self, filepath: str) -> float:
        return self.get_audio_duration(filepath)
