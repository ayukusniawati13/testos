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
import traceback
import faulthandler

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import APP_NAME, APP_VERSION, DIRS, ensure_dirs
from app.utils.helpers import setup_logging, check_ffmpeg


def _global_exception_handler(exc_type, exc_value, exc_tb):
    """Catch unhandled exceptions so the app doesn't close silently."""
    logger = logging.getLogger(__name__)
    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logger.error(f"Unhandled exception:\n{tb_text}")

    try:
        from PyQt6.QtWidgets import QMessageBox, QApplication
        app = QApplication.instance()
        if app:
            msg = QMessageBox()
            msg.setWindowTitle("Error")
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setText("An unexpected error occurred.")
            msg.setDetailedText(tb_text)
            msg.exec()
    except Exception:
        pass


def _check_dependencies(logger):
    """Pre-check critical dependencies and log status."""
    deps = {
        "numpy": False,
        "librosa": False,
        "soundfile": False,
        "mutagen": False,
        "PIL": False,
    }
    for name in deps:
        try:
            __import__(name)
            deps[name] = True
        except ImportError:
            pass
    for name, ok in deps.items():
        if ok:
            logger.info(f"  {name}: OK")
        else:
            logger.warning(f"  {name}: NOT INSTALLED")
    return deps


def main():
    ensure_dirs()
    setup_logging(DIRS["logs"])

    # Enable faulthandler to get tracebacks on C-level crashes
    crash_log = os.path.join(DIRS["logs"], "crash.log")
    try:
        crash_fh = open(crash_log, "w")
        faulthandler.enable(file=crash_fh)
    except Exception:
        faulthandler.enable()

    sys.excepthook = _global_exception_handler

    logger = logging.getLogger(__name__)
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info(f"Python {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info("Checking dependencies...")
    _check_dependencies(logger)

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
    try:
        main()
    except Exception:
        traceback.print_exc()
        input("Press Enter to exit...")
