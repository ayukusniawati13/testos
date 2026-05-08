"""Log panel that mirrors the Python logger output."""
from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget

from app.utils import logger as app_logger


class LogPanel(QWidget):
    """Live, scrollable log view backed by the application logger."""

    new_log = Signal(str, int)  # text, levelno -- emitted from logger thread

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.text, 1)

        controls = QHBoxLayout()
        controls.addStretch(1)
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear)
        controls.addWidget(self.clear_btn)
        layout.addLayout(controls)

        self.new_log.connect(self._append, Qt.ConnectionType.QueuedConnection)
        app_logger.add_listener(self._on_log_record)

    def _on_log_record(self, text: str, levelno: int) -> None:
        # Called from any thread -- forward to the Qt main thread.
        self.new_log.emit(text, levelno)

    def _append(self, text: str, levelno: int) -> None:
        color = "#e6e8ee"
        if levelno >= logging.ERROR:
            color = "#ff7676"
        elif levelno >= logging.WARNING:
            color = "#f5c042"
        elif levelno >= logging.INFO:
            color = "#9bc4ff"
        else:
            color = "#7d869c"
        cursor = self.text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(
            f"<span style='color: {color}; white-space: pre;'>{_escape(text)}</span><br>"
        )
        self.text.setTextCursor(cursor)
        self.text.ensureCursorVisible()

    def append_plain(self, text: str) -> None:
        self._append(text, logging.INFO)

    def clear(self) -> None:
        self.text.clear()


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace(" ", "&nbsp;")
    )
