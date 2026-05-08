"""Application bootstrap: configure logging, load config, create the main window."""
from __future__ import annotations

import logging
import sys
from typing import List

from app.utils import file_utils
from app.utils.config import AppConfig
from app.utils.logger import get_logger, setup_logging


def run(argv: List[str] | None = None) -> int:
    """Launch the Spectrum Lyric Video Maker desktop app."""
    argv = list(argv if argv is not None else sys.argv)

    # Logging first so subsequent imports can emit messages.
    config = AppConfig.load()
    level_name = str(config.get("log_level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    setup_logging(level=level)
    logger = get_logger("main")
    logger.info("Starting Spectrum Lyric Video Maker")

    # Make sure user dirs exist (output / temp / presets).
    file_utils.ensure_dir(config.get("output_dir", str(file_utils.project_root() / "output")))
    file_utils.ensure_dir(config.get("temp_dir", str(file_utils.project_root() / "temp")))
    file_utils.ensure_dir(config.get("presets_dir", str(file_utils.project_root() / "presets")))

    # Lazy import so `python -c "from app import main"` doesn't pull Qt.
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:  # pragma: no cover - missing GUI dep
        logger.error("PySide6 is required to run the GUI: %s", exc)
        print(
            "PySide6 is not installed. Install it with `pip install -r requirements.txt`.",
            file=sys.stderr,
        )
        return 2

    from app.gui.main_window import MainWindow
    from app.gui.themes import load_dark_modern_qss

    app = QApplication.instance() or QApplication(argv)
    app.setApplicationName("Spectrum Lyric Video Maker")
    app.setOrganizationName("Spectrum Lyric Video Maker")

    qss = load_dark_modern_qss()
    if qss:
        app.setStyleSheet(qss)

    window = MainWindow(config=config)
    window.show()
    exit_code = app.exec()
    logger.info("Exiting with code %d", exit_code)
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(run(sys.argv))
