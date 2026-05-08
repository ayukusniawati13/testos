"""Final video rendering: composes background + spectrum + lyrics + overlays
and pipes the result into FFmpeg.

The pipeline is deliberately simple:

    [pre-analyzed audio] -> per-frame composition (Pillow) -> raw RGB pipe
                                                              |
                                                              v
                                              FFmpeg (-i pipe + -i audio) -> mp4

* The background is resampled once per render and re-used (image / colour /
  gradient). For video backgrounds we open the video lazily and read the
  closest frame to the timestamp.
* Spectrum frames come from :class:`SpectrumEngine`.
* Lyrics overlay comes from :class:`LyricEngine`.
* Logo + animation overlay are simple alpha composites.

The class :class:`RenderEngine` is GUI-free. The Qt worker
:class:`RenderWorker` lives in this module too so the GUI can simply do
``worker = RenderWorker(job); worker.start()``.
"""
from __future__ import annotations

import math
import shlex
import subprocess
import tempfile
import threading
import time as time_module
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from PIL import Image, ImageColor, ImageDraw, ImageFilter

from app.core.audio_analyzer import AudioAnalyzer, SpectrumFrames
from app.core.ffmpeg_manager import FFmpegManager
from app.core.lyric_engine import LyricEngine, LyricStyle, LyricTrack
from app.core.spectrum_engine import SpectrumConfig, SpectrumEngine
from app.utils import file_utils, validators
from app.utils.logger import get_logger

logger = get_logger("render_engine")

ProgressCallback = Callable[[float, str], None]
LogCallback = Callable[[str], None]


# --------------------------------------------------------------- data classes


@dataclass
class BackgroundSpec:
    type: str = "solid"  # solid / gradient / image / video
    color: str = "#0f1116"
    gradient: List[str] = field(default_factory=lambda: ["#0f1116", "#1f2233"])
    path: Optional[str] = None
    fit_mode: str = "cover"  # cover / contain / stretch / blur

    @classmethod
    def from_dict(cls, data: dict) -> "BackgroundSpec":
        return cls(
            type=str(data.get("type", "solid")),
            color=str(data.get("color", "#0f1116")),
            gradient=list(data.get("gradient") or ["#0f1116", "#1f2233"]),
            path=str(data.get("path")) if data.get("path") else None,
            fit_mode=str(data.get("fit_mode", "cover")),
        )


@dataclass
class LogoSpec:
    enabled: bool = False
    path: Optional[str] = None
    position: str = "bottom_right"
    x: float = 0.95
    y: float = 0.95
    size: float = 0.12
    opacity: float = 0.85
    margin: int = 24
    fade_in: float = 0.5
    fade_out: float = 0.5

    @classmethod
    def from_dict(cls, data: dict) -> "LogoSpec":
        return cls(
            enabled=bool(data.get("enabled", False)),
            path=str(data.get("path")) if data.get("path") else None,
            position=str(data.get("position", "bottom_right")),
            x=float(data.get("x", 0.95)),
            y=float(data.get("y", 0.95)),
            size=float(data.get("size", 0.12)),
            opacity=float(data.get("opacity", 0.85)),
            margin=int(data.get("margin", 24)),
            fade_in=float(data.get("fade_in", 0.5)),
            fade_out=float(data.get("fade_out", 0.5)),
        )


@dataclass
class AnimationOverlaySpec:
    enabled: bool = False
    path: Optional[str] = None
    placement: str = "start"  # start / middle / end / custom
    start_at: float = 0.0
    duration: float = 3.0
    opacity: float = 1.0
    blend: str = "normal"

    @classmethod
    def from_dict(cls, data: dict) -> "AnimationOverlaySpec":
        return cls(
            enabled=bool(data.get("enabled", False)),
            path=str(data.get("path")) if data.get("path") else None,
            placement=str(data.get("placement", "start")),
            start_at=float(data.get("start_at", 0.0)),
            duration=float(data.get("duration", 3.0)),
            opacity=float(data.get("opacity", 1.0)),
            blend=str(data.get("blend", "normal")),
        )


@dataclass
class RenderSettings:
    resolution: Tuple[int, int] = (1920, 1080)
    fps: int = 30
    codec: str = "h264"  # h264 / h265
    preset: str = "medium"
    crf: int = 20
    video_bitrate: str = ""
    audio_bitrate: str = "192k"

    @classmethod
    def from_dict(cls, data: dict) -> "RenderSettings":
        res = data.get("resolution") or [1920, 1080]
        return cls(
            resolution=(int(res[0]), int(res[1])),
            fps=int(data.get("fps", 30)),
            codec=str(data.get("codec", "h264")),
            preset=str(data.get("preset", "medium")),
            crf=int(data.get("crf", 20)),
            video_bitrate=str(data.get("video_bitrate", "")),
            audio_bitrate=str(data.get("audio_bitrate", "192k")),
        )


@dataclass
class RenderJob:
    audio_path: Path
    output_path: Path
    settings: RenderSettings
    spectrum_config: SpectrumConfig
    lyric_style: LyricStyle
    lyric_track: Optional[LyricTrack] = None
    background: BackgroundSpec = field(default_factory=BackgroundSpec)
    logo: LogoSpec = field(default_factory=LogoSpec)
    animation: AnimationOverlaySpec = field(default_factory=AnimationOverlaySpec)
    transcribe_if_missing: bool = True
    whisper_model: str = "base"
    language: str = "auto"


@dataclass
class RenderResult:
    success: bool
    output_path: Optional[Path]
    duration_seconds: float
    error: Optional[str] = None


# --------------------------------------------------------------- engine


class RenderEngine:
    """Orchestrates the render pipeline for a single :class:`RenderJob`."""

    def __init__(self, ffmpeg_manager: FFmpegManager) -> None:
        self.ffmpeg = ffmpeg_manager
        self._cancel_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # not paused by default

    # ------------------------------------------------------------ controls

    def cancel(self) -> None:
        self._cancel_event.set()

    def pause(self) -> None:
        self._pause_event.clear()

    def resume(self) -> None:
        self._pause_event.set()

    def reset(self) -> None:
        self._cancel_event.clear()
        self._pause_event.set()

    # ------------------------------------------------------------ render

    def render(
        self,
        job: RenderJob,
        progress: Optional[ProgressCallback] = None,
        log_cb: Optional[LogCallback] = None,
    ) -> RenderResult:
        """Render a single job. Returns a :class:`RenderResult`."""
        self.reset()
        ffmpeg_status = self.ffmpeg.status(refresh=True)
        if not ffmpeg_status.installed or ffmpeg_status.path is None:
            msg = "FFmpeg is not available. Please install it first."
            logger.error(msg)
            return RenderResult(False, None, 0.0, msg)

        validators.ensure_audio(job.audio_path)
        file_utils.ensure_dir(job.output_path.parent)

        width, height = validators.ensure_resolution(job.settings.resolution)
        fps = validators.ensure_fps(job.settings.fps)
        if log_cb:
            log_cb(f"Starting render: {job.audio_path.name} ({width}x{height}@{fps})")

        # Step 1 — analyse audio.
        if progress:
            progress(0.02, "Analyzing audio")
        analyzer = AudioAnalyzer(
            n_bands=job.spectrum_config.bar_count,
            fps=fps,
            smoothing=job.spectrum_config.smoothing,
        )
        frames = analyzer.analyze(job.audio_path)
        if frames.duration <= 0:
            return RenderResult(False, None, 0.0, "Failed to analyze audio (zero duration).")
        n_frames = max(1, int(round(frames.duration * fps)))

        # Step 2 — make sure we have lyrics if requested.
        lyric_engine = LyricEngine(job.lyric_style, model=job.whisper_model, language=job.language)
        if job.lyric_track is not None and not job.lyric_track.is_empty():
            lyric_engine.set_track(job.lyric_track)
        elif job.lyric_style.enabled and job.transcribe_if_missing:
            try:
                if progress:
                    progress(0.05, "Transcribing lyrics")
                lyric_engine.transcribe(
                    job.audio_path,
                    progress_cb=lambda p: progress(0.05 + p * 0.10, "Transcribing lyrics") if progress else None,
                )
            except Exception as exc:  # tolerant: render without lyrics
                logger.warning("Transcription failed: %s", exc)
                if log_cb:
                    log_cb(f"Lyrics transcription failed ({exc}); rendering without lyrics.")
                job.lyric_style = LyricStyle.from_dict(
                    {**vars(job.lyric_style), "enabled": False}
                )

        # Step 3 — pre-build static background canvas (cheap).
        background_layer = _prepare_background(job.background, (width, height))

        # Step 4 — pre-load logo + animation overlay.
        logo_layer = _prepare_logo(job.logo, (width, height))
        animation = _AnimationOverlayPlayer(job.animation, (width, height), frames.duration)

        # Step 5 — pipe frames into FFmpeg.
        spectrum_engine = SpectrumEngine(job.spectrum_config)
        beat_iter = _BeatIterator(frames.beat_times)
        ffmpeg_cmd = self._build_ffmpeg_command(ffmpeg_status.path, job, fps, (width, height), frames.duration)
        if log_cb:
            log_cb("FFmpeg: " + " ".join(shlex.quote(c) for c in ffmpeg_cmd))
        logger.info("FFmpeg cmd: %s", " ".join(ffmpeg_cmd))

        start_time = time_module.time()
        try:
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except OSError as exc:
            msg = f"Could not launch FFmpeg: {exc}"
            logger.error(msg)
            return RenderResult(False, None, 0.0, msg)

        last_progress = -1.0
        try:
            assert process.stdin is not None
            for frame_idx in range(n_frames):
                if self._cancel_event.is_set():
                    if log_cb:
                        log_cb("Render cancelled by user.")
                    process.stdin.close()
                    process.terminate()
                    process.wait(timeout=10)
                    return RenderResult(False, None, time_module.time() - start_time, "Cancelled.")

                # Pause support — block until resumed.
                self._pause_event.wait()

                t = frame_idx / fps
                bands = _safe_index(frames.magnitudes, frame_idx)
                energy = _safe_value(frames.energy, frame_idx)
                bass = _safe_value(frames.bass, frame_idx)
                mid = _safe_value(frames.mid, frame_idx)
                treble = _safe_value(frames.treble, frame_idx)
                beat_active = beat_iter.update(t)
                beat_pulse = spectrum_engine.update_beat(beat_active, 1.0 / fps)

                frame = self._compose_frame(
                    size=(width, height),
                    background=background_layer.copy(),
                    spectrum_engine=spectrum_engine,
                    lyric_engine=lyric_engine,
                    bands=bands,
                    energy=energy,
                    bass=bass,
                    mid=mid,
                    treble=treble,
                    beat_pulse=beat_pulse,
                    time=t,
                    logo_layer=logo_layer,
                    logo_spec=job.logo,
                    animation=animation,
                )

                process.stdin.write(frame.tobytes())

                if progress:
                    pct = 0.15 + (frame_idx + 1) / n_frames * 0.85
                    if pct - last_progress > 0.005:
                        progress(pct, f"Encoding frame {frame_idx + 1}/{n_frames}")
                        last_progress = pct

            process.stdin.close()
            ret = process.wait(timeout=120)
        except BrokenPipeError:
            ret = process.wait(timeout=10)
        finally:
            stderr = ""
            if process.stderr is not None:
                try:
                    stderr = process.stderr.read().decode("utf-8", errors="replace")
                except Exception:
                    stderr = ""
                if log_cb and stderr:
                    log_cb(stderr.splitlines()[-1] if stderr.strip() else "")

        duration = time_module.time() - start_time
        if ret != 0:
            msg = f"FFmpeg exited with status {ret}: {stderr.strip()[-400:]}"
            logger.error(msg)
            return RenderResult(False, None, duration, msg)
        if progress:
            progress(1.0, "Done")
        if log_cb:
            log_cb(f"Render complete in {duration:0.1f}s -> {job.output_path}")
        return RenderResult(True, job.output_path, duration)

    # ------------------------------------------------------------ helpers

    def _compose_frame(
        self,
        *,
        size: Tuple[int, int],
        background: Image.Image,
        spectrum_engine: SpectrumEngine,
        lyric_engine: LyricEngine,
        bands,
        energy: float,
        bass: float,
        mid: float,
        treble: float,
        beat_pulse: float,
        time: float,
        logo_layer: Optional[Image.Image],
        logo_spec: LogoSpec,
        animation: "_AnimationOverlayPlayer",
    ) -> Image.Image:
        canvas = background  # already RGB sized to (width, height)
        spectrum_layer = spectrum_engine.render_frame(
            size=size,
            bands=bands,
            energy=energy,
            bass=bass,
            mid=mid,
            treble=treble,
            beat_pulse=beat_pulse,
            time=time,
        )
        canvas = canvas.convert("RGBA")
        canvas.alpha_composite(spectrum_layer)

        lyric_layer = lyric_engine.render_frame(size, time)
        if lyric_layer is not None:
            canvas.alpha_composite(lyric_layer)

        animation_layer = animation.frame_at(time)
        if animation_layer is not None:
            canvas.alpha_composite(animation_layer)

        if logo_layer is not None:
            x, y = _logo_position(logo_spec, size, logo_layer.size)
            faded = _apply_logo_fade(logo_layer, logo_spec, time, animation.duration)
            canvas.alpha_composite(faded, (x, y))

        return canvas.convert("RGB")

    def _build_ffmpeg_command(
        self,
        ffmpeg_path: Path,
        job: RenderJob,
        fps: int,
        size: Tuple[int, int],
        duration: float,
    ) -> List[str]:
        width, height = size
        codec = "libx264" if job.settings.codec.lower() in ("h264", "libx264") else "libx265"
        cmd: List[str] = [
            str(ffmpeg_path),
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{width}x{height}",
            "-r",
            str(fps),
            "-i",
            "-",
            "-i",
            str(job.audio_path),
            "-shortest",
            "-c:v",
            codec,
            "-pix_fmt",
            "yuv420p",
            "-preset",
            job.settings.preset,
        ]
        if job.settings.video_bitrate:
            cmd.extend(["-b:v", job.settings.video_bitrate])
        else:
            cmd.extend(["-crf", str(job.settings.crf)])
        cmd.extend([
            "-c:a",
            "aac",
            "-b:a",
            job.settings.audio_bitrate,
            "-movflags",
            "+faststart",
            str(job.output_path),
        ])
        return cmd


# ---------------------------------------------------------------- helpers


def _safe_index(matrix: Sequence[Sequence[float]], idx: int) -> Sequence[float]:
    if not matrix:
        return []
    return matrix[idx] if idx < len(matrix) else matrix[-1]


def _safe_value(values: Sequence[float], idx: int) -> float:
    if not values:
        return 0.0
    return float(values[idx]) if idx < len(values) else float(values[-1])


def _prepare_background(spec: BackgroundSpec, size: Tuple[int, int]) -> Image.Image:
    width, height = size
    if spec.type == "image" and spec.path:
        try:
            image = Image.open(spec.path).convert("RGB")
            return _fit_image(image, (width, height), spec.fit_mode)
        except (OSError, ValueError):
            logger.warning("Could not open background image %s; using solid colour.", spec.path)
    elif spec.type == "video" and spec.path:
        # Use the first frame as a static background. A future iteration can
        # animate the video frame-by-frame; that requires keeping the video
        # decoder alive throughout the render.
        try:
            import cv2  # type: ignore

            cap = cv2.VideoCapture(spec.path)
            ok, frame = cap.read()
            cap.release()
            if ok:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(rgb)
                return _fit_image(image, (width, height), spec.fit_mode)
        except Exception as exc:  # pragma: no cover - tolerant
            logger.warning("Could not read video background %s (%s); using solid.", spec.path, exc)
    elif spec.type == "gradient" and spec.gradient:
        return _make_gradient(spec.gradient, (width, height))

    color = ImageColor.getrgb(spec.color)
    return Image.new("RGB", (width, height), color)


def _fit_image(image: Image.Image, size: Tuple[int, int], mode: str) -> Image.Image:
    width, height = size
    if mode == "stretch":
        return image.resize((width, height), Image.LANCZOS)
    if mode == "contain":
        canvas = Image.new("RGB", (width, height), (0, 0, 0))
        ratio = min(width / image.width, height / image.height)
        new_size = (max(1, int(image.width * ratio)), max(1, int(image.height * ratio)))
        resized = image.resize(new_size, Image.LANCZOS)
        canvas.paste(resized, ((width - new_size[0]) // 2, (height - new_size[1]) // 2))
        return canvas
    if mode == "blur":
        canvas = image.resize((width, height), Image.LANCZOS).filter(
            ImageFilter.GaussianBlur(radius=24)
        )
        ratio = min(width / image.width, height / image.height)
        new_size = (max(1, int(image.width * ratio)), max(1, int(image.height * ratio)))
        resized = image.resize(new_size, Image.LANCZOS)
        canvas.paste(resized, ((width - new_size[0]) // 2, (height - new_size[1]) // 2))
        return canvas
    # cover
    ratio = max(width / image.width, height / image.height)
    new_size = (max(1, int(image.width * ratio)), max(1, int(image.height * ratio)))
    resized = image.resize(new_size, Image.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def _make_gradient(stops: List[str], size: Tuple[int, int]) -> Image.Image:
    width, height = size
    colors = [ImageColor.getrgb(c) for c in stops] or [(15, 17, 22), (31, 34, 51)]
    gradient = Image.new("RGB", (1, height), colors[0])
    for y in range(height):
        t = y / max(1, height - 1)
        idx = min(len(colors) - 2, int(t * (len(colors) - 1)))
        local_t = (t * (len(colors) - 1)) - idx
        c1, c2 = colors[idx], colors[idx + 1]
        gradient.putpixel(
            (0, y),
            (
                int(c1[0] + (c2[0] - c1[0]) * local_t),
                int(c1[1] + (c2[1] - c1[1]) * local_t),
                int(c1[2] + (c2[2] - c1[2]) * local_t),
            ),
        )
    return gradient.resize((width, height), Image.NEAREST)


def _prepare_logo(spec: LogoSpec, size: Tuple[int, int]) -> Optional[Image.Image]:
    if not spec.enabled or not spec.path:
        return None
    try:
        logo = Image.open(spec.path).convert("RGBA")
    except (OSError, ValueError):
        logger.warning("Cannot open logo %s", spec.path)
        return None
    target_w = max(8, int(size[0] * spec.size))
    ratio = target_w / logo.width
    target_h = max(8, int(logo.height * ratio))
    return logo.resize((target_w, target_h), Image.LANCZOS)


def _logo_position(spec: LogoSpec, canvas: Tuple[int, int], logo_size: Tuple[int, int]) -> Tuple[int, int]:
    cw, ch = canvas
    lw, lh = logo_size
    margin = spec.margin
    presets = {
        "top_left": (margin, margin),
        "top_right": (cw - lw - margin, margin),
        "bottom_left": (margin, ch - lh - margin),
        "bottom_right": (cw - lw - margin, ch - lh - margin),
    }
    if spec.position in presets:
        return presets[spec.position]
    # Custom X/Y in [0, 1].
    return (
        int(cw * spec.x - lw / 2),
        int(ch * spec.y - lh / 2),
    )


def _apply_logo_fade(layer: Image.Image, spec: LogoSpec, time: float, total_duration: float) -> Image.Image:
    alpha_factor = spec.opacity
    if spec.fade_in > 0 and time < spec.fade_in:
        alpha_factor *= time / spec.fade_in
    fade_out_start = max(0.0, total_duration - spec.fade_out)
    if spec.fade_out > 0 and time > fade_out_start:
        alpha_factor *= max(0.0, 1.0 - (time - fade_out_start) / spec.fade_out)
    alpha_factor = max(0.0, min(1.0, alpha_factor))
    if alpha_factor >= 0.999:
        return layer
    base_alpha = layer.split()[3]
    new_alpha = base_alpha.point(lambda v: int(v * alpha_factor))
    out = layer.copy()
    out.putalpha(new_alpha)
    return out


class _AnimationOverlayPlayer:
    """Lazy reader for the optional video / GIF overlay."""

    def __init__(self, spec: AnimationOverlaySpec, size: Tuple[int, int], duration: float) -> None:
        self.spec = spec
        self.size = size
        self.duration = duration
        self._frames: Optional[List[Image.Image]] = None
        self._fps = 30.0
        self._start = self._compute_start()
        self._end = self._start + max(0.1, spec.duration)

    def _compute_start(self) -> float:
        if self.spec.placement == "start":
            return 0.0
        if self.spec.placement == "middle":
            return max(0.0, self.duration / 2 - self.spec.duration / 2)
        if self.spec.placement == "end":
            return max(0.0, self.duration - self.spec.duration)
        return max(0.0, float(self.spec.start_at))

    def _ensure_loaded(self) -> None:
        if self._frames is not None or not self.spec.enabled or not self.spec.path:
            return
        try:
            if self.spec.path.lower().endswith(".gif"):
                self._frames = list(self._iter_gif(self.spec.path))
                self._fps = 12.0
            else:
                self._frames = list(self._iter_video(self.spec.path))
        except Exception as exc:  # pragma: no cover - tolerant
            logger.warning("Animation overlay disabled: %s", exc)
            self._frames = []

    def _iter_gif(self, path: str):
        with Image.open(path) as im:
            for i in range(getattr(im, "n_frames", 1)):
                im.seek(i)
                yield im.convert("RGBA").resize(self.size, Image.LANCZOS)

    def _iter_video(self, path: str):  # pragma: no cover - heavy
        import cv2  # type: ignore

        cap = cv2.VideoCapture(path)
        try:
            self._fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                yield Image.fromarray(rgb).convert("RGBA").resize(self.size, Image.LANCZOS)
        finally:
            cap.release()

    def frame_at(self, time: float) -> Optional[Image.Image]:
        if not self.spec.enabled or not self.spec.path:
            return None
        if time < self._start or time > self._end:
            return None
        self._ensure_loaded()
        if not self._frames:
            return None
        rel = time - self._start
        idx = int(rel * self._fps) % len(self._frames)
        layer = self._frames[idx]
        if self.spec.opacity < 0.999:
            base_alpha = layer.split()[3]
            new_alpha = base_alpha.point(lambda v: int(v * self.spec.opacity))
            layer = layer.copy()
            layer.putalpha(new_alpha)
        return layer


class _BeatIterator:
    def __init__(self, beats: Sequence[float]) -> None:
        self._beats = list(beats)
        self._index = 0

    def update(self, time: float) -> bool:
        if self._index >= len(self._beats):
            return False
        if time >= self._beats[self._index]:
            self._index += 1
            return True
        return False
