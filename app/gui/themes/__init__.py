"""GUI themes (dark modern Qt stylesheet)."""
from __future__ import annotations

from pathlib import Path
from typing import Optional


def load_dark_modern_qss() -> Optional[str]:
    qss_path = Path(__file__).parent / "dark_modern.qss"
    try:
        return qss_path.read_text(encoding="utf-8")
    except OSError:
        return None


__all__ = ["load_dark_modern_qss"]
