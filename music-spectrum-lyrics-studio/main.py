"""
Music Spectrum Lyrics Studio
=============================
Professional music video creator with audio spectrum visualization,
karaoke-style synchronized lyrics, logo branding, CTA animations,
batch rendering, and low-spec mode support.

Usage:
    python main.py
"""
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import APP_NAME, APP_VERSION, DIRS, ensure_dirs
from app.utils.helpers import setup_logging, check_ffmpeg


def main():
    ensure_dirs()
    setup_logging(DIRS["logs"])

    logger = logging.getLogger(__name__)
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")

    # Check FFmpeg
    ffmpeg_ok, ffmpeg_info = check_ffmpeg()
    if ffmpeg_ok:
        logger.info(f"FFmpeg: {ffmpeg_info}")
    else:
        logger.warning(f"FFmpeg not found: {ffmpeg_info}")
        logger.warning("Video rendering requires FFmpeg. Install it via setup.bat or manually.")

    # Start GUI
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    from app.ui.main_window import MainWindow
    window = MainWindow()
    window.show()

    logger.info("Application window opened")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
