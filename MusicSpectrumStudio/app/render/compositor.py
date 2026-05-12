"""Composite a single output frame from all layers."""

from __future__ import annotations

import numpy as np

from ..config import AppConfig
from ..core.audio_spectrum import SpectrumStream
from .background import BackgroundProvider
from .effects import EffectContext, apply_effects
from .logo import LogoOverlay
from .lyrics_styles import LyricRenderState, composite_lyrics, render_lyrics_frame
from .spectrum_styles import draw_spectrum


class FrameCompositor:
    def __init__(
        self,
        cfg: AppConfig,
        spectrum: SpectrumStream,
        lyrics: LyricRenderState | None,
        width: int,
        height: int,
    ):
        self.cfg = cfg
        self.spectrum = spectrum
        self.lyrics = lyrics
        self.width = width
        self.height = height
        self.bg = BackgroundProvider(cfg.background, width, height)
        self.logo = LogoOverlay(cfg.logo, width, height)

    def close(self) -> None:
        self.bg.close()

    def frame(self, frame_index: int) -> np.ndarray:
        fps = self.cfg.render.fps
        t = frame_index / float(fps)
        out = self.bg.get_frame(t).copy()
        # spectrum
        if frame_index < len(self.spectrum.bands):
            bands = self.spectrum.bands[frame_index]
            loud = float(self.spectrum.loudness[frame_index])
        else:
            bands = self.spectrum.bands[-1]
            loud = float(self.spectrum.loudness[-1])
        beat = bool(self.spectrum.beat[frame_index]) if frame_index < len(self.spectrum.beat) else False

        draw_spectrum(out, bands, loud, self.cfg.spectrum, frame_index=frame_index, fps=fps)
        # lyrics
        if self.lyrics is not None and self.cfg.lyrics.enabled:
            overlay = render_lyrics_frame(self.lyrics, self.cfg.lyrics, t)
            composite_lyrics(out, overlay)
        # logo
        self.logo.draw(out)
        # effects
        ctx = EffectContext.make(self.width, self.height, frame_index, fps, loud, beat)
        apply_effects(out, self.cfg.effects, ctx)
        return out
