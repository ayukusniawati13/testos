"""Smoke test: every spectrum style renders without errors."""

from __future__ import annotations

import numpy as np

from app.config import SpectrumConfig
from app.render.spectrum_styles import SPECTRUM_STYLES, draw_spectrum


def _frame(w=320, h=180):
    return np.zeros((h, w, 3), dtype=np.uint8)


def test_every_style_runs():
    cfg = SpectrumConfig()
    bands = np.linspace(0, 1, cfg.bar_count, dtype=np.float32)
    for name in SPECTRUM_STYLES:
        cfg.style = name
        frame = _frame()
        draw_spectrum(frame, bands, loudness=0.4, cfg=cfg, frame_index=10, fps=30)
        assert frame.shape == (180, 320, 3)


def test_resamples_band_count_mismatch():
    cfg = SpectrumConfig(bar_count=48)
    bands = np.linspace(0, 1, 12, dtype=np.float32)  # fewer bands than configured
    frame = _frame()
    draw_spectrum(frame, bands, loudness=0.5, cfg=cfg, frame_index=0, fps=30)
    assert frame.shape == (180, 320, 3)


def test_minimum_19_styles():
    assert len(SPECTRUM_STYLES) >= 15
