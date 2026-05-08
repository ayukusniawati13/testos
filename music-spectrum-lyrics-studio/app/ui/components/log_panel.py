"""
Log and progress panel.
"""
import os
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QPlainTextEdit
)
from PyQt6.QtCore import pyqtSignal, QObject, Qt
from app.core.config import DIRS


class QTextHandler(logging.Handler, QObject):
    """Custom logging handler that emits to a QPlainTextEdit."""

    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self._widget = None

    def set_widget(self, widget):
        self._widget = widget

    def emit(self, record):
        if self._widget:
            msg = self.format(record)
            try:
                self._widget.appendPlainText(msg)
            except RuntimeError:
                pass


class LogPanel(QWidget):
    """Panel for application log display."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_handler()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        log_group = QGroupBox("Application Log")
        log_layout = QVBoxLayout()

        self.txt_log = QPlainTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumBlockCount(5000)
        self.txt_log.setMinimumHeight(200)
        log_layout.addWidget(self.txt_log)

        btn_layout = QHBoxLayout()
        self.btn_clear = QPushButton("Clear Log")
        self.btn_clear.clicked.connect(self.txt_log.clear)
        btn_layout.addWidget(self.btn_clear)

        self.btn_open_folder = QPushButton("Open Log Folder")
        self.btn_open_folder.clicked.connect(self._open_log_folder)
        btn_layout.addWidget(self.btn_open_folder)

        self.btn_save = QPushButton("Save Log")
        self.btn_save.clicked.connect(self._save_log)
        btn_layout.addWidget(self.btn_save)

        log_layout.addLayout(btn_layout)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # FFmpeg status
        ffmpeg_group = QGroupBox("FFmpeg Status")
        ffmpeg_layout = QVBoxLayout()

        self.lbl_ffmpeg = QLabel("Checking FFmpeg...")
        ffmpeg_layout.addWidget(self.lbl_ffmpeg)

        self.btn_install_ffmpeg = QPushButton("Install FFmpeg (winget)")
        self.btn_install_ffmpeg.clicked.connect(self._install_ffmpeg)
        self.btn_install_ffmpeg.setVisible(False)
        ffmpeg_layout.addWidget(self.btn_install_ffmpeg)

        ffmpeg_group.setLayout(ffmpeg_layout)
        layout.addWidget(ffmpeg_group)

        # System info
        sys_group = QGroupBox("System Info")
        sys_layout = QVBoxLayout()

        self.lbl_system = QLabel("Loading...")
        sys_layout.addWidget(self.lbl_system)

        sys_group.setLayout(sys_layout)
        layout.addWidget(sys_group)

        layout.addStretch()

    def _setup_handler(self):
        self.log_handler = QTextHandler()
        self.log_handler.set_widget(self.txt_log)
        self.log_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
        ))
        logging.getLogger().addHandler(self.log_handler)

    def log(self, message):
        self.txt_log.appendPlainText(message)

    def check_ffmpeg(self):
        from app.utils.helpers import check_ffmpeg
        installed, info = check_ffmpeg()
        if installed:
            self.lbl_ffmpeg.setText(f"FFmpeg: Installed - {info}")
            self.btn_install_ffmpeg.setVisible(False)
        else:
            self.lbl_ffmpeg.setText(f"FFmpeg: Not installed - {info}")
            self.btn_install_ffmpeg.setVisible(True)

    def update_system_info(self):
        try:
            from app.utils.helpers import get_system_info
            info = get_system_info()
            text = (
                f"Platform: {info['platform']}\n"
                f"CPU Cores: {info['cpu_count']}\n"
                f"RAM: {info['ram_gb']} GB\n"
                f"GPU Available: {'Yes' if info['gpu_available'] else 'No'}\n"
                f"Recommended Mode: {info['recommended_mode']}"
            )
            self.lbl_system.setText(text)
        except Exception as e:
            self.lbl_system.setText(f"System info unavailable: {e}")

    def _install_ffmpeg(self):
        from app.utils.helpers import install_ffmpeg
        self.log("Installing FFmpeg...")
        success, msg = install_ffmpeg()
        if success:
            self.log(f"FFmpeg installed: {msg}")
            self.check_ffmpeg()
        else:
            self.log(f"FFmpeg install failed: {msg}")

    def _open_log_folder(self):
        import subprocess
        import sys
        log_dir = DIRS["logs"]
        os.makedirs(log_dir, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(log_dir)
        elif sys.platform == "darwin":
            subprocess.run(["open", log_dir])
        else:
            subprocess.run(["xdg-open", log_dir])

    def _save_log(self):
        from datetime import datetime
        log_dir = DIRS["logs"]
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(log_dir, f"render_{timestamp}.log")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.txt_log.toPlainText())
        self.log(f"Log saved: {filepath}")
