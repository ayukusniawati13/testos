"""Dialog: detect FFmpeg + offer auto-install."""
from __future__ import annotations

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from app.core.ffmpeg_manager import FFmpegManager, manual_install_instructions
from app.utils.logger import get_logger

logger = get_logger("ffmpeg_dialog")


class _InstallWorker(QObject):
    progress = Signal(float, str)
    finished = Signal(bool, str)

    def __init__(self, manager: FFmpegManager) -> None:
        super().__init__()
        self.manager = manager

    def run(self) -> None:
        try:
            status = self.manager.auto_install(progress=self._on_progress)
            if status.installed:
                self.finished.emit(True, str(status.path))
            else:
                self.finished.emit(False, "Installer reported success but FFmpeg is still missing.")
        except Exception as exc:  # pragma: no cover - depends on net
            logger.exception("FFmpeg auto-install failed")
            self.finished.emit(False, str(exc))

    def _on_progress(self, pct: float, msg: str) -> None:
        self.progress.emit(pct, msg)


class FFmpegDialog(QDialog):
    """Modal dialog showing the FFmpeg status and an install button."""

    def __init__(self, manager: FFmpegManager, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("FFmpeg")
        self.setMinimumWidth(420)
        self.manager = manager

        self.status_label = QLabel()
        self.path_label = QLabel()
        self.path_label.setWordWrap(True)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)
        self.message = QLabel("")
        self.message.setStyleSheet("color: #9aa0b3;")

        self.btn_install = QPushButton("Install FFmpeg Online")
        self.btn_install.setObjectName("primary")
        self.btn_install.clicked.connect(self._start_install)

        self.btn_recheck = QPushButton("Re-check")
        self.btn_recheck.clicked.connect(self.refresh)

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)

        outer = QVBoxLayout(self)
        outer.addWidget(self.status_label)
        outer.addWidget(self.path_label)
        outer.addWidget(self.progress)
        outer.addWidget(self.message)
        button_row = QHBoxLayout()
        button_row.addWidget(self.btn_install)
        button_row.addWidget(self.btn_recheck)
        button_row.addStretch(1)
        button_row.addWidget(self.btn_close)
        outer.addLayout(button_row)

        self._thread = None  # type: ignore[var-annotated]
        self._worker = None  # type: ignore[var-annotated]

        self.refresh()

    def refresh(self) -> None:
        status = self.manager.status(refresh=True)
        if status.installed:
            self.status_label.setText("FFmpeg installed.")
            self.status_label.setStyleSheet("color: #62d4a4; font-weight: 600;")
            self.path_label.setText(f"{status.path}\n{status.version or ''}")
            self.btn_install.setEnabled(False)
            self.btn_install.setText("Already installed")
        else:
            self.status_label.setText("FFmpeg not found.")
            self.status_label.setStyleSheet("color: #ff7676; font-weight: 600;")
            self.path_label.setText("Click 'Install FFmpeg Online' to download a static build.")
            self.btn_install.setEnabled(True)
            self.btn_install.setText("Install FFmpeg Online")

    def _start_install(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            return
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.message.setText("Downloading FFmpeg...")
        self.btn_install.setEnabled(False)

        worker = _InstallWorker(self.manager)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._on_progress)
        worker.finished.connect(self._on_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._thread = thread
        self._worker = worker
        thread.start()

    def _on_progress(self, pct: float, msg: str) -> None:
        self.progress.setValue(int(pct * 100))
        self.message.setText(msg)

    def _on_finished(self, ok: bool, message: str) -> None:
        self.progress.setVisible(False)
        self.btn_install.setEnabled(True)
        self._thread = None
        self._worker = None
        if ok:
            self.message.setText(f"Installed at {message}")
            self.refresh()
        else:
            QMessageBox.critical(
                self,
                "FFmpeg install failed",
                f"{message}\n\n{manual_install_instructions()}",
            )
            self.message.setText("Install failed. See manual instructions.")
