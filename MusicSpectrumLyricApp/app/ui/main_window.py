"""Main application window with tabbed interface."""

import os
import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QFileDialog, QLineEdit, QProgressBar,
    QTextEdit, QGroupBox, QSplitter, QMessageBox, QFormLayout,
    QFrame, QApplication,
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QIcon

from app.core.ffmpeg_manager import FFmpegManager
from app.core.lrc_parser import LRCParser
from app.core.video_renderer import VideoRenderer, RenderJob
from app.ui.settings_panel import SettingsPanel
from app.ui.preview_panel import PreviewPanel
from app.ui.batch_panel import BatchPanel

logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent.parent.parent


class FFmpegInstallThread(QThread):
    progress = Signal(str)
    finished_signal = Signal(bool)

    def __init__(self, ffmpeg: FFmpegManager):
        super().__init__()
        self.ffmpeg = ffmpeg

    def run(self) -> None:
        try:
            result = self.ffmpeg.download_and_install(
                progress_callback=self.progress.emit
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.progress.emit(f"Error: {e}")
            self.finished_signal.emit(False)


class RenderThread(QThread):
    progress_update = Signal(int)
    log_message = Signal(str)
    finished_signal = Signal(bool)

    def __init__(self, renderer: VideoRenderer, job: RenderJob):
        super().__init__()
        self.renderer = renderer
        self.job = job

    def run(self) -> None:
        try:
            result = self.renderer.render(
                self.job,
                progress_callback=self.progress_update.emit,
                log_callback=self.log_message.emit,
            )
            self.finished_signal.emit(result)
        except Exception as e:
            self.log_message.emit(f"Error: {e}")
            self.finished_signal.emit(False)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ffmpeg = FFmpegManager()
        self.renderer = VideoRenderer(self.ffmpeg)
        self._render_thread: RenderThread | None = None
        self._ffmpeg_thread: FFmpegInstallThread | None = None

        self.setWindowTitle("Music Spectrum Lyric Video Maker")
        self.setMinimumSize(1100, 750)
        self.resize(1280, 820)

        self._setup_ui()
        self._update_ffmpeg_status()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 8, 12, 8)

        header = QHBoxLayout()
        title = QLabel("Music Spectrum Lyric Video Maker")
        title.setObjectName("titleLabel")
        header.addWidget(title)
        header.addStretch()

        self.ffmpeg_status = QLabel()
        header.addWidget(self.ffmpeg_status)
        self.ffmpeg_install_btn = QPushButton("Install FFmpeg Online")
        self.ffmpeg_install_btn.clicked.connect(self._install_ffmpeg)
        self.ffmpeg_install_btn.setVisible(False)
        header.addWidget(self.ffmpeg_install_btn)
        main_layout.addLayout(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2d2d4a;")
        main_layout.addWidget(sep)

        tabs = QTabWidget()

        single_tab = QWidget()
        self._setup_single_tab(single_tab)
        tabs.addTab(single_tab, "Single Render")

        self.batch_panel = BatchPanel(self.ffmpeg)
        tabs.addTab(self.batch_panel, "Batch Render")

        main_layout.addWidget(tabs, 1)

    def _setup_single_tab(self, tab: QWidget) -> None:
        layout = QHBoxLayout(tab)
        layout.setSpacing(10)

        left = QVBoxLayout()
        left.setSpacing(8)

        files_group = QGroupBox("Input Files")
        files_form = QFormLayout()
        files_form.setSpacing(8)

        row_music = QHBoxLayout()
        self.music_path = QLineEdit()
        self.music_path.setPlaceholderText("Select music file (MP3, WAV, FLAC, M4A)...")
        self.music_path.setReadOnly(True)
        btn_music = QPushButton("Browse")
        btn_music.clicked.connect(self._browse_music)
        row_music.addWidget(self.music_path)
        row_music.addWidget(btn_music)
        files_form.addRow("Music:", row_music)

        row_lrc = QHBoxLayout()
        self.lrc_path = QLineEdit()
        self.lrc_path.setPlaceholderText("Select .LRC lyric file...")
        self.lrc_path.setReadOnly(True)
        btn_lrc = QPushButton("Browse")
        btn_lrc.clicked.connect(self._browse_lrc)
        row_lrc.addWidget(self.lrc_path)
        row_lrc.addWidget(btn_lrc)
        files_form.addRow("Lyrics:", row_lrc)

        row_bg = QHBoxLayout()
        self.bg_path = QLineEdit()
        self.bg_path.setPlaceholderText("Select background (image or video)...")
        self.bg_path.setReadOnly(True)
        btn_bg = QPushButton("Browse")
        btn_bg.clicked.connect(self._browse_bg)
        row_bg.addWidget(self.bg_path)
        row_bg.addWidget(btn_bg)
        files_form.addRow("Background:", row_bg)

        row_out = QHBoxLayout()
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("Output file path...")
        self.output_path.setReadOnly(True)
        btn_out = QPushButton("Browse")
        btn_out.clicked.connect(self._browse_output)
        row_out.addWidget(self.output_path)
        row_out.addWidget(btn_out)
        files_form.addRow("Output:", row_out)

        files_group.setLayout(files_form)
        left.addWidget(files_group)

        self.preview_panel = PreviewPanel()
        left.addWidget(self.preview_panel, 1)

        btn_row = QHBoxLayout()
        self.preview_btn = QPushButton("Update Preview")
        self.preview_btn.clicked.connect(self._update_preview)
        self.render_btn = QPushButton("Render Video")
        self.render_btn.setObjectName("renderBtn")
        self.render_btn.clicked.connect(self._start_render)
        self.stop_btn = QPushButton("Stop Render")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.clicked.connect(self._stop_render)
        self.stop_btn.setEnabled(False)
        btn_row.addWidget(self.preview_btn)
        btn_row.addWidget(self.render_btn)
        btn_row.addWidget(self.stop_btn)
        left.addLayout(btn_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("Render: %p%")
        left.addWidget(self.progress_bar)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        left.addWidget(self.log_text)

        left_widget = QWidget()
        left_widget.setLayout(left)

        self.settings_panel = SettingsPanel()
        self.settings_panel.setMinimumWidth(320)
        self.settings_panel.setMaximumWidth(420)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(self.settings_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

    def _update_ffmpeg_status(self) -> None:
        if self.ffmpeg.is_available:
            self.ffmpeg_status.setObjectName("ffmpegOk")
            self.ffmpeg_status.setText("FFmpeg Installed")
            self.ffmpeg_status.setStyle(self.ffmpeg_status.style())
            self.ffmpeg_install_btn.setVisible(False)
        else:
            self.ffmpeg_status.setObjectName("ffmpegError")
            self.ffmpeg_status.setText("FFmpeg Not Found")
            self.ffmpeg_status.setStyle(self.ffmpeg_status.style())
            self.ffmpeg_install_btn.setVisible(True)

    def _install_ffmpeg(self) -> None:
        self.ffmpeg_install_btn.setEnabled(False)
        self.ffmpeg_install_btn.setText("Installing...")
        self._ffmpeg_thread = FFmpegInstallThread(self.ffmpeg)
        self._ffmpeg_thread.progress.connect(
            lambda msg: self.ffmpeg_status.setText(msg))
        self._ffmpeg_thread.finished_signal.connect(self._on_ffmpeg_installed)
        self._ffmpeg_thread.start()

    def _on_ffmpeg_installed(self, success: bool) -> None:
        self._update_ffmpeg_status()
        self.ffmpeg_install_btn.setEnabled(True)
        self.ffmpeg_install_btn.setText("Install FFmpeg Online")
        if success:
            QMessageBox.information(self, "FFmpeg", "FFmpeg installed successfully!")
        else:
            QMessageBox.warning(self, "FFmpeg",
                                "Failed to install FFmpeg. Check your internet connection.")

    def _browse_music(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Music File", "",
            "Audio Files (*.mp3 *.wav *.flac *.m4a *.ogg *.wma);;All Files (*)"
        )
        if path:
            self.music_path.setText(path)
            stem = Path(path).stem
            out_dir = str(APP_DIR / "output")
            os.makedirs(out_dir, exist_ok=True)
            self.output_path.setText(os.path.join(out_dir, f"{stem}.mp4"))

    def _browse_lrc(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select LRC File", "",
            "LRC Files (*.lrc);;Text Files (*.txt);;All Files (*)"
        )
        if path:
            self.lrc_path.setText(path)

    def _browse_bg(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Background", "",
            "Media Files (*.jpg *.jpeg *.png *.webp *.bmp *.mp4 *.mov *.mkv);;All Files (*)"
        )
        if path:
            self.bg_path.setText(path)

    def _browse_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Output Video", "",
            "MP4 Files (*.mp4);;All Files (*)"
        )
        if path:
            if not path.lower().endswith(".mp4"):
                path += ".mp4"
            self.output_path.setText(path)

    def _update_preview(self) -> None:
        spec_cfg = self.settings_panel.get_spectrum_config()
        lyric_cfg = self.settings_panel.get_lyric_config()
        self.preview_panel.set_config(spec_cfg, lyric_cfg)

        lrc = self.lrc_path.text()
        if lrc and os.path.isfile(lrc):
            lyrics = LRCParser.parse(lrc)
            self.preview_panel.set_lyrics(lyrics)

        self.preview_panel._render_frame()

    def _start_render(self) -> None:
        music = self.music_path.text()
        lrc = self.lrc_path.text()
        output = self.output_path.text()

        if not music or not os.path.isfile(music):
            QMessageBox.warning(self, "Error", "Please select a valid music file.")
            return
        if not output:
            QMessageBox.warning(self, "Error", "Please select an output file path.")
            return

        if not self.ffmpeg.is_available:
            QMessageBox.warning(self, "Error",
                                "FFmpeg is not available. Please install it first.")
            return

        job = RenderJob()
        job.music_path = music
        job.lrc_path = lrc
        job.background_path = self.bg_path.text()
        job.output_path = output
        job.video_config = self.settings_panel.get_video_config()
        job.spectrum_config = self.settings_panel.get_spectrum_config()
        job.lyric_config = self.settings_panel.get_lyric_config()
        job.logo_config = self.settings_panel.get_logo_config()

        self.render_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()

        self._render_thread = RenderThread(self.renderer, job)
        self._render_thread.progress_update.connect(self.progress_bar.setValue)
        self._render_thread.log_message.connect(self._append_log)
        self._render_thread.finished_signal.connect(self._on_render_finished)
        self._render_thread.start()

        # Also update batch panel configs
        self.batch_panel.set_configs(
            job.video_config, job.spectrum_config,
            job.lyric_config, job.logo_config
        )

    def _stop_render(self) -> None:
        self.renderer.cancel()
        self.stop_btn.setEnabled(False)

    def _on_render_finished(self, success: bool) -> None:
        self.render_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if success:
            self._append_log("Render complete!")
            QMessageBox.information(self, "Done", "Video rendered successfully!")
        else:
            self._append_log("Render failed or cancelled.")

    def _append_log(self, msg: str) -> None:
        self.log_text.append(msg)

        log_file = APP_DIR / "render_log.txt"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(msg + "\n")
        except Exception:
            pass
