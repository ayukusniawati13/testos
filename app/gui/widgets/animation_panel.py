"""Animation overlay controls (mp4/mov/webm/gif)."""
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
    QVBoxLayout,
    QWidget,
)

from app.core.render_engine import AnimationOverlaySpec


class AnimationPanel(QGroupBox):
    settings_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("6. Animation overlay (optional)", parent)
        outer = QVBoxLayout(self)

        self.enabled = QCheckBox("Enable animation overlay")
        outer.addWidget(self.enabled)

        form = QFormLayout()
        self.path = QLineEdit()
        self.path.setPlaceholderText("Video / GIF overlay file")
        browse = QPushButton("Browse")
        browse.clicked.connect(self._on_browse)
        path_row = QHBoxLayout()
        path_row.addWidget(self.path, 1)
        path_row.addWidget(browse)
        path_widget = QWidget(); path_widget.setLayout(path_row)

        self.placement = QComboBox()
        self.placement.addItems(["start", "middle", "end", "custom"])
        self.start_at = QDoubleSpinBox(); self.start_at.setRange(0, 3600); self.start_at.setSingleStep(0.5)
        self.duration = QDoubleSpinBox(); self.duration.setRange(0.1, 600); self.duration.setSingleStep(0.5); self.duration.setValue(3.0)
        self.opacity = QDoubleSpinBox(); self.opacity.setRange(0, 1); self.opacity.setSingleStep(0.05); self.opacity.setValue(1.0)
        self.blend = QComboBox(); self.blend.addItems(["normal", "screen", "add"])

        form.addRow("Path", path_widget)
        form.addRow("Placement", self.placement)
        form.addRow("Start at (s)", self.start_at)
        form.addRow("Duration (s)", self.duration)
        form.addRow("Opacity", self.opacity)
        form.addRow("Blend", self.blend)
        outer.addLayout(form)

        for w in (
            self.enabled, self.path, self.placement, self.start_at,
            self.duration, self.opacity, self.blend,
        ):
            if hasattr(w, "valueChanged"):
                w.valueChanged.connect(lambda *_: self.settings_changed.emit())
            elif hasattr(w, "currentTextChanged"):
                w.currentTextChanged.connect(lambda *_: self.settings_changed.emit())
            elif hasattr(w, "stateChanged"):
                w.stateChanged.connect(lambda *_: self.settings_changed.emit())
            elif hasattr(w, "textChanged"):
                w.textChanged.connect(lambda *_: self.settings_changed.emit())

    def to_spec(self) -> AnimationOverlaySpec:
        return AnimationOverlaySpec(
            enabled=self.enabled.isChecked(),
            path=self.path.text() or None,
            placement=self.placement.currentText(),
            start_at=float(self.start_at.value()),
            duration=float(self.duration.value()),
            opacity=float(self.opacity.value()),
            blend=self.blend.currentText(),
        )

    def load_dict(self, data: dict) -> None:
        if not data:
            return
        self.enabled.setChecked(bool(data.get("enabled", False)))
        if data.get("path"):
            self.path.setText(str(data["path"]))
        if data.get("placement"):
            self.placement.setCurrentText(str(data["placement"]))
        for attr in ("start_at", "duration", "opacity"):
            if attr in data:
                getattr(self, attr).setValue(float(data[attr]))
        if data.get("blend"):
            self.blend.setCurrentText(str(data["blend"]))

    def _on_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select animation", "",
            "Animation files (*.mp4 *.mov *.webm *.gif);;All files (*.*)",
        )
        if path:
            self.path.setText(path)
