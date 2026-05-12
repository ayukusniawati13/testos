"""Tests for lyric fade-in/out + gap-hide logic."""

from __future__ import annotations

from app.core.transcribe import LyricLine
from app.render.lyrics_styles import _line_visibility


def _line(text: str, start: float, end: float) -> LyricLine:
    return LyricLine(text=text, start=start, end=end, words=[])


def test_fade_in_before_start():
    line = _line("hello", 5.0, 7.0)
    assert 0.0 < _line_visibility(line, t=4.85, fade_s=0.3, hide_before_next=1.0, next_line=None) < 1.0
    assert _line_visibility(line, t=4.7, fade_s=0.3, hide_before_next=1.0, next_line=None) == 0.0
    assert _line_visibility(line, t=5.0, fade_s=0.3, hide_before_next=1.0, next_line=None) == 1.0


def test_fade_out_after_end_no_gap():
    line = _line("hello", 5.0, 7.0)
    nxt = _line("world", 7.1, 8.0)  # gap 0.1
    # Within fade window
    assert 0.0 < _line_visibility(line, 7.2, 0.3, hide_before_next=0.6, next_line=nxt) < 1.0


def test_hide_before_next_when_gap_large():
    line = _line("hello", 5.0, 7.0)
    nxt = _line("world", 9.0, 10.0)  # gap 2s, > line_gap_seconds=0.6
    # At end, alpha should already be fading out
    a_end = _line_visibility(line, 7.0, 0.3, hide_before_next=0.6, next_line=nxt)
    a_after = _line_visibility(line, 7.2, 0.3, hide_before_next=0.6, next_line=nxt)
    assert a_after < a_end
    assert a_after < 0.7


def test_invisible_far_before_or_after():
    line = _line("hello", 5.0, 7.0)
    assert _line_visibility(line, 0.0, 0.3, 0.6, None) == 0.0
    assert _line_visibility(line, 30.0, 0.3, 0.6, None) == 0.0
