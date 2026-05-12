"""Reusable Qt widgets."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (
    QColorDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ColorButton(QPushButton):
    """Square button that opens a colour picker."""

    colorChanged = Signal(str)

    def __init__(self, hex_value: str = "#FFFFFF", parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("secondary", True)
        self.setFixedSize(34, 30)
        self._value = "#FFFFFF"
        self.set_color(hex_value)
        self.clicked.connect(self._on_click)

    def color(self) -> str:
        return self._value

    def set_color(self, hex_value: str) -> None:
        if not hex_value or not hex_value.startswith("#"):
            hex_value = "#FFFFFF"
        self._value = hex_value
        self._render_swatch()

    def _render_swatch(self) -> None:
        pix = QPixmap(28, 22)
        pix.fill(QColor(self._value))
        painter = QPainter(pix)
        painter.setPen(QColor("#1F2533"))
        painter.drawRect(0, 0, 27, 21)
        painter.end()
        self.setIcon(pix)
        self.setIconSize(pix.size())
        self.setText("")
        self.setToolTip(self._value)

    def _on_click(self) -> None:
        c = QColorDialog.getColor(QColor(self._value), self.window(), "Pilih Warna")
        if c.isValid():
            self.set_color(c.name())
            self.colorChanged.emit(self._value)


class Divider(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("role", "divider")
        self.setFixedHeight(1)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


class StatusBadge(QLabel):
    OK = "badge_ok"
    BAD = "badge_bad"
    WARN = "badge_warn"

    def __init__(self, text: str = "", state: str = "badge_warn"):
        super().__init__(text)
        self.set_state(state)

    def set_state(self, state: str) -> None:
        self.setProperty("role", state)
        self.style().unpolish(self)
        self.style().polish(self)


class Card(QWidget):
    def __init__(self, title: str | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("card")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        if title:
            header = QLabel(title)
            header.setProperty("role", "title")
            outer.addWidget(header)
        self.body = QVBoxLayout()
        self.body.setContentsMargins(0, 6, 0, 0)
        self.body.setSpacing(8)
        outer.addLayout(self.body)


class Row(QWidget):
    def __init__(self, *widgets: QWidget, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        for w in widgets:
            layout.addWidget(w)
