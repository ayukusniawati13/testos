"""Build a standalone executable of Spectrum Lyric Video Maker via PyInstaller.

Usage:
    python build.py            # Build with default options
    python build.py --onefile  # Single-file executable
    python build.py --clean    # Clean previous build artifacts first
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
APP_NAME = "SpectrumLyricVideoMaker"


def _ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("[build] PyInstaller not found. Installing...", flush=True)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller>=6.0"]
        )


def _clean() -> None:
    for name in ("build", "dist", f"{APP_NAME}.spec"):
        target = PROJECT_ROOT / name
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        elif target.is_file():
            target.unlink(missing_ok=True)


def build(onefile: bool = False, clean: bool = False) -> int:
    _ensure_pyinstaller()
    if clean:
        _clean()

    cmd: list[str] = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name",
        APP_NAME,
        "--add-data",
        f"app/assets{':' if sys.platform != 'win32' else ';'}app/assets",
        "--add-data",
        f"app/gui/themes{':' if sys.platform != 'win32' else ';'}app/gui/themes",
        "run.py",
    ]
    if onefile:
        cmd.insert(4, "--onefile")

    print("[build] Running:", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=PROJECT_ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the desktop app with PyInstaller")
    parser.add_argument("--onefile", action="store_true", help="Build a single-file executable")
    parser.add_argument("--clean", action="store_true", help="Remove previous build artifacts")
    args = parser.parse_args()
    return build(onefile=args.onefile, clean=args.clean)


if __name__ == "__main__":
    raise SystemExit(main())
