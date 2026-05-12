"""End-to-end smoke test for the renderer (no real ffmpeg call).

We exercise the compositor with synthetic data and verify a few frames render."""

from __future__ import annotations

import numpy as np

from app.config import AppConfig
from app.core.audio_spectrum import SpectrumStream
from app.core.transcribe import LyricLine, TranscriptionResult, WordTiming
from app.render.compositor import FrameCompositor
from app.render.lyrics_styles import LyricRenderState


def _stream(num_frames=15, bands=32):
    rng = np.random.default_rng(0)
    b = rng.random((num_frames, bands)).astype(np.float32)
    loud = b.mean(axis=1)
    beat = (np.arange(num_frames) % 5 == 0).astype(np.float32)
    return SpectrumStream(bands=b, loudness=loud, beat=beat, fps=30, num_bands=bands)


def _transcription():
    words = [WordTiming("hello", 0.2, 0.6), WordTiming("world", 0.7, 1.1)]
    line = LyricLine(text="Hello world", start=0.1, end=1.2, words=words)
    return TranscriptionResult(language="en", duration=2.0, lines=[line])


def test_compositor_runs_a_few_frames():
    cfg = AppConfig()
    cfg.render.width = 320
    cfg.render.height = 180
    cfg.spectrum.bar_count = 32
    cfg.lyrics.enabled = True
    cfg.lyrics.font_size = 28
    cfg.effects.glow = False
    cfg.effects.vignette = False
    lyrics_state = LyricRenderState(transcription=_transcription(), width=320, height=180)
    stream = _stream(15, 32)
    compositor = FrameCompositor(cfg, stream, lyrics_state, 320, 180)
    try:
        for i in range(10):
            frame = compositor.frame(i)
            assert frame.shape == (180, 320, 3)
            assert frame.dtype == np.uint8
    finally:
        compositor.close()
