"""Logo overlay controls."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
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

from app.core.render_engine import LogoSpec


class LogoPanel(QGroupBox):
    settings_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("5. Logo (optional)", parent)
        outer = QVBoxLayout(self)

        self.enabled = QCheckBox("Enable logo overlay")
        outer.addWidget(self.enabled)

        form = QFormLayout()
        self.path = QLineEdit()
        self.path.setPlaceholderText("Path to PNG / JPG logo")
        browse = QPushButton("Browse")
        browse.clicked.connect(self._on_browse)
        path_row = QHBoxLayout()
        path_row.addWidget(self.path, 1)
        path_row.addWidget(browse)
        path_widget = QWidget(); path_widget.setLayout(path_row)

        self.position = QComboBox()
        self.position.addItems(["top_left", "top_right", "bottom_left", "bottom_right", "custom"])
        self.position.setCurrentText("bottom_right")

        self.x = QDoubleSpinBox(); self.x.setRange(0, 1); self.x.setSingleStep(0.05); self.x.setValue(0.95)
        self.y = QDoubleSpinBox(); self.y.setRange(0, 1); self.y.setSingleStep(0.05); self.y.setValue(0.95)
        self.size = QDoubleSpinBox(); self.size.setRange(0.01, 1.0); self.size.setSingleStep(0.01); self.size.setValue(0.12)
        self.opacity = QDoubleSpinBox(); self.opacity.setRange(0, 1); self.opacity.setSingleStep(0.05); self.opacity.setValue(0.85)
        self.margin = QSpinBox(); self.margin.setRange(0, 500); self.margin.setValue(24)
        self.fade_in = QDoubleSpinBox(); self.fade_in.setRange(0, 5); self.fade_in.setSingleStep(0.1); self.fade_in.setValue(0.5)
        self.fade_out = QDoubleSpinBox(); self.fade_out.setRange(0, 5); self.fade_out.setSingleStep(0.1); self.fade_out.setValue(0.5)

        form.addRow("Path", path_widget)
        form.addRow("Position", self.position)
        form.addRow("Custom X", self.x)
        form.addRow("Custom Y", self.y)
        form.addRow("Size (ratio)", self.size)
        form.addRow("Opacity", self.opacity)
        form.addRow("Margin (px)", self.margin)
        form.addRow("Fade in (s)", self.fade_in)
        form.addRow("Fade out (s)", self.fade_out)
        outer.addLayout(form)

        for w in (
            self.enabled, self.path, self.position,
            self.x, self.y, self.size, self.opacity, self.margin,
            self.fade_in, self.fade_out,
        ):
            if hasattr(w, "valueChanged"):
                w.valueChanged.connect(lambda *_: self.settings_changed.emit())
            elif hasattr(w, "currentTextChanged"):
                w.currentTextChanged.connect(lambda *_: self.settings_changed.emit())
            elif hasattr(w, "stateChanged"):
                w.stateChanged.connect(lambda *_: self.settings_changed.emit())
            elif hasattr(w, "textChanged"):
                w.textChanged.connect(lambda *_: self.settings_changed.emit())

    def to_spec(self) -> LogoSpec:
        return LogoSpec(
            enabled=self.enabled.isChecked(),
            path=self.path.text() or None,
            position=self.position.currentText(),
            x=float(self.x.value()),
            y=float(self.y.value()),
            size=float(self.size.value()),
            opacity=float(self.opacity.value()),
            margin=int(self.margin.value()),
            fade_in=float(self.fade_in.value()),
            fade_out=float(self.fade_out.value()),
        )

    def load_dict(self, data: dict) -> None:
        if not data:
            return
        self.enabled.setChecked(bool(data.get("enabled", False)))
        if data.get("path"):
            self.path.setText(str(data["path"]))
        if data.get("position"):
            self.position.setCurrentText(str(data["position"]))
        for attr in ("x", "y", "size", "opacity", "fade_in", "fade_out"):
            if attr in data:
                getattr(self, attr).setValue(float(data[attr]))
        if "margin" in data:
            self.margin.setValue(int(data["margin"]))

    def _on_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select logo", "",
            "Image files (*.png *.jpg *.jpeg *.webp);;All files (*.*)",
        )
        if path:
            self.path.setText(path)
