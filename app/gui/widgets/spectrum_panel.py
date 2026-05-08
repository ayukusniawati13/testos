"""Spectrum styling controls — style, colours, position, effects."""
from __future__ import annotations

from typing import Dict

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.spectrum_engine import (
    SUPPORTED_COLOR_MODES,
    SUPPORTED_STYLES,
    SpectrumConfig,
    SpectrumEffects,
    list_color_modes,
    list_styles,
)


class _ColorButton(QPushButton):
    color_changed = Signal(str)

    def __init__(self, hex_value: str = "#7c5cff", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._hex = hex_value
        self.setMinimumWidth(70)
        self.setCursor(self.cursor())
        self.clicked.connect(self._pick)
        self._refresh()

    def _refresh(self) -> None:
        self.setText(self._hex)
        self.setStyleSheet(
            f"background-color: {self._hex}; color: #ffffff; border: 1px solid #2a2f3e;"
        )

    def _pick(self) -> None:
        color = QColorDialog.getColor(QColor(self._hex), self, "Select color")
        if color.isValid():
            self._hex = color.name()
            self._refresh()
            self.color_changed.emit(self._hex)

    def value(self) -> str:
        return self._hex

    def set_value(self, hex_value: str) -> None:
        self._hex = hex_value
        self._refresh()


class SpectrumPanel(QGroupBox):
    settings_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("3. Audio Spectrum", parent)
        outer = QVBoxLayout(self)

        # Style + colours
        top = QFormLayout()
        self.style = QComboBox()
        self.style.addItems(list_styles())
        self.color_mode = QComboBox()
        self.color_mode.addItems(list_color_modes())
        self.primary = _ColorButton("#7c5cff")
        self.secondary = _ColorButton("#21d4fd")
        self.bar_count = QSpinBox()
        self.bar_count.setRange(8, 256)
        self.bar_count.setValue(64)
        self.smoothing = QDoubleSpinBox()
        self.smoothing.setRange(0.0, 0.95)
        self.smoothing.setSingleStep(0.05)
        self.smoothing.setValue(0.6)

        top.addRow("Style", self.style)
        top.addRow("Color mode", self.color_mode)
        top.addRow("Primary color", self.primary)
        top.addRow("Secondary color", self.secondary)
        top.addRow("Bar count", self.bar_count)
        top.addRow("Smoothing", self.smoothing)
        outer.addLayout(top)

        # Position
        pos_box = QGroupBox("Position")
        pos_grid = QGridLayout(pos_box)
        self.x = QDoubleSpinBox(); self.x.setRange(0, 1); self.x.setSingleStep(0.05); self.x.setValue(0.5)
        self.y = QDoubleSpinBox(); self.y.setRange(0, 1); self.y.setSingleStep(0.05); self.y.setValue(0.85)
        self.scale = QDoubleSpinBox(); self.scale.setRange(0.1, 5.0); self.scale.setSingleStep(0.05); self.scale.setValue(1.0)
        self.rotation = QDoubleSpinBox(); self.rotation.setRange(-180, 180); self.rotation.setSingleStep(5.0)
        self.opacity = QDoubleSpinBox(); self.opacity.setRange(0, 1); self.opacity.setSingleStep(0.05); self.opacity.setValue(1.0)
        self.anchor = QComboBox()
        self.anchor.addItems([
            "top_left", "top", "top_right",
            "left", "center", "right",
            "bottom_left", "bottom", "bottom_right",
        ])
        self.anchor.setCurrentText("center")
        for row, (label, w) in enumerate([
            ("X", self.x), ("Y", self.y), ("Scale", self.scale),
            ("Rotation", self.rotation), ("Opacity", self.opacity), ("Anchor", self.anchor),
        ]):
            pos_grid.addWidget(QLabel(label), row // 3, (row % 3) * 2)
            pos_grid.addWidget(w, row // 3, (row % 3) * 2 + 1)
        outer.addWidget(pos_box)

        # Effects
        fx_box = QGroupBox("Effects")
        fx_layout = QHBoxLayout(fx_box)
        self.fx_glow = QCheckBox("Glow"); self.fx_glow.setChecked(True)
        self.fx_blur = QCheckBox("Blur")
        self.fx_shadow = QCheckBox("Shadow"); self.fx_shadow.setChecked(True)
        self.fx_pulse = QCheckBox("Pulse beat"); self.fx_pulse.setChecked(True)
        self.fx_particle = QCheckBox("Particle")
        self.fx_reflection = QCheckBox("Reflection")
        for w in (self.fx_glow, self.fx_blur, self.fx_shadow, self.fx_pulse, self.fx_particle, self.fx_reflection):
            fx_layout.addWidget(w)
        outer.addWidget(fx_box)

        for w in (
            self.style, self.color_mode, self.bar_count, self.smoothing,
            self.x, self.y, self.scale, self.rotation, self.opacity, self.anchor,
            self.fx_glow, self.fx_blur, self.fx_shadow, self.fx_pulse, self.fx_particle, self.fx_reflection,
        ):
            if hasattr(w, "valueChanged"):
                w.valueChanged.connect(self._emit)
            elif hasattr(w, "currentTextChanged"):
                w.currentTextChanged.connect(self._emit)
            elif hasattr(w, "stateChanged"):
                w.stateChanged.connect(self._emit)
        self.primary.color_changed.connect(self._emit)
        self.secondary.color_changed.connect(self._emit)

    # --------------------------------------------------------------- API

    def to_config(self) -> SpectrumConfig:
        return SpectrumConfig(
            style=self.style.currentText(),
            color_mode=self.color_mode.currentText(),
            primary_color=self.primary.value(),
            secondary_color=self.secondary.value(),
            bar_count=int(self.bar_count.value()),
            smoothing=float(self.smoothing.value()),
            x=float(self.x.value()),
            y=float(self.y.value()),
            scale=float(self.scale.value()),
            rotation=float(self.rotation.value()),
            opacity=float(self.opacity.value()),
            anchor=self.anchor.currentText(),
            effects=SpectrumEffects(
                glow=self.fx_glow.isChecked(),
                blur=self.fx_blur.isChecked(),
                shadow=self.fx_shadow.isChecked(),
                pulse=self.fx_pulse.isChecked(),
                particle=self.fx_particle.isChecked(),
                reflection=self.fx_reflection.isChecked(),
            ),
        )

    def load_dict(self, data: Dict) -> None:
        if not data:
            return
        if data.get("style") in SUPPORTED_STYLES:
            self.style.setCurrentText(data["style"])
        if data.get("color_mode") in SUPPORTED_COLOR_MODES:
            self.color_mode.setCurrentText(data["color_mode"])
        if data.get("primary_color"):
            self.primary.set_value(data["primary_color"])
        if data.get("secondary_color"):
            self.secondary.set_value(data["secondary_color"])
        if "bar_count" in data:
            self.bar_count.setValue(int(data["bar_count"]))
        if "smoothing" in data:
            self.smoothing.setValue(float(data["smoothing"]))
        for attr in ("x", "y", "scale", "rotation", "opacity"):
            if attr in data:
                getattr(self, attr).setValue(float(data[attr]))
        if data.get("anchor"):
            self.anchor.setCurrentText(data["anchor"])
        effects = data.get("effects") or {}
        for key, widget in (
            ("glow", self.fx_glow), ("blur", self.fx_blur), ("shadow", self.fx_shadow),
            ("pulse", self.fx_pulse), ("particle", self.fx_particle), ("reflection", self.fx_reflection),
        ):
            if key in effects:
                widget.setChecked(bool(effects[key]))

    # --------------------------------------------------------------- internal

    def _emit(self, *_args) -> None:
        self.settings_changed.emit(self.to_config().__dict__)
