"""Logging utilities for Spectrum Lyric Video Maker.

The application logs to two destinations:
- a rotating file in ``logs/app.log`` (persistent, project-relative)
- an in-process Qt-friendly handler that GUI panels can subscribe to

Heavy GUI dependencies are imported lazily inside :class:`QtSignalLogHandler`
so this module stays usable in headless contexts (e.g. unit tests, CLI).
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable, List, Optional

from app.utils import file_utils

LOG_NAME = "spectrum_lyric_video_maker"
DEFAULT_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
)

_LISTENERS: List[Callable[[str, int], None]] = []
_INITIALISED = False


class _BroadcastHandler(logging.Handler):
    """Forward formatted log records to every registered Python callable."""

    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - thin
        try:
            text = self.format(record)
        except Exception:  # pragma: no cover - defensive
            text = record.getMessage()
        for listener in list(_LISTENERS):
            try:
                listener(text, record.levelno)
            except Exception:
                # A faulty UI listener must never break the logging pipeline.
                pass


def add_listener(listener: Callable[[str, int], None]) -> None:
    """Register a callable to receive every formatted log line.

    Used by the in-app log panel to mirror the file log.
    """
    if listener not in _LISTENERS:
        _LISTENERS.append(listener)


def remove_listener(listener: Callable[[str, int], None]) -> None:
    if listener in _LISTENERS:
        _LISTENERS.remove(listener)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a child logger of the application root logger."""
    if name and not name.startswith(LOG_NAME):
        return logging.getLogger(f"{LOG_NAME}.{name}")
    return logging.getLogger(name or LOG_NAME)


def setup_logging(
    level: int = logging.INFO,
    log_dir: Optional[Path] = None,
    file_name: str = "app.log",
) -> logging.Logger:
    """Configure the application logger. Idempotent — safe to call repeatedly."""
    global _INITIALISED

    log_dir = Path(log_dir) if log_dir else file_utils.project_root() / "logs"
    file_utils.ensure_dir(log_dir)
    log_path = log_dir / file_name

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    root_logger = logging.getLogger(LOG_NAME)
    root_logger.setLevel(level)

    if not _INITIALISED:
        # File handler with simple rotation: 5 files of 1 MB each.
        try:
            file_handler = RotatingFileHandler(
                log_path, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            root_logger.addHandler(file_handler)
        except OSError:
            # Read-only filesystem etc. — keep going without a file log.
            pass

        stream_handler = logging.StreamHandler(stream=sys.stderr)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(level)
        root_logger.addHandler(stream_handler)

        broadcast = _BroadcastHandler()
        broadcast.setFormatter(formatter)
        broadcast.setLevel(level)
        root_logger.addHandler(broadcast)

        root_logger.propagate = False
        _INITIALISED = True

    return root_logger


def shutdown() -> None:  # pragma: no cover - cleanup helper
    """Flush + close handlers (call on app exit)."""
    logger = logging.getLogger(LOG_NAME)
    for handler in list(logger.handlers):
        try:
            handler.flush()
            handler.close()
        except Exception:
            pass
        logger.removeHandler(handler)
    _LISTENERS.clear()
