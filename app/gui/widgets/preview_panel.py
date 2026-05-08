"""Lightweight preview panel that renders a single representative frame.

This is meant for fast iteration on style settings — it does not play the
audio. The full render pipeline runs in :mod:`app.core.render_engine`.
"""
from __future__ import annotations

from typing import Optional, Sequence

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from app.core.render_engine import (
    BackgroundSpec,
    LogoSpec,
    AnimationOverlaySpec,
    _AnimationOverlayPlayer,
    _apply_logo_fade,
    _logo_position,
    _prepare_background,
    _prepare_logo,
)
from app.core.spectrum_engine import SpectrumConfig, SpectrumEngine
from app.core.lyric_engine import LyricEngine, LyricStyle, LyricTrack


class PreviewPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel("Preview will appear here")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            "background-color: #11131a; border: 1px solid #1f2230; border-radius: 6px;"
        )
        self._label.setMinimumSize(480, 270)
        self._label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self._label, 1)

    def render_preview(
        self,
        size,
        spectrum_config: SpectrumConfig,
        background: BackgroundSpec,
        lyric_style: LyricStyle,
        bands: Optional[Sequence[float]] = None,
        lyric_track: Optional[LyricTrack] = None,
        logo: Optional[LogoSpec] = None,
        animation: Optional[AnimationOverlaySpec] = None,
    ) -> None:
        width, height = size
        # Generate a synthetic, mildly noisy band vector if none provided.
        if bands is None:
            bands = _synthetic_bands(spectrum_config.bar_count)

        canvas = _prepare_background(background, (width, height)).convert("RGBA")
        engine = SpectrumEngine(spectrum_config)
        spectrum_layer = engine.render_frame(
            size=(width, height),
            bands=bands,
            energy=0.65,
            bass=0.6,
            mid=0.5,
            treble=0.5,
            beat_pulse=0.4,
            time=0.0,
        )
        canvas.alpha_composite(spectrum_layer)

        if lyric_style.enabled and lyric_track is not None and not lyric_track.is_empty():
            lyric_engine = LyricEngine(lyric_style)
            lyric_engine.set_track(lyric_track)
            lyric_layer = lyric_engine.render_frame(
                (width, height),
                lyric_track.lines[0].start + 0.1,
            )
            if lyric_layer is not None:
                canvas.alpha_composite(lyric_layer)
        elif lyric_style.enabled:
            # Synthetic preview line so the user sees the styling.
            lyric_engine = LyricEngine(lyric_style)
            lyric_engine.set_track(LyricTrack(lines=[
                _preview_line()
            ]))
            preview_layer = lyric_engine.render_frame((width, height), 0.5)
            if preview_layer is not None:
                canvas.alpha_composite(preview_layer)

        logo_spec = logo or LogoSpec()
        logo_layer = _prepare_logo(logo_spec, (width, height))
        if logo_layer is not None:
            x, y = _logo_position(logo_spec, (width, height), logo_layer.size)
            faded = _apply_logo_fade(logo_layer, logo_spec, 0.0, 1.0)
            canvas.alpha_composite(faded, (x, y))

        animation_spec = animation or AnimationOverlaySpec()
        if animation_spec.enabled and animation_spec.path:
            player = _AnimationOverlayPlayer(animation_spec, (width, height), 1.0)
            layer = player.frame_at(animation_spec.start_at)
            if layer is not None:
                canvas.alpha_composite(layer)

        self._label.setPixmap(_pillow_to_pixmap(canvas).scaled(
            self._label.width() or 480,
            self._label.height() or 270,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))


def _synthetic_bands(n: int) -> list:
    import math

    return [0.4 + 0.4 * math.sin(i * 0.32) + 0.15 * math.sin(i * 0.05) for i in range(n)]


def _preview_line():
    from app.core.lyric_engine import LyricLine, LyricWord

    text = "Spectrum Lyric Preview"
    words = text.split()
    word_objs = []
    t = 0.0
    for w in words:
        word_objs.append(LyricWord(text=w, start=t, end=t + 0.5))
        t += 0.5
    return LyricLine(text=text, start=0.0, end=t + 1.0, words=word_objs)


def _pillow_to_pixmap(image: Image.Image) -> QPixmap:
    rgba = image.convert("RGBA")
    data = rgba.tobytes("raw", "RGBA")
    qimg = QImage(data, rgba.width, rgba.height, rgba.width * 4, QImage.Format.Format_RGBA8888)
    return QPixmap.fromImage(qimg.copy())
