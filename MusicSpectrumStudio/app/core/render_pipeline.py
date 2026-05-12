"""Render pipeline: audio + lyrics + visual config -> mp4 file via ffmpeg pipe."""

from __future__ import annotations

import logging
import os
import subprocess
import threading
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from ..config import AppConfig
from ..core.audio_spectrum import analyze_audio, load_audio
from ..core.ffmpeg_check import resolve_ffmpeg_path
from ..core.transcribe import TranscriptionResult
from ..render.compositor import FrameCompositor
from ..render.lyrics_styles import LyricRenderState

logger = logging.getLogger(__name__)


@dataclass
class RenderProgress:
    frame: int
    total: int

    @property
    def fraction(self) -> float:
        return min(1.0, self.frame / max(1, self.total))


def render_to_file(
    cfg: AppConfig,
    *,
    audio_path: str,
    output_path: str,
    transcription: TranscriptionResult | None,
    progress: Callable[[RenderProgress], None] | None = None,
    cancel: threading.Event | None = None,
) -> None:
    ffmpeg = resolve_ffmpeg_path()
    width, height = cfg.render.width, cfg.render.height
    fps = cfg.render.fps

    logger.info("Memuat audio %s ...", audio_path)
    audio = load_audio(audio_path)
    spectrum = analyze_audio(
        audio,
        fps=fps,
        num_bands=cfg.spectrum.bar_count,
        smoothing=cfg.spectrum.smoothing,
    )
    total_frames = len(spectrum.bands)
    if total_frames <= 0:
        raise RuntimeError("Audio terlalu pendek atau gagal dianalisis.")

    lyrics_state = None
    if transcription and transcription.lines:
        lyrics_state = LyricRenderState(transcription=transcription, width=width, height=height)

    compositor = FrameCompositor(cfg, spectrum, lyrics_state, width, height)
    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        cmd = [
            ffmpeg, "-y",
            "-f", "rawvideo", "-pix_fmt", "bgr24",
            "-s", f"{width}x{height}", "-r", str(fps),
            "-i", "pipe:0",
            "-i", audio_path,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", cfg.render.preset, "-crf", str(cfg.render.crf),
            "-c:a", "aac", "-b:a", cfg.render.audio_bitrate,
            "-movflags", "+faststart",
            "-shortest",
            output_path,
        ]
        logger.info("Menjalankan ffmpeg: %s", " ".join(cmd))
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        assert proc.stdin is not None
        try:
            for i in range(total_frames):
                if cancel and cancel.is_set():
                    logger.info("Render dibatalkan oleh user.")
                    break
                frame = compositor.frame(i)
                proc.stdin.write(frame.tobytes())
                if progress and (i % 5 == 0 or i == total_frames - 1):
                    try:
                        progress(RenderProgress(frame=i + 1, total=total_frames))
                    except Exception:
                        pass
            proc.stdin.close()
            err = proc.stderr.read().decode(errors="ignore") if proc.stderr else ""
            proc.wait(timeout=None)
            if proc.returncode != 0:
                raise RuntimeError(f"ffmpeg keluar dengan kode {proc.returncode}: {err[-500:]}")
        finally:
            try:
                proc.stdin.close()
            except Exception:
                pass
            proc.kill() if proc.poll() is None else None
    finally:
        compositor.close()


def render_preview_frame(
    cfg: AppConfig,
    audio_path: str | None,
    transcription: TranscriptionResult | None,
    *,
    width: int = 960,
    height: int = 540,
    at_seconds: float = 1.0,
) -> np.ndarray:
    """Render a single preview frame (BGR uint8) without writing to disk."""
    preview_cfg = AppConfig.from_dict(cfg.to_dict())
    preview_cfg.render.width = width
    preview_cfg.render.height = height
    fps = preview_cfg.render.fps

    # Lightweight spectrum: synthesise pseudo bands if no audio
    if audio_path and os.path.exists(audio_path):
        try:
            audio = load_audio(audio_path)
            stream = analyze_audio(
                audio,
                fps=fps,
                num_bands=preview_cfg.spectrum.bar_count,
                smoothing=preview_cfg.spectrum.smoothing,
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("Preview audio gagal dianalisis: %s", exc)
            stream = _synthetic_stream(fps, preview_cfg.spectrum.bar_count, max(at_seconds * 2.0, 6.0))
    else:
        stream = _synthetic_stream(fps, preview_cfg.spectrum.bar_count, max(at_seconds * 2.0, 6.0))

    lyrics_state = None
    if transcription and transcription.lines:
        lyrics_state = LyricRenderState(transcription=transcription, width=width, height=height)

    compositor = FrameCompositor(preview_cfg, stream, lyrics_state, width, height)
    try:
        frame_idx = int(at_seconds * fps)
        frame_idx = max(0, min(frame_idx, len(stream.bands) - 1))
        return compositor.frame(frame_idx)
    finally:
        compositor.close()


def _synthetic_stream(fps: int, num_bands: int, duration: float):
    from ..core.audio_spectrum import SpectrumStream

    frames = max(2, int(duration * fps))
    t = np.linspace(0, duration, frames)
    rng = np.random.default_rng(42)
    base = 0.35 + 0.25 * np.sin(2 * np.pi * t / 4.0)
    bands = np.zeros((frames, num_bands), dtype=np.float32)
    for b in range(num_bands):
        bands[:, b] = np.clip(
            base + 0.4 * np.sin(2 * np.pi * (t + b * 0.07)) + 0.2 * rng.standard_normal(frames),
            0.0,
            1.0,
        )
    loud = bands.mean(axis=1)
    beat = (np.arange(frames) % max(1, fps // 2) == 0).astype(np.float32)
    return SpectrumStream(bands=bands, loudness=loud.astype(np.float32), beat=beat, fps=fps, num_bands=num_bands)
