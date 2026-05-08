"""
CTA (Call to Action) animation panel.
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QFileDialog, QGridLayout, QLineEdit
)
from PyQt6.QtCore import pyqtSignal
from app.core.config import CTA_TYPES, CTA_TIMING, CTA_PRESETS


class CTAPanel(QWidget):
    """Panel for CTA animation settings."""
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.custom_path = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.chk_enabled = QCheckBox("Enable CTA Animation")
        layout.addWidget(self.chk_enabled)

        # Type
        type_group = QGroupBox("CTA Type")
        type_layout = QGridLayout()

        type_layout.addWidget(QLabel("Type:"), 0, 0)
        self.combo_type = QComboBox()
        self.combo_type.addItems(CTA_TYPES)
        type_layout.addWidget(self.combo_type, 0, 1)

        type_layout.addWidget(QLabel("Custom Text:"), 1, 0)
        self.txt_custom = QLineEdit()
        self.txt_custom.setPlaceholderText("Custom CTA text...")
        type_layout.addWidget(self.txt_custom, 1, 1)

        type_group.setLayout(type_layout)
        layout.addWidget(type_group)

        # Timing
        timing_group = QGroupBox("Timing")
        timing_layout = QGridLayout()

        timing_layout.addWidget(QLabel("Show at:"), 0, 0)
        self.combo_timing = QComboBox()
        self.combo_timing.addItems(CTA_TIMING)
        self.combo_timing.setCurrentText("End")
        timing_layout.addWidget(self.combo_timing, 0, 1)

        timing_layout.addWidget(QLabel("Custom Time (s):"), 1, 0)
        self.spin_custom_time = QDoubleSpinBox()
        self.spin_custom_time.setRange(0, 9999)
        self.spin_custom_time.setValue(0)
        timing_layout.addWidget(self.spin_custom_time, 1, 1)

        timing_layout.addWidget(QLabel("Duration (s):"), 2, 0)
        self.spin_duration = QDoubleSpinBox()
        self.spin_duration.setRange(1, 30)
        self.spin_duration.setValue(5)
        timing_layout.addWidget(self.spin_duration, 2, 1)

        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)

        # Preset
        preset_group = QGroupBox("CTA Preset")
        preset_layout = QVBoxLayout()
        self.combo_preset = QComboBox()
        self.combo_preset.addItems(CTA_PRESETS)
        preset_layout.addWidget(self.combo_preset)
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)

        # Custom animation
        custom_group = QGroupBox("Custom CTA Animation")
        custom_layout = QVBoxLayout()

        self.btn_upload = QPushButton("Upload Animation (GIF/WEBM/MP4/MOV/PNG)")
        self.btn_upload.clicked.connect(self._upload_custom)
        custom_layout.addWidget(self.btn_upload)

        self.lbl_custom = QLabel("No custom animation")
        custom_layout.addWidget(self.lbl_custom)

        self.chk_chroma = QCheckBox("Chroma Key (Green Screen Removal)")
        custom_layout.addWidget(self.chk_chroma)

        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)

        # Display settings
        display_group = QGroupBox("Display")
        display_layout = QGridLayout()

        display_layout.addWidget(QLabel("Position:"), 0, 0)
        self.combo_position = QComboBox()
        self.combo_position.addItems(["Top Left", "Top Right", "Bottom Left", "Bottom Right", "Center"])
        self.combo_position.setCurrentText("Bottom Right")
        display_layout.addWidget(self.combo_position, 0, 1)

        display_layout.addWidget(QLabel("Size:"), 1, 0)
        self.spin_size = QSpinBox()
        self.spin_size.setRange(50, 500)
        self.spin_size.setValue(200)
        display_layout.addWidget(self.spin_size, 1, 1)

        display_layout.addWidget(QLabel("Opacity:"), 2, 0)
        self.spin_opacity = QDoubleSpinBox()
        self.spin_opacity.setRange(0.0, 1.0)
        self.spin_opacity.setValue(0.9)
        self.spin_opacity.setSingleStep(0.05)
        display_layout.addWidget(self.spin_opacity, 2, 1)

        self.chk_fade_in = QCheckBox("Fade In")
        self.chk_fade_in.setChecked(True)
        display_layout.addWidget(self.chk_fade_in, 3, 0)

        self.chk_fade_out = QCheckBox("Fade Out")
        self.chk_fade_out.setChecked(True)
        display_layout.addWidget(self.chk_fade_out, 3, 1)

        self.chk_loop = QCheckBox("Loop")
        display_layout.addWidget(self.chk_loop, 4, 0)

        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        layout.addStretch()

    def _upload_custom(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CTA Animation", "",
            "Animation Files (*.gif *.webm *.mp4 *.mov *.png);;All Files (*)"
        )
        if path:
            self.custom_path = path
            self.lbl_custom.setText(os.path.basename(path))

    def get_settings(self):
        return {
            "enabled": self.chk_enabled.isChecked(),
            "type": self.combo_type.currentText(),
            "custom_text": self.txt_custom.text(),
            "timing": self.combo_timing.currentText(),
            "custom_timestamp": self.spin_custom_time.value(),
            "duration": self.spin_duration.value(),
            "preset": self.combo_preset.currentText(),
            "custom_path": self.custom_path,
            "chroma_key": self.chk_chroma.isChecked(),
            "position": self.combo_position.currentText(),
            "size": self.spin_size.value(),
            "opacity": self.spin_opacity.value(),
            "fade_in": self.chk_fade_in.isChecked(),
            "fade_out": self.chk_fade_out.isChecked(),
            "loop": self.chk_loop.isChecked(),
        }
