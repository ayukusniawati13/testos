"""Entry point for Spectrum Lyric Video Maker.

Usage:
    python run.py
"""
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    # Make sure the project root is on sys.path so ``app`` is importable when
    # the user runs ``python run.py`` from any working directory.
    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from app.main import run

    return run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
