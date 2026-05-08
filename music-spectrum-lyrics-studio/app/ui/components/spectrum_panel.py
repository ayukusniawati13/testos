"""
Audio spectrum settings panel.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QSlider, QGridLayout, QColorDialog
)
from PyQt6.QtCore import pyqtSignal, Qt
from app.core.config import SPECTRUM_STYLES, SPECTRUM_PRESETS, POSITION_PRESETS


class SpectrumPanel(QWidget):
    """Panel for spectrum visualization settings."""
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Style selection
        style_group = QGroupBox("Spectrum Style")
        style_layout = QVBoxLayout()
        self.combo_style = QComboBox()
        self.combo_style.addItems(SPECTRUM_STYLES)
        style_layout.addWidget(self.combo_style)
        style_group.setLayout(style_layout)
        layout.addWidget(style_group)

        # Preset selection
        preset_group = QGroupBox("Spectrum Preset")
        preset_layout = QVBoxLayout()
        self.combo_preset = QComboBox()
        self.combo_preset.addItems(list(SPECTRUM_PRESETS.keys()))
        preset_layout.addWidget(self.combo_preset)

        self.btn_apply_preset = QPushButton("Apply Preset")
        preset_layout.addWidget(self.btn_apply_preset)
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        # Bar settings
        bar_group = QGroupBox("Bar Settings")
        bar_layout = QGridLayout()

        bar_layout.addWidget(QLabel("Bar Count:"), 0, 0)
        self.spin_bar_count = QSpinBox()
        self.spin_bar_count.setRange(8, 256)
        self.spin_bar_count.setValue(64)
        bar_layout.addWidget(self.spin_bar_count, 0, 1)

        bar_layout.addWidget(QLabel("Bar Width:"), 1, 0)
        self.spin_bar_width = QSpinBox()
        self.spin_bar_width.setRange(2, 30)
        self.spin_bar_width.setValue(8)
        bar_layout.addWidget(self.spin_bar_width, 1, 1)

        bar_layout.addWidget(QLabel("Bar Spacing:"), 2, 0)
        self.spin_bar_spacing = QSpinBox()
        self.spin_bar_spacing.setRange(0, 20)
        self.spin_bar_spacing.setValue(3)
        bar_layout.addWidget(self.spin_bar_spacing, 2, 1)

        bar_layout.addWidget(QLabel("Max Height:"), 3, 0)
        self.spin_max_height = QSpinBox()
        self.spin_max_height.setRange(50, 500)
        self.spin_max_height.setValue(200)
        bar_layout.addWidget(self.spin_max_height, 3, 1)

        bar_group.setLayout(bar_layout)
        layout.addWidget(bar_group)

        # Audio reaction
        react_group = QGroupBox("Audio Reaction")
        react_layout = QGridLayout()

        react_layout.addWidget(QLabel("Sensitivity:"), 0, 0)
        self.spin_sensitivity = QDoubleSpinBox()
        self.spin_sensitivity.setRange(0.1, 5.0)
        self.spin_sensitivity.setValue(1.0)
        self.spin_sensitivity.setSingleStep(0.1)
        react_layout.addWidget(self.spin_sensitivity, 0, 1)

        react_layout.addWidget(QLabel("Bass Boost:"), 1, 0)
        self.spin_bass_boost = QDoubleSpinBox()
        self.spin_bass_boost.setRange(0.5, 5.0)
        self.spin_bass_boost.setValue(1.2)
        self.spin_bass_boost.setSingleStep(0.1)
        react_layout.addWidget(self.spin_bass_boost, 1, 1)

        react_layout.addWidget(QLabel("Treble Reaction:"), 2, 0)
        self.spin_treble = QDoubleSpinBox()
        self.spin_treble.setRange(0.1, 3.0)
        self.spin_treble.setValue(1.0)
        self.spin_treble.setSingleStep(0.1)
        react_layout.addWidget(self.spin_treble, 2, 1)

        react_group.setLayout(react_layout)
        layout.addWidget(react_group)

        # Visual effects
        fx_group = QGroupBox("Visual Effects")
        fx_layout = QVBoxLayout()

        self.chk_rainbow = QCheckBox("Rainbow Mode")
        fx_layout.addWidget(self.chk_rainbow)

        self.chk_neon = QCheckBox("Neon Mode")
        fx_layout.addWidget(self.chk_neon)

        self.chk_glow = QCheckBox("Glow Effect")
        self.chk_glow.setChecked(True)
        fx_layout.addWidget(self.chk_glow)

        self.chk_rounded = QCheckBox("Rounded Bars")
        self.chk_rounded.setChecked(True)
        fx_layout.addWidget(self.chk_rounded)

        self.chk_bounce = QCheckBox("Beat Bounce Effect")
        self.chk_bounce.setChecked(True)
        fx_layout.addWidget(self.chk_bounce)

        self.chk_reflection = QCheckBox("Reflection (optional)")
        fx_layout.addWidget(self.chk_reflection)

        color_btn_layout = QHBoxLayout()
        self.btn_color1 = QPushButton("Color 1")
        self.btn_color1.clicked.connect(lambda: self._pick_color(0))
        color_btn_layout.addWidget(self.btn_color1)

        self.btn_color2 = QPushButton("Color 2")
        self.btn_color2.clicked.connect(lambda: self._pick_color(1))
        color_btn_layout.addWidget(self.btn_color2)
        fx_layout.addLayout(color_btn_layout)

        fx_group.setLayout(fx_layout)
        layout.addWidget(fx_group)

        # Position
        pos_group = QGroupBox("Spectrum Position")
        pos_layout = QGridLayout()

        pos_layout.addWidget(QLabel("Position:"), 0, 0)
        self.combo_position = QComboBox()
        self.combo_position.addItems(["Bottom", "Top", "Left", "Right", "Center", "Custom"])
        pos_layout.addWidget(self.combo_position, 0, 1)

        pos_layout.addWidget(QLabel("Custom X:"), 1, 0)
        self.spin_pos_x = QDoubleSpinBox()
        self.spin_pos_x.setRange(0.0, 1.0)
        self.spin_pos_x.setValue(0.5)
        self.spin_pos_x.setSingleStep(0.05)
        pos_layout.addWidget(self.spin_pos_x, 1, 1)

        pos_layout.addWidget(QLabel("Custom Y:"), 2, 0)
        self.spin_pos_y = QDoubleSpinBox()
        self.spin_pos_y.setRange(0.0, 1.0)
        self.spin_pos_y.setValue(0.95)
        self.spin_pos_y.setSingleStep(0.05)
        pos_layout.addWidget(self.spin_pos_y, 2, 1)

        pos_group.setLayout(pos_layout)
        layout.addWidget(pos_group)

        layout.addStretch()

        self._gradient_colors = ["#00ffff", "#ff00ff"]

    def _connect_signals(self):
        self.btn_apply_preset.clicked.connect(self._apply_preset)
        self.combo_position.currentTextChanged.connect(self._on_position_changed)

    def _apply_preset(self):
        name = self.combo_preset.currentText()
        preset = SPECTRUM_PRESETS.get(name, {})
        if preset:
            self.spin_bar_count.setValue(preset.get("bar_count", 64))
            self.spin_bar_width.setValue(preset.get("bar_width", 8))
            self.spin_bar_spacing.setValue(preset.get("bar_spacing", 3))
            self.spin_max_height.setValue(preset.get("max_height", 200))
            self.spin_sensitivity.setValue(preset.get("sensitivity", 1.0))
            self.spin_bass_boost.setValue(preset.get("bass_boost", 1.2))
            self.spin_treble.setValue(preset.get("treble_reaction", 1.0))
            self.chk_rainbow.setChecked(preset.get("rainbow_mode", False))
            self.chk_neon.setChecked(preset.get("neon_mode", False))
            self.chk_glow.setChecked(preset.get("glow", True))
            self.chk_rounded.setChecked(preset.get("rounded", True))
            self._gradient_colors = preset.get("gradient_colors", ["#00ffff", "#ff00ff"])
            self.settings_changed.emit(self.get_settings())

    def _on_position_changed(self, pos_text):
        positions = {
            "Bottom": (0.5, 0.95), "Top": (0.5, 0.1),
            "Left": (0.1, 0.5), "Right": (0.9, 0.5),
            "Center": (0.5, 0.5),
        }
        if pos_text in positions:
            self.spin_pos_x.setValue(positions[pos_text][0])
            self.spin_pos_y.setValue(positions[pos_text][1])

    def _pick_color(self, index):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            while len(self._gradient_colors) <= index:
                self._gradient_colors.append("#ffffff")
            self._gradient_colors[index] = hex_color

    def get_settings(self):
        return {
            "style": self.combo_style.currentText(),
            "preset": self.combo_preset.currentText(),
            "bar_count": self.spin_bar_count.value(),
            "bar_width": self.spin_bar_width.value(),
            "bar_spacing": self.spin_bar_spacing.value(),
            "max_height": self.spin_max_height.value(),
            "sensitivity": self.spin_sensitivity.value(),
            "bass_boost": self.spin_bass_boost.value(),
            "treble_reaction": self.spin_treble.value(),
            "rainbow_mode": self.chk_rainbow.isChecked(),
            "neon_mode": self.chk_neon.isChecked(),
            "glow": self.chk_glow.isChecked(),
            "rounded": self.chk_rounded.isChecked(),
            "beat_bounce": self.chk_bounce.isChecked(),
            "reflection": self.chk_reflection.isChecked(),
            "gradient_colors": self._gradient_colors,
            "position_x": self.spin_pos_x.value(),
            "position_y": self.spin_pos_y.value(),
        }
