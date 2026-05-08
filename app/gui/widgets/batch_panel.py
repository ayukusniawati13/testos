"""Batch processing UI: pick folders, queue, status table, controls."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.batch_processor import (
    BatchEntry,
    JobStatus,
    SUPPORTED_MATCH_STRATEGIES,
)
from app.utils import file_utils


class BatchPanel(QGroupBox):
    """UI surface for batch mode (queue + controls)."""

    # Emitted when the user has chosen folders + clicks Build queue.
    build_queue = Signal(str, str, str, str)  # audio_folder, bg_folder, strategy, shared_bg
    start_clicked = Signal()
    pause_clicked = Signal()
    resume_clicked = Signal()
    cancel_clicked = Signal()
    clear_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Batch processing", parent)
        outer = QVBoxLayout(self)

        form = QFormLayout()
        self.audio_folder = self._build_folder_row("Music folder")
        self.bg_folder = self._build_folder_row("Background folder")
        self.strategy = QComboBox()
        self.strategy.addItems(SUPPORTED_MATCH_STRATEGIES)
        self.strategy.setCurrentText("random")
        self.shared_bg = QLineEdit()
        self.shared_bg.setPlaceholderText("Path to single background (used by 'one_for_all')")

        form.addRow("Music folder", self.audio_folder)
        form.addRow("Background folder", self.bg_folder)
        form.addRow("Match strategy", self.strategy)
        form.addRow("Shared background", self.shared_bg)
        outer.addLayout(form)

        actions = QHBoxLayout()
        self.btn_build = QPushButton("Build queue")
        self.btn_start = QPushButton("Start"); self.btn_start.setObjectName("primary")
        self.btn_pause = QPushButton("Pause")
        self.btn_resume = QPushButton("Resume")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_clear = QPushButton("Clear")
        for b in (self.btn_build, self.btn_start, self.btn_pause, self.btn_resume, self.btn_cancel, self.btn_clear):
            actions.addWidget(b)
        actions.addStretch(1)
        outer.addLayout(actions)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Audio", "Background", "Status", "Progress"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        outer.addWidget(self.table, 1)

        self.btn_build.clicked.connect(self._on_build)
        self.btn_start.clicked.connect(self.start_clicked.emit)
        self.btn_pause.clicked.connect(self.pause_clicked.emit)
        self.btn_resume.clicked.connect(self.resume_clicked.emit)
        self.btn_cancel.clicked.connect(self.cancel_clicked.emit)
        self.btn_clear.clicked.connect(self._on_clear)

    def _build_folder_row(self, dialog_title: str) -> QWidget:
        edit = QLineEdit()
        button = QPushButton("Browse")

        def pick() -> None:
            path = QFileDialog.getExistingDirectory(self, dialog_title, edit.text())
            if path:
                edit.setText(path)

        button.clicked.connect(pick)
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edit, 1)
        layout.addWidget(button)
        wrapper.line_edit = edit  # type: ignore[attr-defined]
        return wrapper

    # ------------------------------------------------------------- API

    def set_table_entries(self, entries: List[BatchEntry]) -> None:
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self._render_row(row, entry)

    def update_entry(self, idx: int, entry: BatchEntry) -> None:
        if idx >= self.table.rowCount():
            self.table.setRowCount(idx + 1)
        self._render_row(idx, entry)

    def update_progress(self, idx: int, pct: float, message: str) -> None:
        if idx >= self.table.rowCount():
            return
        progress = f"{pct * 100:0.0f}%  {message}"
        item = self.table.item(idx, 3) or QTableWidgetItem()
        item.setText(progress)
        self.table.setItem(idx, 3, item)

    def get_audio_folder(self) -> str:
        return self.audio_folder.line_edit.text().strip()  # type: ignore[attr-defined]

    def get_bg_folder(self) -> str:
        return self.bg_folder.line_edit.text().strip()  # type: ignore[attr-defined]

    def get_strategy(self) -> str:
        return self.strategy.currentText()

    def get_shared_bg(self) -> str:
        return self.shared_bg.text().strip()

    # ------------------------------------------------------------- internals

    def _render_row(self, row: int, entry: BatchEntry) -> None:
        bg_label = (
            Path(entry.job.background.path).name if entry.job.background.path else "—"
        )
        items = [
            QTableWidgetItem(entry.job.audio_path.name),
            QTableWidgetItem(bg_label),
            QTableWidgetItem(_status_label(entry.status)),
            QTableWidgetItem(f"{entry.progress * 100:0.0f}%  {entry.message}"),
        ]
        for col, item in enumerate(items):
            item.setToolTip(item.text())
            self.table.setItem(row, col, item)

    def _on_build(self) -> None:
        self.build_queue.emit(
            self.get_audio_folder(),
            self.get_bg_folder(),
            self.get_strategy(),
            self.get_shared_bg(),
        )

    def _on_clear(self) -> None:
        self.table.setRowCount(0)
        self.clear_clicked.emit()


def _status_label(status: JobStatus) -> str:
    return {
        JobStatus.WAITING: "Waiting",
        JobStatus.PROCESSING: "Processing",
        JobStatus.DONE: "Done",
        JobStatus.FAILED: "Failed",
        JobStatus.CANCELLED: "Cancelled",
    }.get(status, str(status))
