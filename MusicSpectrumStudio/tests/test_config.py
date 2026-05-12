"""Tests for AppConfig persistence."""

from __future__ import annotations

from app.config import AppConfig


def test_roundtrip(tmp_path):
    cfg = AppConfig()
    cfg.spectrum.style = "Ribbon"
    cfg.lyrics.font_size = 72
    cfg.render.width = 2560
    cfg.render.height = 1440
    path = tmp_path / "cfg.json"
    cfg.save(str(path))

    loaded = AppConfig.load(str(path))
    assert loaded.spectrum.style == "Ribbon"
    assert loaded.lyrics.font_size == 72
    assert loaded.render.width == 2560


def test_missing_file_returns_defaults(tmp_path):
    loaded = AppConfig.load(str(tmp_path / "nope.json"))
    assert loaded.spectrum.style == AppConfig().spectrum.style
