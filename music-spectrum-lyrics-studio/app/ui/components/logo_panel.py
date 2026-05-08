"""
Logo/watermark settings panel.
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QFileDialog, QGridLayout
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
from app.core.config import LOGO_POSITIONS, LOGO_ANIMATIONS, LOGO_FILTER


class LogoPanel(QWidget):
    """Panel for logo/watermark settings."""
    settings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logo_path = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Enable
        self.chk_enabled = QCheckBox("Enable Logo/Watermark")
        layout.addWidget(self.chk_enabled)

        # File selection
        file_group = QGroupBox("Logo File")
        file_layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        self.btn_select = QPushButton("Select Logo (PNG/JPG)")
        self.btn_select.clicked.connect(self._select_logo)
        btn_layout.addWidget(self.btn_select)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self._clear_logo)
        btn_layout.addWidget(self.btn_clear)
        file_layout.addLayout(btn_layout)

        self.lbl_file = QLabel("No logo selected")
        self.lbl_file.setObjectName("statusLabel")
        file_layout.addWidget(self.lbl_file)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(80)
        file_layout.addWidget(self.preview_label)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Settings
        settings_group = QGroupBox("Logo Settings")
        settings_layout = QGridLayout()

        settings_layout.addWidget(QLabel("Position:"), 0, 0)
        self.combo_position = QComboBox()
        self.combo_position.addItems(LOGO_POSITIONS)
        self.combo_position.setCurrentText("Top Right")
        settings_layout.addWidget(self.combo_position, 0, 1)

        settings_layout.addWidget(QLabel("Size:"), 1, 0)
        self.spin_size = QSpinBox()
        self.spin_size.setRange(20, 500)
        self.spin_size.setValue(100)
        self.spin_size.setSuffix(" px")
        settings_layout.addWidget(self.spin_size, 1, 1)

        settings_layout.addWidget(QLabel("Opacity:"), 2, 0)
        self.spin_opacity = QDoubleSpinBox()
        self.spin_opacity.setRange(0.0, 1.0)
        self.spin_opacity.setValue(0.8)
        self.spin_opacity.setSingleStep(0.05)
        settings_layout.addWidget(self.spin_opacity, 2, 1)

        settings_layout.addWidget(QLabel("Margin:"), 3, 0)
        self.spin_margin = QSpinBox()
        self.spin_margin.setRange(0, 100)
        self.spin_margin.setValue(20)
        self.spin_margin.setSuffix(" px")
        settings_layout.addWidget(self.spin_margin, 3, 1)

        settings_layout.addWidget(QLabel("Animation:"), 4, 0)
        self.combo_animation = QComboBox()
        self.combo_animation.addItems(LOGO_ANIMATIONS)
        settings_layout.addWidget(self.combo_animation, 4, 1)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        layout.addStretch()

    def _select_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo", "", LOGO_FILTER
        )
        if path:
            self.logo_path = path
            self.lbl_file.setText(os.path.basename(path))
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.preview_label.setPixmap(
                    pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
                )

    def _clear_logo(self):
        self.logo_path = ""
        self.lbl_file.setText("No logo selected")
        self.preview_label.clear()

    def get_settings(self):
        return {
            "enabled": self.chk_enabled.isChecked(),
            "path": self.logo_path,
            "position": self.combo_position.currentText(),
            "size": self.spin_size.value(),
            "opacity": self.spin_opacity.value(),
            "margin": self.spin_margin.value(),
            "animation": self.combo_animation.currentText(),
        }
