"""Time helpers for lyric / segment math."""

from __future__ import annotations


def format_srt(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    ms_total = int(round(seconds * 1000))
    hours, rem = divmod(ms_total, 3600000)
    minutes, rem = divmod(rem, 60000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def format_lrc(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    minutes = int(seconds // 60)
    rem = seconds - minutes * 60
    return f"[{minutes:02d}:{rem:05.2f}]"
