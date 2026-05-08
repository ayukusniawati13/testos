"""Background source + fit + resolution controls."""
from __future__ import annotations

from typing import Tuple

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.render_engine import BackgroundSpec


_RESOLUTION_PRESETS: list[tuple[str, Tuple[int, int]]] = [
    ("1920x1080 (Landscape)", (1920, 1080)),
    ("1080x1920 (Vertical)", (1080, 1920)),
    ("1080x1080 (Square)", (1080, 1080)),
    ("1280x720 (HD)", (1280, 720)),
    ("3840x2160 (4K)", (3840, 2160)),
    ("Custom", (0, 0)),
]


class BackgroundPanel(QGroupBox):
    settings_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("4. Background", parent)
        outer = QVBoxLayout(self)

        form = QFormLayout()
        self.type = QComboBox()
        self.type.addItems(["solid", "gradient", "image", "video"])
        self.color_btn = QPushButton("#0f1116")
        self.color_btn.clicked.connect(self._pick_color)
        self.color_btn.setStyleSheet("background-color: #0f1116; color: #ffffff;")
        self.gradient_a = QPushButton("#0f1116")
        self.gradient_b = QPushButton("#1f2233")
        self.gradient_a.clicked.connect(lambda: self._pick_gradient(0))
        self.gradient_b.clicked.connect(lambda: self._pick_gradient(1))
        self.path = QLineEdit()
        self.path.setPlaceholderText("Path to image / video / folder")
        browse = QPushButton("Browse")
        browse.clicked.connect(self._on_browse)
        path_row = QHBoxLayout()
        path_row.addWidget(self.path, 1)
        path_row.addWidget(browse)
        path_row_w = QWidget()
        path_row_w.setLayout(path_row)
        self.fit = QComboBox()
        self.fit.addItems(["cover", "contain", "stretch", "blur"])

        form.addRow("Type", self.type)
        form.addRow("Solid color", self.color_btn)
        gradient_row = QHBoxLayout()
        gradient_row.addWidget(self.gradient_a)
        gradient_row.addWidget(self.gradient_b)
        gradient_widget = QWidget(); gradient_widget.setLayout(gradient_row)
        form.addRow("Gradient", gradient_widget)
        form.addRow("Path", path_row_w)
        form.addRow("Fit mode", self.fit)
        outer.addLayout(form)

        # Resolution presets
        res_box = QGroupBox("Output resolution")
        res_form = QFormLayout(res_box)
        self.res_preset = QComboBox()
        self.res_preset.addItems([p[0] for p in _RESOLUTION_PRESETS])
        self.res_w = QSpinBox(); self.res_w.setRange(64, 7680); self.res_w.setValue(1920); self.res_w.setSingleStep(2)
        self.res_h = QSpinBox(); self.res_h.setRange(64, 4320); self.res_h.setValue(1080); self.res_h.setSingleStep(2)
        res_form.addRow("Preset", self.res_preset)
        res_form.addRow("Width", self.res_w)
        res_form.addRow("Height", self.res_h)
        outer.addWidget(res_box)

        self.res_preset.currentIndexChanged.connect(self._on_preset_changed)
        for w in (self.type, self.fit):
            w.currentTextChanged.connect(lambda *_: self.settings_changed.emit())
        for w in (self.res_w, self.res_h):
            w.valueChanged.connect(lambda *_: self.settings_changed.emit())
        self.path.textChanged.connect(lambda *_: self.settings_changed.emit())

        self._gradient = ["#0f1116", "#1f2233"]
        self._refresh_color_buttons()

    # ---------------------------------------------------------- API

    def to_background(self) -> BackgroundSpec:
        return BackgroundSpec(
            type=self.type.currentText(),
            color=self.color_btn.text(),
            gradient=list(self._gradient),
            path=self.path.text() or None,
            fit_mode=self.fit.currentText(),
        )

    def to_resolution(self) -> Tuple[int, int]:
        w = int(self.res_w.value())
        h = int(self.res_h.value())
        if w % 2:
            w += 1
        if h % 2:
            h += 1
        return w, h

    def load_dict(self, data: dict) -> None:
        if not data:
            return
        if data.get("type"):
            self.type.setCurrentText(str(data["type"]))
        if data.get("color"):
            self.color_btn.setText(str(data["color"]))
            self._refresh_color_buttons()
        if data.get("gradient"):
            grad = list(data["gradient"])
            if len(grad) >= 2:
                self._gradient = [str(grad[0]), str(grad[1])]
                self._refresh_color_buttons()
        if data.get("path"):
            self.path.setText(str(data["path"]))
        if data.get("fit_mode"):
            self.fit.setCurrentText(str(data["fit_mode"]))

    # ---------------------------------------------------------- internals

    def _on_preset_changed(self, idx: int) -> None:
        if 0 <= idx < len(_RESOLUTION_PRESETS):
            label, (w, h) = _RESOLUTION_PRESETS[idx]
            if w and h:
                self.res_w.setValue(w)
                self.res_h.setValue(h)
        self.settings_changed.emit()

    def _on_browse(self) -> None:
        if self.type.currentText() == "video":
            filt = "Video files (*.mp4 *.mov *.webm *.mkv);;All files (*.*)"
        else:
            filt = "Image files (*.jpg *.jpeg *.png *.bmp *.webp);;All files (*.*)"
        path, _ = QFileDialog.getOpenFileName(self, "Select background", "", filt)
        if path:
            self.path.setText(path)

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(QColor(self.color_btn.text()), self, "Background color")
        if color.isValid():
            self.color_btn.setText(color.name())
            self._refresh_color_buttons()
            self.settings_changed.emit()

    def _pick_gradient(self, slot: int) -> None:
        color = QColorDialog.getColor(QColor(self._gradient[slot]), self, "Gradient stop")
        if color.isValid():
            self._gradient[slot] = color.name()
            self._refresh_color_buttons()
            self.settings_changed.emit()

    def _refresh_color_buttons(self) -> None:
        self.color_btn.setStyleSheet(f"background-color: {self.color_btn.text()}; color: #ffffff;")
        self.gradient_a.setText(self._gradient[0])
        self.gradient_b.setText(self._gradient[1])
        self.gradient_a.setStyleSheet(f"background-color: {self._gradient[0]}; color: #ffffff;")
        self.gradient_b.setStyleSheet(f"background-color: {self._gradient[1]}; color: #ffffff;")
