"""Tests for batch background matching."""

from __future__ import annotations

import os
from pathlib import Path

from app.core.batch import build_batch


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")


def test_match_order(tmp_path):
    music = tmp_path / "music"
    bg = tmp_path / "bg"
    for i in range(3):
        _touch(music / f"track{i}.mp3")
        _touch(bg / f"bg{i}.jpg")
    jobs = build_batch(str(music), str(bg), match_mode="order")
    assert len(jobs) == 3
    for j in jobs:
        assert j.background_files


def test_match_name(tmp_path):
    music = tmp_path / "music"
    bg = tmp_path / "bg"
    _touch(music / "song-alpha.mp3")
    _touch(bg / "song-alpha-bg.jpg")
    _touch(bg / "other.jpg")
    jobs = build_batch(str(music), str(bg), match_mode="name")
    assert len(jobs) == 1
    assert os.path.basename(jobs[0].background_files[0]) == "song-alpha-bg.jpg"


def test_missing_folders(tmp_path):
    jobs = build_batch(str(tmp_path / "missing"), str(tmp_path / "missing2"), match_mode="order")
    assert jobs == []
