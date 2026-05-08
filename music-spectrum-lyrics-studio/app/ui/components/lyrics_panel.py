"""
Lyrics management panel - Whisper model settings, lyrics editor.
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QCheckBox, QTextEdit, QGridLayout,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import pyqtSignal
from app.core.config import WHISPER_MODELS


class LyricsPanel(QWidget):
    """Panel for lyrics generation and editing."""
    generate_requested = pyqtSignal()
    model_download_requested = pyqtSignal(str)
    lyrics_edited = pyqtSignal(str)
    import_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Whisper model settings
        model_group = QGroupBox("AI Model Settings")
        model_layout = QGridLayout()

        model_layout.addWidget(QLabel("Model:"), 0, 0)
        self.combo_model = QComboBox()
        self.combo_model.addItems(WHISPER_MODELS)
        model_layout.addWidget(self.combo_model, 0, 1)

        model_layout.addWidget(QLabel("Language:"), 1, 0)
        self.combo_language = QComboBox()
        self.combo_language.addItems([
            "Auto Detect", "English", "Indonesian", "Japanese",
            "Korean", "Chinese", "Spanish", "French", "German",
            "Portuguese", "Russian", "Arabic", "Hindi", "Thai",
            "Vietnamese", "Turkish", "Italian", "Dutch", "Polish",
        ])
        model_layout.addWidget(self.combo_language, 1, 1)

        model_layout.addWidget(QLabel("Device:"), 2, 0)
        self.combo_device = QComboBox()
        self.combo_device.addItems(["Auto", "CPU", "GPU (CUDA)"])
        model_layout.addWidget(self.combo_device, 2, 1)

        model_layout.addWidget(QLabel("Compute Type:"), 3, 0)
        self.combo_compute = QComboBox()
        self.combo_compute.addItems(["Auto", "float16", "int8"])
        model_layout.addWidget(self.combo_compute, 3, 1)

        self.chk_word_timestamp = QCheckBox("Word-level Timestamp")
        self.chk_word_timestamp.setChecked(True)
        model_layout.addWidget(self.chk_word_timestamp, 4, 0, 1, 2)

        self.chk_forced_alignment = QCheckBox("Forced Alignment (WhisperX)")
        self.chk_forced_alignment.setChecked(True)
        model_layout.addWidget(self.chk_forced_alignment, 5, 0, 1, 2)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # Model management
        mgmt_group = QGroupBox("Model Management")
        mgmt_layout = QVBoxLayout()

        self.lbl_model_status = QLabel("Model Status: Not checked")
        mgmt_layout.addWidget(self.lbl_model_status)

        btn_layout = QHBoxLayout()
        self.btn_download = QPushButton("Download/Prepare Model")
        self.btn_download.clicked.connect(self._download_model)
        btn_layout.addWidget(self.btn_download)

        self.btn_check = QPushButton("Check Status")
        btn_layout.addWidget(self.btn_check)

        self.btn_clear_cache = QPushButton("Clear Cache")
        btn_layout.addWidget(self.btn_clear_cache)
        mgmt_layout.addLayout(btn_layout)

        mgmt_group.setLayout(mgmt_layout)
        layout.addWidget(mgmt_group)

        # Generate / Import
        gen_group = QGroupBox("Lyrics Generation")
        gen_layout = QVBoxLayout()

        self.lbl_source = QLabel("Source: None")
        gen_layout.addWidget(self.lbl_source)

        btn_gen_layout = QHBoxLayout()
        self.btn_generate = QPushButton("Generate Lyrics (AI)")
        self.btn_generate.setObjectName("primaryButton")
        self.btn_generate.clicked.connect(self.generate_requested.emit)
        btn_gen_layout.addWidget(self.btn_generate)

        self.btn_import = QPushButton("Import .lrc/.srt/.ass")
        self.btn_import.clicked.connect(self._import_lyrics)
        btn_gen_layout.addWidget(self.btn_import)
        gen_layout.addLayout(btn_gen_layout)

        gen_group.setLayout(gen_layout)
        layout.addWidget(gen_group)

        # Lyrics editor
        edit_group = QGroupBox("Lyrics Editor (Manual)")
        edit_layout = QVBoxLayout()

        self.txt_lyrics = QTextEdit()
        self.txt_lyrics.setPlaceholderText(
            "Lyrics will appear here after generation.\n"
            "You can also paste lyrics manually.\n"
            "Format: [MM:SS.ss]Lyrics text"
        )
        self.txt_lyrics.setMinimumHeight(150)
        edit_layout.addWidget(self.txt_lyrics)

        btn_edit_layout = QHBoxLayout()
        self.btn_apply_manual = QPushButton("Apply Manual Lyrics")
        self.btn_apply_manual.clicked.connect(
            lambda: self.lyrics_edited.emit(self.txt_lyrics.toPlainText())
        )
        btn_edit_layout.addWidget(self.btn_apply_manual)

        self.btn_export_lrc = QPushButton("Export .lrc")
        btn_edit_layout.addWidget(self.btn_export_lrc)

        self.btn_export_srt = QPushButton("Export .srt")
        btn_edit_layout.addWidget(self.btn_export_srt)
        edit_layout.addLayout(btn_edit_layout)

        edit_group.setLayout(edit_layout)
        layout.addWidget(edit_group)

        layout.addStretch()

    def _download_model(self):
        model = self.combo_model.currentText()
        self.model_download_requested.emit(model)

    def _import_lyrics(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Lyrics File", "",
            "Lyrics Files (*.lrc *.srt *.ass);;All Files (*)"
        )
        if path:
            self.import_requested.emit(path)

    def update_source(self, source):
        self.lbl_source.setText(f"Source: {source}")

    def update_model_status(self, status):
        self.lbl_model_status.setText(f"Model Status: {status}")

    def set_lyrics_text(self, text):
        self.txt_lyrics.setPlainText(text)

    def get_settings(self):
        lang_map = {
            "Auto Detect": "auto", "English": "en", "Indonesian": "id",
            "Japanese": "ja", "Korean": "ko", "Chinese": "zh",
            "Spanish": "es", "French": "fr", "German": "de",
            "Portuguese": "pt", "Russian": "ru", "Arabic": "ar",
            "Hindi": "hi", "Thai": "th", "Vietnamese": "vi",
            "Turkish": "tr", "Italian": "it", "Dutch": "nl", "Polish": "pl",
        }
        device_map = {"Auto": "auto", "CPU": "cpu", "GPU (CUDA)": "cuda"}
        compute_map = {"Auto": "auto", "float16": "float16", "int8": "int8"}

        return {
            "model": self.combo_model.currentText(),
            "language": lang_map.get(self.combo_language.currentText(), "auto"),
            "device": device_map.get(self.combo_device.currentText(), "auto"),
            "compute_type": compute_map.get(self.combo_compute.currentText(), "auto"),
            "word_timestamp": self.chk_word_timestamp.isChecked(),
            "forced_alignment": self.chk_forced_alignment.isChecked(),
        }
