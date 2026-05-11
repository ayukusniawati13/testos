"""Video renderer combining background, spectrum, lyrics, and logo into final MP4."""

import os
import subprocess
import tempfile
import shutil
import logging
from pathlib import Path

import numpy as np
from PIL import Image

from app.core.audio_analyzer import AudioAnalyzer
from app.core.lrc_parser import LRCParser, LyricLine
from app.core.spectrum_engine import SpectrumEngine, SpectrumConfig
from app.core.lyric_renderer import LyricRenderer, LyricConfig
from app.core.ffmpeg_manager import FFmpegManager

logger = logging.getLogger(__name__)


class VideoConfig:
    def __init__(self):
        self.width: int = 1920
        self.height: int = 1080
        self.fps: int = 30
        self.bitrate: str = "8M"
        self.output_format: str = "mp4"


class LogoConfig:
    def __init__(self):
        self.enabled: bool = False
        self.path: str = ""
        self.position: str = "top-right"
        self.size: int = 100
        self.opacity: float = 0.8
        self.margin: int = 20


class RenderJob:
    def __init__(self):
        self.music_path: str = ""
        self.lrc_path: str = ""
        self.background_path: str = ""
        self.output_path: str = ""
        self.video_config = VideoConfig()
        self.spectrum_config = SpectrumConfig()
        self.lyric_config = LyricConfig()
        self.logo_config = LogoConfig()


class VideoRenderer:
    def __init__(self, ffmpeg: FFmpegManager | None = None):
        self.ffmpeg = ffmpeg or FFmpegManager()
        self._cancelled = False
        self._process: subprocess.Popen | None = None

    def cancel(self) -> None:
        self._cancelled = True
        if self._process:
            try:
                self._process.terminate()
            except Exception:
                pass

    def render(self, job: RenderJob,
               progress_callback=None,
               log_callback=None) -> bool:
        self._cancelled = False

        if not os.path.isfile(job.music_path):
            raise FileNotFoundError(f"Music file not found: {job.music_path}")

        if log_callback:
            log_callback(f"Loading audio: {job.music_path}")

        analyzer = AudioAnalyzer(job.music_path)
        analyzer.load()
        analyzer.analyze()
        duration = analyzer.duration

        if log_callback:
            log_callback(f"Audio duration: {duration:.1f}s")

        lyrics: list[LyricLine] = []
        if job.lrc_path and os.path.isfile(job.lrc_path):
            lyrics = LRCParser.parse(job.lrc_path)
            if log_callback:
                log_callback(f"Loaded {len(lyrics)} lyric lines")

        spectrum = SpectrumEngine(job.spectrum_config)
        lyric_renderer = LyricRenderer(job.lyric_config)

        bg_image = self._load_background(job.background_path,
                                         job.video_config.width,
                                         job.video_config.height)
        logo_image = self._load_logo(job.logo_config,
                                     job.video_config.width,
                                     job.video_config.height)

        bg_is_video = job.background_path.lower().endswith(
            (".mp4", ".mov", ".mkv", ".avi", ".webm"))

        w = job.video_config.width
        h = job.video_config.height
        fps = job.video_config.fps
        total_frames = int(duration * fps)

        os.makedirs(os.path.dirname(job.output_path) or ".", exist_ok=True)

        temp_dir = tempfile.mkdtemp(prefix="mslv_")
        frames_pattern = os.path.join(temp_dir, "frame_%07d.png")

        try:
            if log_callback:
                log_callback("Rendering frames...")

            for frame_idx in range(total_frames):
                if self._cancelled:
                    if log_callback:
                        log_callback("Render cancelled.")
                    return False

                t = frame_idx / fps

                if bg_is_video:
                    frame = bg_image.copy()
                else:
                    frame = bg_image.copy()

                bands = analyzer.get_spectrum_at_time(t, n_bands=64)
                beat = analyzer.get_beat_strength_at_time(t)

                spec_layer = spectrum.render(w, h, bands, beat)
                frame = Image.alpha_composite(frame, spec_layer)

                if lyrics:
                    lyric_layer = lyric_renderer.render(w, h, lyrics, t)
                    frame = Image.alpha_composite(frame, lyric_layer)

                if logo_image:
                    frame = Image.alpha_composite(frame, logo_image)

                frame_path = frames_pattern % frame_idx
                frame.convert("RGB").save(frame_path, "PNG")

                if progress_callback and frame_idx % max(1, fps) == 0:
                    pct = int((frame_idx / total_frames) * 90)
                    progress_callback(pct)

            if self._cancelled:
                return False

            if log_callback:
                log_callback("Encoding video with FFmpeg...")

            if progress_callback:
                progress_callback(90)

            cmd = [
                self.ffmpeg.ffmpeg_path,
                "-y",
                "-framerate", str(fps),
                "-i", frames_pattern,
                "-i", job.music_path,
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "18",
                "-b:v", job.video_config.bitrate,
                "-c:a", "aac",
                "-b:a", "192k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                job.output_path,
            ]

            if log_callback:
                log_callback(f"FFmpeg command: {' '.join(cmd)}")

            self._process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            _, stderr = self._process.communicate()

            if self._process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace")
                if log_callback:
                    log_callback(f"FFmpeg error: {error_msg}")
                raise RuntimeError(f"FFmpeg encoding failed: {error_msg}")

            if progress_callback:
                progress_callback(100)

            if log_callback:
                log_callback(f"Video saved: {job.output_path}")

            return True

        finally:
            self._process = None
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _load_background(self, path: str, width: int, height: int) -> Image.Image:
        if not path or not os.path.isfile(path):
            bg = Image.new("RGBA", (width, height), (15, 15, 25, 255))
            return bg

        ext = path.lower().rsplit(".", 1)[-1]
        if ext in ("jpg", "jpeg", "png", "webp", "bmp"):
            img = Image.open(path).convert("RGBA")
            img = img.resize((width, height), Image.LANCZOS)
            return img
        else:
            bg = Image.new("RGBA", (width, height), (15, 15, 25, 255))
            return bg

    def _load_logo(self, config: LogoConfig, width: int, height: int
                   ) -> Image.Image | None:
        if not config.enabled or not config.path or not os.path.isfile(config.path):
            return None

        try:
            logo = Image.open(config.path).convert("RGBA")
            aspect = logo.width / logo.height
            new_w = config.size
            new_h = int(new_w / aspect)
            logo = logo.resize((new_w, new_h), Image.LANCZOS)

            if config.opacity < 1.0:
                alpha = logo.split()[3]
                alpha = alpha.point(lambda p: int(p * config.opacity))
                logo.putalpha(alpha)

            canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            pos = config.position
            m = config.margin

            if pos == "top-left":
                x, y = m, m
            elif pos == "top-right":
                x, y = width - new_w - m, m
            elif pos == "bottom-left":
                x, y = m, height - new_h - m
            elif pos == "bottom-right":
                x, y = width - new_w - m, height - new_h - m
            elif pos == "center":
                x, y = (width - new_w) // 2, (height - new_h) // 2
            else:
                x, y = width - new_w - m, m

            canvas.paste(logo, (x, y))
            return canvas

        except Exception as e:
            logger.warning(f"Failed to load logo: {e}")
            return None
