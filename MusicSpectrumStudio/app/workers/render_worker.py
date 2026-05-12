"""Background worker that drives the render pipeline."""

from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass

from PySide6.QtCore import QThread, Signal

from ..config import AppConfig
from ..core.render_pipeline import RenderProgress, render_to_file
from ..core.transcribe import TranscriptionResult

logger = logging.getLogger(__name__)


@dataclass
class RenderJob:
    cfg: AppConfig
    audio_path: str
    output_path: str
    transcription: TranscriptionResult | None


class RenderWorker(QThread):
    progressed = Signal(float, str)  # (fraction, message)
    finished_one = Signal(str)  # output path on success
    failed = Signal(str)
    all_done = Signal()

    def __init__(self, jobs: list[RenderJob], parent=None):
        super().__init__(parent)
        self.jobs = jobs
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    def _make_progress_cb(self, idx: int, total: int):
        def cb(progress: RenderProgress) -> None:
            overall = (idx + progress.fraction) / max(1, total)
            self.progressed.emit(overall, f"Frame {progress.frame}/{progress.total}")
        return cb

    def run(self) -> None:
        total = len(self.jobs)
        for i, job in enumerate(self.jobs):
            if self._cancel.is_set():
                break
            try:
                self.progressed.emit(
                    (i + 0) / max(1, total),
                    f"Render {i + 1}/{total}: {os.path.basename(job.audio_path)}",
                )
                render_to_file(
                    job.cfg,
                    audio_path=job.audio_path,
                    output_path=job.output_path,
                    transcription=job.transcription,
                    progress=self._make_progress_cb(i, total),
                    cancel=self._cancel,
                )
                self.finished_one.emit(job.output_path)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Render gagal untuk %s: %s", job.audio_path, exc)
                self.failed.emit(f"{os.path.basename(job.audio_path)}: {exc}")
        self.all_done.emit()
