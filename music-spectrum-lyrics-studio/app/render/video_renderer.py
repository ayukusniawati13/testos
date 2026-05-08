"""
Main video renderer - composites all visual elements and outputs via FFmpeg.
"""
import os
import subprocess
import logging
import re
import time
import numpy as np
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class VideoRenderer:
    """Render final video with spectrum, lyrics, logo, and CTA."""

    def __init__(self, settings):
        self.width = settings.get("width", 1920)
        self.height = settings.get("height", 1080)
        self.fps = settings.get("fps", 30)
        self.ffmpeg_preset = settings.get("ffmpeg_preset", "medium")
        self.audio_path = None
        self.background_path = None
        self.output_path = None
        self.duration = 0.0
        self.audio_analyzer = None
        self.karaoke_engine = None
        self.spectrum_renderer = None
        self.logo_manager = None
        self.cta_manager = None
        self.position_manager = None
        self._cancel = False

    def set_audio(self, path, analyzer, duration):
        self.audio_path = path
        self.audio_analyzer = analyzer
        self.duration = duration

    def set_background(self, path):
        self.background_path = path

    def set_output(self, path):
        self.output_path = path

    def cancel(self):
        self._cancel = True

    def _prepare_background_frame(self, bg_source, time_sec):
        """Get background frame at given time."""
        if isinstance(bg_source, Image.Image):
            return bg_source.copy()
        elif isinstance(bg_source, list):
            idx = int(time_sec * self.fps) % len(bg_source)
            return bg_source[idx].copy()
        return Image.new("RGB", (self.width, self.height), (20, 20, 30))

    def _load_background(self):
        """Load background as image or video frames source."""
        if not self.background_path or not os.path.exists(self.background_path):
            return Image.new("RGB", (self.width, self.height), (20, 20, 30))

        ext = os.path.splitext(self.background_path)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".webp"]:
            img = Image.open(self.background_path).convert("RGB")
            return img.resize((self.width, self.height), Image.LANCZOS)
        else:
            return "video"

    def render_frame(self, bg_frame, time_sec):
        """Render a single composite frame."""
        frame = bg_frame.resize((self.width, self.height), Image.LANCZOS)

        if self.spectrum_renderer and self.audio_analyzer:
            spectrum_settings = self.spectrum_renderer.settings
            bars = self.audio_analyzer.get_spectrum_at_time(
                time_sec,
                bar_count=spectrum_settings.get("bar_count", 64),
                bass_boost=spectrum_settings.get("bass_boost", 1.2),
                treble_reaction=spectrum_settings.get("treble_reaction", 1.0),
                sensitivity=spectrum_settings.get("sensitivity", 1.0),
            )
            beat_energy = self.audio_analyzer.get_bass_energy(time_sec)
            frame = self.spectrum_renderer.render(frame, bars, beat_energy, time_sec)

        if self.karaoke_engine:
            from app.lyrics.karaoke_effects import KaraokeRenderer
            kr = KaraokeRenderer(self.width, self.height)
            display_data = self.karaoke_engine.get_display_data(time_sec)
            beat_energy = 0.0
            if self.audio_analyzer:
                beat_energy = self.audio_analyzer.get_bass_energy(time_sec)
            frame = kr.render(frame, display_data, beat_energy)

        if self.logo_manager:
            frame = self.logo_manager.render(frame, time_sec, self.duration)

        if self.cta_manager:
            frame = self.cta_manager.render(frame, time_sec, self.duration)

        if frame.mode == "RGBA":
            bg = Image.new("RGB", frame.size, (0, 0, 0))
            bg.paste(frame, mask=frame.split()[3])
            frame = bg

        return frame

    def render_preview(self, start_time=0, preview_duration=10):
        """Render a short preview clip."""
        bg = self._load_background()
        frames = []
        total_frames = int(preview_duration * self.fps)

        for i in range(total_frames):
            if self._cancel:
                break
            t = start_time + i / self.fps
            if t > self.duration:
                break

            if isinstance(bg, str) and bg == "video":
                bg_frame = Image.new("RGB", (self.width, self.height), (20, 20, 30))
            else:
                bg_frame = bg.copy() if isinstance(bg, Image.Image) else bg
            frame = self.render_frame(bg_frame, t)
            frames.append(frame)

        return frames


class RenderThread(QThread):
    """Background thread for video rendering."""
    progress = pyqtSignal(int, str)
    frame_rendered = pyqtSignal(object)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, renderer):
        super().__init__()
        self.renderer = renderer
        self._cancel = False

    def cancel(self):
        self._cancel = True
        self.renderer.cancel()

    def run(self):
        try:
            r = self.renderer
            if not r.audio_path or not r.output_path:
                self.error.emit("Audio or output path not set")
                return

            self.progress.emit(0, "Preparing background...")
            bg = r._load_background()
            is_video_bg = isinstance(bg, str) and bg == "video"

            total_frames = int(r.duration * r.fps)
            if total_frames == 0:
                self.error.emit("Duration is zero")
                return

            self.progress.emit(2, "Starting FFmpeg pipe...")

            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-vcodec", "rawvideo",
                "-s", f"{r.width}x{r.height}",
                "-pix_fmt", "rgb24",
                "-r", str(r.fps),
                "-i", "-",
                "-i", r.audio_path,
                "-c:v", "libx264",
                "-preset", r.ffmpeg_preset,
                "-crf", "18",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-pix_fmt", "yuv420p",
                r.output_path,
            ]

            if is_video_bg:
                ffmpeg_cmd = self._build_video_bg_cmd(r)

            process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            bg_reader_process = None
            bg_frames_iter = None
            if is_video_bg:
                bg_reader_process, bg_frames_iter = self._start_bg_reader(r)

            start_time = time.time()

            for frame_num in range(total_frames):
                if self._cancel:
                    process.stdin.close()
                    process.terminate()
                    self.progress.emit(0, "Cancelled")
                    return

                t = frame_num / r.fps

                if is_video_bg and bg_frames_iter:
                    try:
                        raw = next(bg_frames_iter)
                        bg_frame = Image.frombytes("RGB", (r.width, r.height), raw)
                    except StopIteration:
                        bg_frame = Image.new("RGB", (r.width, r.height), (20, 20, 30))
                else:
                    bg_frame = bg.copy() if isinstance(bg, Image.Image) else Image.new("RGB", (r.width, r.height), (20, 20, 30))

                frame = r.render_frame(bg_frame, t)
                frame_data = np.array(frame)

                try:
                    process.stdin.write(frame_data.tobytes())
                except BrokenPipeError:
                    break

                pct = int((frame_num + 1) / total_frames * 100)
                elapsed = time.time() - start_time
                if frame_num > 0:
                    eta = elapsed / frame_num * (total_frames - frame_num)
                    eta_str = f"ETA: {int(eta)}s"
                else:
                    eta_str = "Calculating..."

                if frame_num % (r.fps) == 0:
                    self.progress.emit(pct, f"Rendering {pct}% - {eta_str}")

            process.stdin.close()
            process.wait()

            if bg_reader_process:
                bg_reader_process.terminate()

            if process.returncode != 0:
                stderr = process.stderr.read().decode()
                self.error.emit(f"FFmpeg error: {stderr[-500:]}")
                return

            self.progress.emit(100, "Render complete!")
            self.finished.emit(r.output_path)

        except Exception as e:
            logger.error(f"Render error: {e}")
            self.error.emit(str(e))

    def _build_video_bg_cmd(self, r):
        """Build FFmpeg command for video background."""
        return [
            "ffmpeg", "-y",
            "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{r.width}x{r.height}",
            "-pix_fmt", "rgb24", "-r", str(r.fps),
            "-i", "-",
            "-i", r.audio_path,
            "-c:v", "libx264", "-preset", r.ffmpeg_preset,
            "-crf", "18", "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-pix_fmt", "yuv420p",
            r.output_path,
        ]

    def _start_bg_reader(self, r):
        """Start reading video background frames via FFmpeg."""
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", r.background_path,
            "-vf", f"scale={r.width}:{r.height}",
            "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-r", str(r.fps),
            "-v", "quiet",
            "-",
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        frame_size = r.width * r.height * 3

        def frame_gen():
            while True:
                data = proc.stdout.read(frame_size)
                if len(data) < frame_size:
                    break
                yield data

        return proc, frame_gen()
