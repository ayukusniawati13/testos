"""Spectrum Lyric Video Maker — top-level package.

This package keeps heavy dependencies (PySide6, librosa, faster-whisper,
opencv) out of the import path so submodules can be imported individually
without pulling the GUI stack.
"""

__version__ = "0.1.0"
