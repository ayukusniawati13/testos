"""Batch rendering manager for processing multiple music files."""

import os
import random
import logging
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from app.core.video_renderer import VideoRenderer, RenderJob, VideoConfig
from app.core.spectrum_engine import SpectrumConfig
from app.core.lyric_renderer import LyricConfig
from app.core.video_renderer import LogoConfig
from app.core.ffmpeg_manager import FFmpegManager

logger = logging.getLogger(__name__)

MUSIC_EXTS = {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".wma"}
BG_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
BG_VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
BG_ALL_EXTS = BG_IMAGE_EXTS | BG_VIDEO_EXTS


class BackgroundMode(Enum):
    SEQUENTIAL = "sequential"
    MATCH_NAME = "match_name"
    RANDOM = "random"


class JobStatus(Enum):
    PENDING = "pending"
    RENDERING = "rendering"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class BatchJob:
    music_path: str = ""
    music_name: str = ""
    lrc_path: str = ""
    lrc_status: str = "Not found"
    background_path: str = ""
    bg_status: str = "Not found"
    output_path: str = ""
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    error_message: str = ""


class BatchManager:
    def __init__(self, ffmpeg: FFmpegManager | None = None):
        self.ffmpeg = ffmpeg or FFmpegManager()
        self.jobs: list[BatchJob] = []
        self._renderer: VideoRenderer | None = None
        self._cancelled = False

    def scan_folders(self, music_folder: str, lrc_folder: str,
                     bg_folder: str, output_folder: str,
                     bg_mode: BackgroundMode = BackgroundMode.MATCH_NAME,
                     default_bg: str = "") -> list[BatchJob]:
        self.jobs.clear()

        music_files = []
        if os.path.isdir(music_folder):
            for f in sorted(os.listdir(music_folder)):
                ext = os.path.splitext(f)[1].lower()
                if ext in MUSIC_EXTS:
                    music_files.append(os.path.join(music_folder, f))

        lrc_map: dict[str, str] = {}
        if os.path.isdir(lrc_folder):
            for f in os.listdir(lrc_folder):
                if f.lower().endswith(".lrc"):
                    stem = os.path.splitext(f)[0].lower()
                    lrc_map[stem] = os.path.join(lrc_folder, f)

        bg_files: list[str] = []
        bg_map: dict[str, str] = {}
        if os.path.isdir(bg_folder):
            for f in sorted(os.listdir(bg_folder)):
                ext = os.path.splitext(f)[1].lower()
                if ext in BG_ALL_EXTS:
                    full = os.path.join(bg_folder, f)
                    bg_files.append(full)
                    stem = os.path.splitext(f)[0].lower()
                    bg_map[stem] = full

        for idx, music_path in enumerate(music_files):
            music_name = os.path.splitext(os.path.basename(music_path))[0]
            stem = music_name.lower()

            job = BatchJob()
            job.music_path = music_path
            job.music_name = music_name

            if stem in lrc_map:
                job.lrc_path = lrc_map[stem]
                job.lrc_status = "Found"
            else:
                job.lrc_status = "Not found"

            if bg_mode == BackgroundMode.MATCH_NAME:
                if stem in bg_map:
                    job.background_path = bg_map[stem]
                    job.bg_status = "Matched"
                elif default_bg and os.path.isfile(default_bg):
                    job.background_path = default_bg
                    job.bg_status = "Default"
                elif bg_files:
                    job.background_path = random.choice(bg_files)
                    job.bg_status = "Random fallback"
                else:
                    job.bg_status = "Not found"
            elif bg_mode == BackgroundMode.SEQUENTIAL:
                if bg_files:
                    job.background_path = bg_files[idx % len(bg_files)]
                    job.bg_status = "Sequential"
                else:
                    job.bg_status = "Not found"
            elif bg_mode == BackgroundMode.RANDOM:
                if bg_files:
                    job.background_path = random.choice(bg_files)
                    job.bg_status = "Random"
                else:
                    job.bg_status = "Not found"

            output_name = f"{music_name}.mp4"
            job.output_path = os.path.join(output_folder, output_name)

            self.jobs.append(job)

        return self.jobs

    def render_all(self, video_config: VideoConfig,
                   spectrum_config: SpectrumConfig,
                   lyric_config: LyricConfig,
                   logo_config: LogoConfig,
                   progress_callback=None,
                   job_callback=None,
                   log_callback=None) -> None:
        self._cancelled = False
        total = len(self.jobs)
        renderer = VideoRenderer(self.ffmpeg)
        self._renderer = renderer

        for idx, job in enumerate(self.jobs):
            if self._cancelled:
                job.status = JobStatus.CANCELLED
                continue

            if not job.lrc_path:
                job.status = JobStatus.ERROR
                job.error_message = "LRC file not found"
                if job_callback:
                    job_callback(idx, job)
                continue

            job.status = JobStatus.RENDERING
            if job_callback:
                job_callback(idx, job)

            try:
                render_job = RenderJob()
                render_job.music_path = job.music_path
                render_job.lrc_path = job.lrc_path
                render_job.background_path = job.background_path
                render_job.output_path = job.output_path
                render_job.video_config = video_config
                render_job.spectrum_config = spectrum_config
                render_job.lyric_config = lyric_config
                render_job.logo_config = logo_config

                def _progress(pct: int) -> None:
                    job.progress = pct
                    if progress_callback:
                        overall = int(((idx + pct / 100) / total) * 100)
                        progress_callback(overall)
                    if job_callback:
                        job_callback(idx, job)

                def _log(msg: str) -> None:
                    if log_callback:
                        log_callback(f"[{job.music_name}] {msg}")

                success = renderer.render(render_job,
                                          progress_callback=_progress,
                                          log_callback=_log)

                if success:
                    job.status = JobStatus.COMPLETED
                    job.progress = 100
                else:
                    job.status = JobStatus.CANCELLED

            except Exception as e:
                job.status = JobStatus.ERROR
                job.error_message = str(e)
                if log_callback:
                    log_callback(f"[{job.music_name}] Error: {e}")

            if job_callback:
                job_callback(idx, job)

        self._renderer = None

    def cancel(self) -> None:
        self._cancelled = True
        if self._renderer:
            self._renderer.cancel()
