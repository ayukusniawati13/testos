"""Vertical navigation sidebar with checkable buttons."""
from __future__ import annotations

from typing import List, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QPushButton, QVBoxLayout, QWidget, QLabel


class Sidebar(QWidget):
    """Sidebar with mode buttons. Emits ``page_changed(index)`` on selection."""

    page_changed = Signal(int)

    def __init__(self, items: List[Tuple[str, str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(200)
        self.setMaximumWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(0)

        title = QLabel("Spectrum Lyric\nVideo Maker")
        title.setStyleSheet(
            "padding: 12px 18px; font-size: 15px; font-weight: 700; color: #ffffff;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #1c1f2a; border: none;")
        layout.addWidget(separator)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: list[QPushButton] = []

        for index, (title_text, _icon) in enumerate(items):
            button = QPushButton(title_text)
            button.setObjectName("sidebarItem")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            self._buttons.append(button)
            self._group.addButton(button, index)
            layout.addWidget(button)
            button.clicked.connect(lambda _checked=False, idx=index: self.page_changed.emit(idx))

        layout.addStretch(1)

        if self._buttons:
            self._buttons[0].setChecked(True)

    def set_active(self, index: int) -> None:
        if 0 <= index < len(self._buttons):
            self._buttons[index].setChecked(True)
