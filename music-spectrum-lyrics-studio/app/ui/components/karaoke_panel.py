"""
Karaoke settings panel - mode selection, style, sync controls.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QGridLayout, QColorDialog, QSlider
)
from PyQt6.QtCore import pyqtSignal, Qt
from app.core.config import KARAOKE_MODES, KARAOKE_PRESETS, SYNC_ACCURACY_MODES


class KaraokePanel(QWidget):
    """Panel for karaoke mode and style settings."""
    settings_changed = pyqtSignal(dict)
    sync_requested = pyqtSignal()
    resync_requested = pyqtSignal()
    shift_requested = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Mode selection
        mode_group = QGroupBox("Karaoke Mode")
        mode_layout = QVBoxLayout()
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(KARAOKE_MODES)
        self.combo_mode.setCurrentText("Karaoke Word Highlight")
        mode_layout.addWidget(self.combo_mode)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Preset
        preset_group = QGroupBox("Karaoke Preset")
        preset_layout = QVBoxLayout()
        self.combo_preset = QComboBox()
        self.combo_preset.addItems(list(KARAOKE_PRESETS.keys()))
        preset_layout.addWidget(self.combo_preset)
        self.btn_apply_preset = QPushButton("Apply Preset")
        preset_layout.addWidget(self.btn_apply_preset)
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        # Font settings
        font_group = QGroupBox("Font & Text")
        font_layout = QGridLayout()

        font_layout.addWidget(QLabel("Font Family:"), 0, 0)
        self.combo_font = QComboBox()
        self.combo_font.addItems(["Arial", "DejaVu Sans", "Roboto", "Impact", "Verdana", "Tahoma"])
        font_layout.addWidget(self.combo_font, 0, 1)

        font_layout.addWidget(QLabel("Font Size:"), 1, 0)
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(12, 120)
        self.spin_font_size.setValue(42)
        font_layout.addWidget(self.spin_font_size, 1, 1)

        font_layout.addWidget(QLabel("Outline Thickness:"), 2, 0)
        self.spin_outline = QSpinBox()
        self.spin_outline.setRange(0, 10)
        self.spin_outline.setValue(2)
        font_layout.addWidget(self.spin_outline, 2, 1)

        font_layout.addWidget(QLabel("Line Spacing:"), 3, 0)
        self.spin_line_spacing = QDoubleSpinBox()
        self.spin_line_spacing.setRange(1.0, 3.0)
        self.spin_line_spacing.setValue(1.4)
        self.spin_line_spacing.setSingleStep(0.1)
        font_layout.addWidget(self.spin_line_spacing, 3, 1)

        font_layout.addWidget(QLabel("Transition Speed:"), 4, 0)
        self.spin_transition = QDoubleSpinBox()
        self.spin_transition.setRange(0.05, 2.0)
        self.spin_transition.setValue(0.3)
        self.spin_transition.setSingleStep(0.05)
        font_layout.addWidget(self.spin_transition, 4, 1)

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        # Colors
        color_group = QGroupBox("Colors")
        color_layout = QHBoxLayout()

        self.btn_normal_color = QPushButton("Normal Color")
        self.btn_normal_color.clicked.connect(lambda: self._pick_color("normal"))
        color_layout.addWidget(self.btn_normal_color)

        self.btn_highlight_color = QPushButton("Highlight Color")
        self.btn_highlight_color.clicked.connect(lambda: self._pick_color("highlight"))
        color_layout.addWidget(self.btn_highlight_color)

        self.btn_outline_color = QPushButton("Outline Color")
        self.btn_outline_color.clicked.connect(lambda: self._pick_color("outline"))
        color_layout.addWidget(self.btn_outline_color)

        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        # Effects
        fx_group = QGroupBox("Effects")
        fx_layout = QVBoxLayout()

        self.chk_glow = QCheckBox("Glow Effect")
        fx_layout.addWidget(self.chk_glow)

        glow_layout = QHBoxLayout()
        glow_layout.addWidget(QLabel("Glow Intensity:"))
        self.spin_glow_intensity = QDoubleSpinBox()
        self.spin_glow_intensity.setRange(0.0, 2.0)
        self.spin_glow_intensity.setValue(0.5)
        self.spin_glow_intensity.setSingleStep(0.1)
        glow_layout.addWidget(self.spin_glow_intensity)
        fx_layout.addLayout(glow_layout)

        self.combo_text_anim = QComboBox()
        self.combo_text_anim.addItems(["Fade", "Slide", "Pop", "Zoom"])
        fx_layout.addWidget(QLabel("Text Animation:"))
        fx_layout.addWidget(self.combo_text_anim)

        fx_group.setLayout(fx_layout)
        layout.addWidget(fx_group)

        # Lyrics Position
        pos_group = QGroupBox("Lyrics Position")
        pos_layout = QGridLayout()

        pos_layout.addWidget(QLabel("Position:"), 0, 0)
        self.combo_lyrics_pos = QComboBox()
        self.combo_lyrics_pos.addItems([
            "Above Spectrum", "Bottom", "Top", "Center", "Custom"
        ])
        pos_layout.addWidget(self.combo_lyrics_pos, 0, 1)

        pos_layout.addWidget(QLabel("Custom X:"), 1, 0)
        self.spin_lyrics_x = QDoubleSpinBox()
        self.spin_lyrics_x.setRange(0.0, 1.0)
        self.spin_lyrics_x.setValue(0.5)
        self.spin_lyrics_x.setSingleStep(0.05)
        pos_layout.addWidget(self.spin_lyrics_x, 1, 1)

        pos_layout.addWidget(QLabel("Custom Y:"), 2, 0)
        self.spin_lyrics_y = QDoubleSpinBox()
        self.spin_lyrics_y.setRange(0.0, 1.0)
        self.spin_lyrics_y.setValue(0.75)
        self.spin_lyrics_y.setSingleStep(0.05)
        pos_layout.addWidget(self.spin_lyrics_y, 2, 1)

        pos_group.setLayout(pos_layout)
        layout.addWidget(pos_group)

        # Sync controls
        sync_group = QGroupBox("Lyrics Sync")
        sync_layout = QVBoxLayout()

        self.combo_sync_mode = QComboBox()
        self.combo_sync_mode.addItems(SYNC_ACCURACY_MODES)
        self.combo_sync_mode.setCurrentText("Balanced Sync")
        sync_layout.addWidget(QLabel("Sync Accuracy:"))
        sync_layout.addWidget(self.combo_sync_mode)

        self.lbl_sync_quality = QLabel("Sync Quality: -")
        sync_layout.addWidget(self.lbl_sync_quality)

        btn_sync_layout = QHBoxLayout()
        self.btn_sync = QPushButton("Sync Lyrics")
        btn_sync_layout.addWidget(self.btn_sync)
        self.btn_resync = QPushButton("Re-Sync")
        btn_sync_layout.addWidget(self.btn_resync)
        sync_layout.addLayout(btn_sync_layout)

        shift_layout = QHBoxLayout()
        self.btn_shift_earlier = QPushButton("Shift Earlier (-0.1s)")
        self.btn_shift_earlier.clicked.connect(lambda: self.shift_requested.emit(-0.1))
        shift_layout.addWidget(self.btn_shift_earlier)

        self.btn_shift_later = QPushButton("Shift Later (+0.1s)")
        self.btn_shift_later.clicked.connect(lambda: self.shift_requested.emit(0.1))
        shift_layout.addWidget(self.btn_shift_later)
        sync_layout.addLayout(shift_layout)

        self.btn_reset_sync = QPushButton("Reset Sync")
        sync_layout.addWidget(self.btn_reset_sync)

        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)

        layout.addStretch()

        self._colors = {
            "normal": "#888888",
            "highlight": "#ffffff",
            "outline": "#000000",
        }

    def _connect_signals(self):
        self.btn_apply_preset.clicked.connect(self._apply_preset)
        self.btn_sync.clicked.connect(self.sync_requested.emit)
        self.btn_resync.clicked.connect(self.resync_requested.emit)
        self.combo_lyrics_pos.currentTextChanged.connect(self._on_pos_changed)

    def _apply_preset(self):
        name = self.combo_preset.currentText()
        preset = KARAOKE_PRESETS.get(name, {})
        if preset:
            if "mode" in preset:
                self.combo_mode.setCurrentText(preset["mode"])
            if "font_size" in preset:
                self.spin_font_size.setValue(preset["font_size"])
            if "outline_thickness" in preset:
                self.spin_outline.setValue(preset["outline_thickness"])
            if "glow_effect" in preset:
                self.chk_glow.setChecked(preset["glow_effect"])
            if "glow_intensity" in preset:
                self.spin_glow_intensity.setValue(preset["glow_intensity"])
            if "transition_speed" in preset:
                self.spin_transition.setValue(preset["transition_speed"])
            if "normal_color" in preset:
                self._colors["normal"] = preset["normal_color"]
            if "highlight_color" in preset:
                self._colors["highlight"] = preset["highlight_color"]
            if "outline_color" in preset:
                self._colors["outline"] = preset["outline_color"]
            self.settings_changed.emit(self.get_settings())

    def _on_pos_changed(self, text):
        positions = {
            "Above Spectrum": (0.5, 0.7),
            "Bottom": (0.5, 0.9),
            "Top": (0.5, 0.15),
            "Center": (0.5, 0.5),
        }
        if text in positions:
            self.spin_lyrics_x.setValue(positions[text][0])
            self.spin_lyrics_y.setValue(positions[text][1])

    def _pick_color(self, which):
        color = QColorDialog.getColor()
        if color.isValid():
            self._colors[which] = color.name()

    def update_sync_quality(self, quality, detail):
        self.lbl_sync_quality.setText(f"Sync Quality: {quality} - {detail}")

    def get_settings(self):
        return {
            "mode": self.combo_mode.currentText(),
            "preset": self.combo_preset.currentText(),
            "font_family": self.combo_font.currentText(),
            "font_size": self.spin_font_size.value(),
            "outline_thickness": self.spin_outline.value(),
            "line_spacing": self.spin_line_spacing.value(),
            "transition_speed": self.spin_transition.value(),
            "normal_color": self._colors["normal"],
            "highlight_color": self._colors["highlight"],
            "outline_color": self._colors["outline"],
            "glow_effect": self.chk_glow.isChecked(),
            "glow_intensity": self.spin_glow_intensity.value(),
            "text_animation": self.combo_text_anim.currentText(),
            "lyrics_position_x": self.spin_lyrics_x.value(),
            "lyrics_position_y": self.spin_lyrics_y.value(),
            "sync_accuracy": self.combo_sync_mode.currentText(),
        }
