"""Batch processing pipeline.

Manages a queue of :class:`RenderJob` objects, executes them sequentially on
a worker thread, surfaces real-time status (waiting / processing / done /
failed), and supports pause / resume / cancel from the GUI.

The processor is GUI-free; the GUI binds to it through plain callbacks
(``on_status``, ``on_progress``, ``on_log``).
"""
from __future__ import annotations

import random
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

from app.core.ffmpeg_manager import FFmpegManager
from app.core.render_engine import RenderEngine, RenderJob, RenderResult
from app.utils import file_utils
from app.utils.logger import get_logger

logger = get_logger("batch_processor")


class JobStatus(str, Enum):
    WAITING = "waiting"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchEntry:
    job: RenderJob
    status: JobStatus = JobStatus.WAITING
    progress: float = 0.0
    message: str = ""
    error: Optional[str] = None
    result: Optional[RenderResult] = None

    @property
    def label(self) -> str:
        return self.job.audio_path.name


StatusCallback = Callable[[int, BatchEntry], None]
ProgressCallback = Callable[[int, float, str], None]
LogCallback = Callable[[str], None]


class BatchProcessor:
    """Sequential job runner with pause / cancel support."""

    def __init__(self, ffmpeg_manager: FFmpegManager) -> None:
        self.ffmpeg = ffmpeg_manager
        self._engine = RenderEngine(ffmpeg_manager)
        self._entries: List[BatchEntry] = []
        self._thread: Optional[threading.Thread] = None
        self._cancel_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._lock = threading.Lock()
        self.on_status: Optional[StatusCallback] = None
        self.on_progress: Optional[ProgressCallback] = None
        self.on_log: Optional[LogCallback] = None
        self.on_finished: Optional[Callable[[List[BatchEntry]], None]] = None

    # ------------------------------------------------------------ queue mgmt

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def add(self, job: RenderJob) -> int:
        entry = BatchEntry(job=job)
        with self._lock:
            self._entries.append(entry)
            idx = len(self._entries) - 1
        if self.on_status:
            self.on_status(idx, entry)
        return idx

    def entries(self) -> List[BatchEntry]:
        with self._lock:
            return list(self._entries)

    # ------------------------------------------------------------ control

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running():
            return
        self._cancel_event.clear()
        self._pause_event.set()
        self._thread = threading.Thread(target=self._run, name="BatchProcessor", daemon=True)
        self._thread.start()

    def pause(self) -> None:
        self._pause_event.clear()
        self._engine.pause()

    def resume(self) -> None:
        self._pause_event.set()
        self._engine.resume()

    def cancel(self) -> None:
        self._cancel_event.set()
        self._engine.cancel()
        # Make sure we don't deadlock on a paused queue.
        self._pause_event.set()

    # ------------------------------------------------------------ runner

    def _run(self) -> None:
        try:
            while True:
                if self._cancel_event.is_set():
                    break
                self._pause_event.wait()

                with self._lock:
                    next_idx = next(
                        (
                            i
                            for i, e in enumerate(self._entries)
                            if e.status == JobStatus.WAITING
                        ),
                        None,
                    )
                if next_idx is None:
                    break
                entry = self._entries[next_idx]
                entry.status = JobStatus.PROCESSING
                if self.on_status:
                    self.on_status(next_idx, entry)

                try:
                    result = self._engine.render(
                        entry.job,
                        progress=lambda pct, msg, idx=next_idx: self._on_progress(idx, pct, msg),
                        log_cb=self._on_log,
                    )
                    entry.result = result
                    if self._cancel_event.is_set():
                        entry.status = JobStatus.CANCELLED
                        entry.message = "Cancelled by user."
                    elif result.success:
                        entry.status = JobStatus.DONE
                        entry.progress = 1.0
                        entry.message = "Done"
                    else:
                        entry.status = JobStatus.FAILED
                        entry.error = result.error
                        entry.message = result.error or "Failed"
                except Exception as exc:  # pragma: no cover - defensive
                    logger.exception("Batch entry failed: %s", exc)
                    entry.status = JobStatus.FAILED
                    entry.error = str(exc)
                    entry.message = str(exc)

                if self.on_status:
                    self.on_status(next_idx, entry)
        finally:
            entries = self.entries()
            if self.on_finished:
                self.on_finished(entries)

    def _on_progress(self, idx: int, pct: float, msg: str) -> None:
        with self._lock:
            if 0 <= idx < len(self._entries):
                self._entries[idx].progress = pct
                self._entries[idx].message = msg
        if self.on_progress:
            self.on_progress(idx, pct, msg)

    def _on_log(self, msg: str) -> None:
        if self.on_log and msg:
            self.on_log(msg)


# --------------------------------------------------------------- matching


SUPPORTED_MATCH_STRATEGIES: Sequence[str] = (
    "random",
    "same_name",
    "by_orientation",
    "one_for_all",
)


def match_backgrounds(
    audio_files: Sequence[Path],
    background_files: Sequence[Path],
    strategy: str,
    shared_background: Optional[Path] = None,
    seed: Optional[int] = None,
) -> Dict[Path, Optional[Path]]:
    """Return a mapping ``audio -> background`` for a batch."""
    if not audio_files:
        return {}
    if not background_files and strategy not in ("one_for_all",):
        return {audio: None for audio in audio_files}

    rng = random.Random(seed)
    result: Dict[Path, Optional[Path]] = {}

    if strategy == "one_for_all":
        chosen = shared_background or (background_files[0] if background_files else None)
        return {audio: chosen for audio in audio_files}

    if strategy == "same_name":
        index = {p.stem.lower(): p for p in background_files}
        for audio in audio_files:
            result[audio] = index.get(audio.stem.lower())
        # Fill missing matches with random selections.
        leftover = [p for p in background_files if p not in set(result.values())]
        for audio, bg in result.items():
            if bg is None and leftover:
                result[audio] = rng.choice(leftover)
        return result

    if strategy == "by_orientation":
        # Split backgrounds by aspect ratio (>=1 landscape, <1 portrait).
        landscape, portrait = [], []
        for p in background_files:
            ratio = _ratio_of(p)
            (landscape if ratio >= 1 else portrait).append(p)
        for audio in audio_files:
            # Prefer landscape unless the file name hints at vertical.
            target_pool = landscape or background_files
            if "vertical" in audio.stem.lower() or "9x16" in audio.stem.lower():
                target_pool = portrait or target_pool
            result[audio] = rng.choice(list(target_pool))
        return result

    # default: random
    for audio in audio_files:
        result[audio] = rng.choice(list(background_files))
    return result


def _ratio_of(path: Path) -> float:
    try:
        if path.suffix.lower() in file_utils.IMAGE_EXTS:
            from PIL import Image  # local import to keep startup fast

            with Image.open(path) as img:
                return img.width / max(1, img.height)
        if path.suffix.lower() in file_utils.VIDEO_EXTS:
            try:
                import cv2  # type: ignore

                cap = cv2.VideoCapture(str(path))
                w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                cap.release()
                if h > 0:
                    return w / h
            except Exception:
                return 1.0
    except Exception:
        return 1.0
    return 1.0
