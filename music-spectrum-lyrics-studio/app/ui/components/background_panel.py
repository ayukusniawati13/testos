"""
Background selection panel.
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QGroupBox, QComboBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
from app.core.config import BG_FILTER, SUPPORTED_IMAGE_BG


class BackgroundPanel(QWidget):
    """Panel for background file selection."""
    background_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bg_path = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        bg_group = QGroupBox("Background")
        bg_layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        self.btn_select = QPushButton("Select Background")
        self.btn_select.clicked.connect(self._select_file)
        btn_layout.addWidget(self.btn_select)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self._clear)
        btn_layout.addWidget(self.btn_clear)
        bg_layout.addLayout(btn_layout)

        self.lbl_file = QLabel("No background selected (default dark will be used)")
        self.lbl_file.setObjectName("statusLabel")
        self.lbl_file.setWordWrap(True)
        bg_layout.addWidget(self.lbl_file)

        self.lbl_type = QLabel("")
        self.lbl_type.setObjectName("statusLabel")
        bg_layout.addWidget(self.lbl_type)

        bg_group.setLayout(bg_layout)
        layout.addWidget(bg_group)

        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        self.preview_label = QLabel("No preview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(150)
        preview_layout.addWidget(self.preview_label)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Info
        info_group = QGroupBox("Info")
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel("Supported formats:"))
        info_layout.addWidget(QLabel("Images: JPG, JPEG, PNG, WEBP"))
        info_layout.addWidget(QLabel("Videos: MP4, MOV, WEBM, AVI"))
        info_layout.addWidget(QLabel(""))
        info_layout.addWidget(QLabel("Image backgrounds will be extended to match audio duration."))
        info_layout.addWidget(QLabel("Video backgrounds will be looped/trimmed to match audio."))
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        layout.addStretch()

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Background", "", BG_FILTER
        )
        if path:
            self.bg_path = path
            self.lbl_file.setText(os.path.basename(path))
            ext = os.path.splitext(path)[1].lower()
            if ext in SUPPORTED_IMAGE_BG:
                self.lbl_type.setText("Type: Image")
                self._show_image_preview(path)
            else:
                self.lbl_type.setText("Type: Video")
                self.preview_label.setText("Video background selected")
            self.background_selected.emit(path)

    def _clear(self):
        self.bg_path = ""
        self.lbl_file.setText("No background selected")
        self.lbl_type.setText("")
        self.preview_label.setText("No preview")
        self.preview_label.setPixmap(QPixmap())

    def _show_image_preview(self, path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.preview_label.setPixmap(
                pixmap.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
            )

    def get_background_path(self):
        return self.bg_path
