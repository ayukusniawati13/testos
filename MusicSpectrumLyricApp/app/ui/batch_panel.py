"""Batch rendering panel with job table and folder selection."""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QFileDialog, QProgressBar, QHeaderView, QTextEdit, QSplitter,
    QFormLayout,
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QColor

from app.core.batch_manager import (
    BatchManager, BatchJob, BackgroundMode, JobStatus,
)
from app.core.video_renderer import VideoConfig
from app.core.spectrum_engine import SpectrumConfig
from app.core.lyric_renderer import LyricConfig
from app.core.video_renderer import LogoConfig
from app.core.ffmpeg_manager import FFmpegManager


class BatchRenderThread(QThread):
    progress_update = Signal(int)
    job_update = Signal(int, object)
    log_message = Signal(str)
    finished_signal = Signal()

    def __init__(self, manager: BatchManager, video_config: VideoConfig,
                 spectrum_config: SpectrumConfig, lyric_config: LyricConfig,
                 logo_config: LogoConfig):
        super().__init__()
        self.manager = manager
        self.video_config = video_config
        self.spectrum_config = spectrum_config
        self.lyric_config = lyric_config
        self.logo_config = logo_config

    def run(self) -> None:
        self.manager.render_all(
            self.video_config,
            self.spectrum_config,
            self.lyric_config,
            self.logo_config,
            progress_callback=self.progress_update.emit,
            job_callback=lambda idx, job: self.job_update.emit(idx, job),
            log_callback=self.log_message.emit,
        )
        self.finished_signal.emit()


class BatchPanel(QWidget):
    batch_started = Signal()
    batch_finished = Signal()

    def __init__(self, ffmpeg: FFmpegManager | None = None, parent=None):
        super().__init__(parent)
        self.ffmpeg = ffmpeg or FFmpegManager()
        self.manager = BatchManager(self.ffmpeg)
        self._thread: BatchRenderThread | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        folders_group = QGroupBox("Batch Folders")
        form = QFormLayout()
        form.setSpacing(8)

        self.music_folder = QLineEdit()
        self.music_folder.setPlaceholderText("Select music folder...")
        self.music_folder.setReadOnly(True)
        btn_music = QPushButton("Browse")
        btn_music.clicked.connect(lambda: self._browse_folder(self.music_folder))
        row1 = QHBoxLayout()
        row1.addWidget(self.music_folder)
        row1.addWidget(btn_music)
        form.addRow("Music Folder:", row1)

        self.lrc_folder = QLineEdit()
        self.lrc_folder.setPlaceholderText("Select lyrics folder...")
        self.lrc_folder.setReadOnly(True)
        btn_lrc = QPushButton("Browse")
        btn_lrc.clicked.connect(lambda: self._browse_folder(self.lrc_folder))
        row2 = QHBoxLayout()
        row2.addWidget(self.lrc_folder)
        row2.addWidget(btn_lrc)
        form.addRow("Lyrics Folder:", row2)

        self.bg_folder = QLineEdit()
        self.bg_folder.setPlaceholderText("Select background folder...")
        self.bg_folder.setReadOnly(True)
        btn_bg = QPushButton("Browse")
        btn_bg.clicked.connect(lambda: self._browse_folder(self.bg_folder))
        row3 = QHBoxLayout()
        row3.addWidget(self.bg_folder)
        row3.addWidget(btn_bg)
        form.addRow("Background Folder:", row3)

        self.output_folder = QLineEdit()
        self.output_folder.setPlaceholderText("Select output folder...")
        self.output_folder.setReadOnly(True)
        btn_out = QPushButton("Browse")
        btn_out.clicked.connect(lambda: self._browse_folder(self.output_folder))
        row4 = QHBoxLayout()
        row4.addWidget(self.output_folder)
        row4.addWidget(btn_out)
        form.addRow("Output Folder:", row4)

        self.bg_mode_combo = QComboBox()
        self.bg_mode_combo.addItems([
            "Match by Filename",
            "Sequential Order",
            "Random",
        ])
        form.addRow("Background Mode:", self.bg_mode_combo)

        folders_group.setLayout(form)
        layout.addWidget(folders_group)

        btn_row = QHBoxLayout()
        self.scan_btn = QPushButton("Scan && Match Files")
        self.scan_btn.clicked.connect(self._scan)
        self.render_btn = QPushButton("Start Batch Render")
        self.render_btn.setObjectName("renderBtn")
        self.render_btn.clicked.connect(self._start_render)
        self.render_btn.setEnabled(False)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.clicked.connect(self._stop_render)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.scan_btn)
        btn_row.addWidget(self.render_btn)
        btn_row.addWidget(self.stop_btn)
        layout.addLayout(btn_row)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Music", "Lyrics", "Background", "Status", "Progress", "Output"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        splitter.addWidget(self.table)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        splitter.addWidget(self.log_text)

        layout.addWidget(splitter, 1)

        self.total_progress = QProgressBar()
        self.total_progress.setFormat("Total: %p%")
        layout.addWidget(self.total_progress)

    def _browse_folder(self, line_edit: QLineEdit) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            line_edit.setText(folder)

    def _scan(self) -> None:
        music = self.music_folder.text()
        lrc = self.lrc_folder.text()
        bg = self.bg_folder.text()
        output = self.output_folder.text()

        if not music or not output:
            return

        mode_idx = self.bg_mode_combo.currentIndex()
        modes = [BackgroundMode.MATCH_NAME, BackgroundMode.SEQUENTIAL, BackgroundMode.RANDOM]
        bg_mode = modes[mode_idx]

        jobs = self.manager.scan_folders(music, lrc, bg, output, bg_mode)
        self._populate_table(jobs)
        self.render_btn.setEnabled(len(jobs) > 0)

    def _populate_table(self, jobs: list[BatchJob]) -> None:
        self.table.setRowCount(len(jobs))
        for row, job in enumerate(jobs):
            self.table.setItem(row, 0, QTableWidgetItem(job.music_name))

            lrc_item = QTableWidgetItem(job.lrc_status)
            if job.lrc_status == "Found":
                lrc_item.setForeground(QColor("#00e676"))
            else:
                lrc_item.setForeground(QColor("#ff5252"))
            self.table.setItem(row, 1, lrc_item)

            bg_item = QTableWidgetItem(job.bg_status)
            if job.bg_status in ("Matched", "Sequential", "Random", "Default"):
                bg_item.setForeground(QColor("#00e676"))
            else:
                bg_item.setForeground(QColor("#ff5252"))
            self.table.setItem(row, 2, bg_item)

            self.table.setItem(row, 3, QTableWidgetItem(job.status.value))
            self.table.setItem(row, 4, QTableWidgetItem("0%"))
            self.table.setItem(row, 5, QTableWidgetItem(
                os.path.basename(job.output_path)))

    def _update_job_row(self, idx: int, job: BatchJob) -> None:
        if idx >= self.table.rowCount():
            return

        status_item = QTableWidgetItem(job.status.value)
        if job.status == JobStatus.COMPLETED:
            status_item.setForeground(QColor("#00e676"))
        elif job.status == JobStatus.ERROR:
            status_item.setForeground(QColor("#ff5252"))
        elif job.status == JobStatus.RENDERING:
            status_item.setForeground(QColor("#00d4ff"))
        self.table.setItem(idx, 3, status_item)
        self.table.setItem(idx, 4, QTableWidgetItem(f"{job.progress}%"))

    def set_configs(self, video_config: VideoConfig,
                    spectrum_config: SpectrumConfig,
                    lyric_config: LyricConfig,
                    logo_config: LogoConfig) -> None:
        self._video_config = video_config
        self._spectrum_config = spectrum_config
        self._lyric_config = lyric_config
        self._logo_config = logo_config

    def _start_render(self) -> None:
        if not hasattr(self, "_video_config"):
            return

        self.render_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.scan_btn.setEnabled(False)
        self.log_text.clear()
        self.total_progress.setValue(0)

        self._thread = BatchRenderThread(
            self.manager,
            self._video_config,
            self._spectrum_config,
            self._lyric_config,
            self._logo_config,
        )
        self._thread.progress_update.connect(self.total_progress.setValue)
        self._thread.job_update.connect(
            lambda idx, job: self._update_job_row(idx, job))
        self._thread.log_message.connect(self._append_log)
        self._thread.finished_signal.connect(self._on_finished)
        self._thread.start()
        self.batch_started.emit()

    def _stop_render(self) -> None:
        self.manager.cancel()
        self.stop_btn.setEnabled(False)

    def _on_finished(self) -> None:
        self.render_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.scan_btn.setEnabled(True)
        self._append_log("Batch render complete.")
        self.batch_finished.emit()

    def _append_log(self, msg: str) -> None:
        self.log_text.append(msg)
