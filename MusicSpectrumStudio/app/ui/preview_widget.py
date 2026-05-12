"""Live preview pane on the right of the main window."""

from __future__ import annotations

import logging

import cv2
import numpy as np
from PySide6.QtCore import QSize, Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ..config import AppConfig
from ..core.render_pipeline import render_preview_frame
from ..core.transcribe import TranscriptionResult

logger = logging.getLogger(__name__)


class _PreviewWorker(QThread):
    finished_with_frame = Signal(object)

    def __init__(self, cfg: AppConfig, audio_path: str | None, transcription: TranscriptionResult | None, t: float, parent: QWidget | None = None):
        super().__init__(parent)
        self.cfg = cfg
        self.audio_path = audio_path
        self.transcription = transcription
        self.t = t

    def run(self) -> None:
        try:
            frame = render_preview_frame(
                self.cfg,
                self.audio_path,
                self.transcription,
                width=960,
                height=540,
                at_seconds=self.t,
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Preview gagal: %s", exc)
            self.finished_with_frame.emit(None)
            return
        self.finished_with_frame.emit(frame)


class PreviewWidget(QFrame):
    requestRefresh = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("preview")
        self.setStyleSheet("#preview { background:#000; border:1px solid #2A3245; border-radius:10px; }")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(QSize(540, 320))
        self._worker: _PreviewWorker | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        self.image_label = QLabel("Preview akan muncul di sini")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("color:#6C7689;")
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        outer.addWidget(self.image_label, stretch=1)

        controls = QHBoxLayout()
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(0, 300)
        self.time_slider.setValue(20)
        self.time_slider.setToolTip("Geser untuk pratinjau pada detik tertentu")
        self.time_slider.valueChanged.connect(lambda _: self.requestRefresh.emit())
        controls.addWidget(QLabel("t (s)"))
        controls.addWidget(self.time_slider)
        refresh = QPushButton("Refresh")
        refresh.setProperty("secondary", True)
        refresh.clicked.connect(lambda: self.requestRefresh.emit())
        controls.addWidget(refresh)
        outer.addLayout(controls)

        self._last_pix: QPixmap | None = None

    def time_seconds(self) -> float:
        return float(self.time_slider.value()) / 10.0

    def update_preview(self, cfg: AppConfig, audio_path: str | None, transcription: TranscriptionResult | None) -> None:
        if self._worker and self._worker.isRunning():
            return
        worker = _PreviewWorker(cfg, audio_path, transcription, self.time_seconds(), self)
        worker.finished_with_frame.connect(self._on_frame)
        worker.start()
        self._worker = worker

    def _on_frame(self, frame: object) -> None:
        if frame is None:
            self.image_label.setText("Gagal memuat pratinjau")
            return
        if not isinstance(frame, np.ndarray):
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        qimg = QImage(rgb.data, w, h, w * 3, QImage.Format_RGB888).copy()
        pix = QPixmap.fromImage(qimg)
        self._last_pix = pix
        self._render_scaled()

    def _render_scaled(self) -> None:
        if self._last_pix is None:
            return
        target = self.image_label.size()
        scaled = self._last_pix.scaled(target, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)

    def resizeEvent(self, event) -> None:  # noqa: D401
        super().resizeEvent(event)
        self._render_scaled()
