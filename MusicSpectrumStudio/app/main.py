"""Entry point for Music Spectrum Studio."""

from __future__ import annotations

import logging
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from . import APP_NAME, ORG_NAME
from .ui.main_window import MainWindow
from .ui.theme import DARK_THEME


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> int:
    _setup_logging()
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setStyleSheet(DARK_THEME)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
