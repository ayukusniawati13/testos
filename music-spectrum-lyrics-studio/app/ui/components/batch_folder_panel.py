"""
Batch folder render panel.
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QCheckBox, QFileDialog, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar
)
from PyQt6.QtCore import pyqtSignal, Qt
from app.core.config import BATCH_BG_MODES, DIRS


class BatchFolderPanel(QWidget):
    """Panel for batch folder rendering."""
    batch_start_requested = pyqtSignal()
    batch_cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_folder = ""
        self.bg_folder = ""
        self.output_folder = DIRS["output"]
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Folders
        folder_group = QGroupBox("Folders")
        folder_layout = QGridLayout()

        folder_layout.addWidget(QLabel("Music Folder:"), 0, 0)
        self.lbl_audio = QLabel("Not selected")
        self.lbl_audio.setObjectName("statusLabel")
        folder_layout.addWidget(self.lbl_audio, 0, 1)
        self.btn_audio = QPushButton("Browse")
        self.btn_audio.clicked.connect(self._select_audio_folder)
        folder_layout.addWidget(self.btn_audio, 0, 2)

        folder_layout.addWidget(QLabel("Background Folder:"), 1, 0)
        self.lbl_bg = QLabel("Not selected")
        self.lbl_bg.setObjectName("statusLabel")
        folder_layout.addWidget(self.lbl_bg, 1, 1)
        self.btn_bg = QPushButton("Browse")
        self.btn_bg.clicked.connect(self._select_bg_folder)
        folder_layout.addWidget(self.btn_bg, 1, 2)

        folder_layout.addWidget(QLabel("Output Folder:"), 2, 0)
        self.lbl_output = QLabel(DIRS["output"])
        self.lbl_output.setObjectName("statusLabel")
        folder_layout.addWidget(self.lbl_output, 2, 1)
        self.btn_output = QPushButton("Browse")
        self.btn_output.clicked.connect(self._select_output_folder)
        folder_layout.addWidget(self.btn_output, 2, 2)

        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)

        # Settings
        settings_group = QGroupBox("Batch Settings")
        settings_layout = QVBoxLayout()

        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Background Mode:"))
        self.combo_bg_mode = QComboBox()
        self.combo_bg_mode.addItems(BATCH_BG_MODES)
        bg_layout.addWidget(self.combo_bg_mode)
        settings_layout.addLayout(bg_layout)

        self.chk_auto_lyrics = QCheckBox("Auto Generate Lyrics")
        self.chk_auto_lyrics.setChecked(True)
        settings_layout.addWidget(self.chk_auto_lyrics)

        self.chk_auto_sync = QCheckBox("Auto Sync Lyrics")
        self.chk_auto_sync.setChecked(True)
        settings_layout.addWidget(self.chk_auto_sync)

        self.chk_metadata = QCheckBox("Check Metadata Lyrics First")
        self.chk_metadata.setChecked(True)
        settings_layout.addWidget(self.chk_metadata)

        self.chk_cache = QCheckBox("Cache Audio Analysis")
        self.chk_cache.setChecked(True)
        settings_layout.addWidget(self.chk_cache)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        # Job table
        table_group = QGroupBox("Batch Jobs")
        table_layout = QVBoxLayout()

        self.btn_scan = QPushButton("Scan Files")
        self.btn_scan.clicked.connect(self._scan_files)
        table_layout.addWidget(self.btn_scan)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "File", "Background", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(200)
        table_layout.addWidget(self.table)

        self.lbl_count = QLabel("Files: 0")
        table_layout.addWidget(self.lbl_count)

        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # Progress
        progress_group = QGroupBox("Batch Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Ready")
        progress_layout.addWidget(self.lbl_status)

        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("Start Batch Render")
        self.btn_start.setObjectName("primaryButton")
        self.btn_start.clicked.connect(self.batch_start_requested.emit)
        btn_layout.addWidget(self.btn_start)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.batch_cancel_requested.emit)
        self.btn_cancel.setEnabled(False)
        btn_layout.addWidget(self.btn_cancel)
        progress_layout.addLayout(btn_layout)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        layout.addStretch()

    def _select_audio_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if folder:
            self.audio_folder = folder
            self.lbl_audio.setText(folder)

    def _select_bg_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Background Folder")
        if folder:
            self.bg_folder = folder
            self.lbl_bg.setText(folder)

    def _select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder
            self.lbl_output.setText(folder)

    def _scan_files(self):
        from app.render.batch_folder_renderer import BatchFolderRenderer
        batch = BatchFolderRenderer()
        batch.audio_folder = self.audio_folder
        batch.background_folder = self.bg_folder
        batch.output_folder = self.output_folder
        batch.bg_mode = self.combo_bg_mode.currentText()

        jobs = batch.prepare_jobs()
        self.table.setRowCount(len(jobs))
        for i, job in enumerate(jobs):
            self.table.setItem(i, 0, QTableWidgetItem(str(job["index"])))
            self.table.setItem(i, 1, QTableWidgetItem(job["name"]))
            bg_name = os.path.basename(job["background_path"]) if job["background_path"] else "None"
            self.table.setItem(i, 2, QTableWidgetItem(bg_name))
            self.table.setItem(i, 3, QTableWidgetItem("Pending"))

        self.lbl_count.setText(f"Files: {len(jobs)}")

    def update_job_status(self, index, status):
        row = index - 1
        if 0 <= row < self.table.rowCount():
            self.table.setItem(row, 3, QTableWidgetItem(status))

    def update_progress(self, pct, msg):
        self.progress_bar.setValue(pct)
        self.lbl_status.setText(msg)

    def get_settings(self):
        return {
            "audio_folder": self.audio_folder,
            "bg_folder": self.bg_folder,
            "output_folder": self.output_folder,
            "bg_mode": self.combo_bg_mode.currentText(),
            "auto_lyrics": self.chk_auto_lyrics.isChecked(),
            "auto_sync": self.chk_auto_sync.isChecked(),
            "use_metadata": self.chk_metadata.isChecked(),
            "cache": self.chk_cache.isChecked(),
        }
