"""FFmpeg status banner with install button."""

from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QPushButton

from ..core.ffmpeg_check import FFmpegStatus, check_ffmpeg, install_ffmpeg_online
from .widgets import StatusBadge

logger = logging.getLogger(__name__)


class _InstallWorker(QThread):
    progressed = Signal(str)
    finished_with_status = Signal(object)

    def run(self) -> None:  # noqa: D401
        status = install_ffmpeg_online(progress=self.progressed.emit)
        self.finished_with_status.emit(status)


class FfmpegStatusBar(QGroupBox):
    statusChanged = Signal(object)

    def __init__(self):
        super().__init__("Status FFmpeg")
        layout = QHBoxLayout(self)
        self.badge = StatusBadge("Mengecek...", StatusBadge.WARN)
        self.detail = QLabel("")
        self.detail.setProperty("role", "muted")
        self.install_btn = QPushButton("Install FFmpeg (online)")
        self.install_btn.setProperty("success", True)
        self.install_btn.clicked.connect(self._install)
        layout.addWidget(self.badge)
        layout.addWidget(self.detail, stretch=1)
        layout.addWidget(self.install_btn)
        self._worker: _InstallWorker | None = None
        self.refresh()

    def refresh(self) -> None:
        status = check_ffmpeg()
        self._apply_status(status)

    def _apply_status(self, status: FFmpegStatus) -> None:
        if status.available:
            self.badge.setText("Terinstall")
            self.badge.set_state(StatusBadge.OK)
            self.detail.setText(f"{status.source} · {status.version or ''}")
            self.install_btn.setText("Re-cek")
        else:
            self.badge.setText("Belum tersedia")
            self.badge.set_state(StatusBadge.BAD)
            self.detail.setText("Klik tombol di kanan untuk mengunduh & install FFmpeg secara online.")
            self.install_btn.setText("Install FFmpeg (online)")
        self.statusChanged.emit(status)

    def _install(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self.badge.setText("Mengunduh...")
        self.badge.set_state(StatusBadge.WARN)
        self.install_btn.setEnabled(False)
        self._worker = _InstallWorker(self)
        self._worker.progressed.connect(lambda msg: self.detail.setText(msg))
        self._worker.finished_with_status.connect(self._on_done)
        self._worker.start()

    def _on_done(self, status: FFmpegStatus) -> None:
        self.install_btn.setEnabled(True)
        self._apply_status(status)
