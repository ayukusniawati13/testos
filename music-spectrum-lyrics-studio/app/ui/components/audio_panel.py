"""
Audio input panel - select music file and view metadata.
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QGroupBox, QGridLayout, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPixmap
from app.core.config import AUDIO_FILTER, SUPPORTED_AUDIO


class AudioPanel(QWidget):
    """Panel for audio file selection and metadata display."""
    audio_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_path = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # File selection
        file_group = QGroupBox("Music File")
        file_layout = QVBoxLayout()

        btn_layout = QHBoxLayout()
        self.btn_select = QPushButton("Select Music File")
        self.btn_select.clicked.connect(self._select_file)
        btn_layout.addWidget(self.btn_select)
        file_layout.addLayout(btn_layout)

        self.lbl_file = QLabel("No file selected")
        self.lbl_file.setObjectName("statusLabel")
        self.lbl_file.setWordWrap(True)
        file_layout.addWidget(self.lbl_file)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # Metadata display
        meta_group = QGroupBox("Audio Metadata")
        meta_layout = QGridLayout()

        labels = ["Title:", "Artist:", "Album:", "Year:", "Genre:", "Duration:", "Lyrics:"]
        self.meta_labels = {}
        for i, label in enumerate(labels):
            meta_layout.addWidget(QLabel(label), i, 0)
            val = QLabel("-")
            val.setWordWrap(True)
            self.meta_labels[label.replace(":", "").lower()] = val
            meta_layout.addWidget(val, i, 1)

        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)

        # Cover art
        cover_group = QGroupBox("Cover Art")
        cover_layout = QVBoxLayout()
        self.cover_label = QLabel("No cover art")
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setMinimumHeight(120)
        cover_layout.addWidget(self.cover_label)
        cover_group.setLayout(cover_layout)
        layout.addWidget(cover_group)

        layout.addStretch()

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Music File", "", AUDIO_FILTER
        )
        if path:
            self.audio_path = path
            self.lbl_file.setText(os.path.basename(path))
            self.audio_selected.emit(path)

    def update_metadata(self, lyrics_data):
        """Update metadata display from LyricsData."""
        if not lyrics_data:
            return
        self.meta_labels["title"].setText(lyrics_data.title or "-")
        self.meta_labels["artist"].setText(lyrics_data.artist or "-")
        self.meta_labels["album"].setText(lyrics_data.album or "-")
        self.meta_labels["year"].setText(lyrics_data.year or "-")
        self.meta_labels["genre"].setText(lyrics_data.genre or "-")
        self.meta_labels["lyrics"].setText(lyrics_data.source or "-")

        if lyrics_data.cover_data:
            pixmap = QPixmap()
            pixmap.loadFromData(lyrics_data.cover_data)
            if not pixmap.isNull():
                self.cover_label.setPixmap(
                    pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
                )

    def update_duration(self, duration):
        from app.utils.helpers import format_time
        self.meta_labels["duration"].setText(format_time(duration))

    def get_audio_path(self):
        return self.audio_path
