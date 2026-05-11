"""Preset spectrum style configurations."""

from app.core.spectrum_engine import SpectrumConfig, SpectrumStyle


SPECTRUM_PRESETS: dict[str, SpectrumConfig] = {}


def _make(style: str, **kwargs) -> SpectrumConfig:
    cfg = SpectrumConfig()
    cfg.style = style
    for k, v in kwargs.items():
        setattr(cfg, k, v)
    return cfg


SPECTRUM_PRESETS[SpectrumStyle.BAR_MODERN] = _make(
    SpectrumStyle.BAR_MODERN,
    color1=(0, 180, 255), color2=(255, 0, 180),
    sensitivity=1.2, glow=0.6, bar_width=8, bar_gap=3,
)

SPECTRUM_PRESETS[SpectrumStyle.CIRCULAR] = _make(
    SpectrumStyle.CIRCULAR,
    color1=(0, 255, 200), color2=(255, 100, 0),
    sensitivity=1.0, glow=0.7, position="center", height_ratio=0.4,
)

SPECTRUM_PRESETS[SpectrumStyle.WAVEFORM] = _make(
    SpectrumStyle.WAVEFORM,
    color1=(100, 200, 255), color2=(200, 100, 255),
    sensitivity=1.3, glow=0.4,
)

SPECTRUM_PRESETS[SpectrumStyle.RADIAL_PULSE] = _make(
    SpectrumStyle.RADIAL_PULSE,
    color1=(255, 50, 100), color2=(50, 100, 255),
    sensitivity=1.1, glow=0.8, position="center",
)

SPECTRUM_PRESETS[SpectrumStyle.NEON_EQ] = _make(
    SpectrumStyle.NEON_EQ,
    color1=(0, 255, 100), color2=(255, 0, 255),
    sensitivity=1.4, glow=0.9,
)

SPECTRUM_PRESETS[SpectrumStyle.SMOOTH_BLOB] = _make(
    SpectrumStyle.SMOOTH_BLOB,
    color1=(100, 0, 255), color2=(0, 255, 200),
    sensitivity=1.0, glow=0.6, position="center", height_ratio=0.35,
)

SPECTRUM_PRESETS[SpectrumStyle.PARTICLE] = _make(
    SpectrumStyle.PARTICLE,
    color1=(255, 200, 0), color2=(255, 50, 50),
    sensitivity=1.2, glow=0.5,
)

SPECTRUM_PRESETS[SpectrumStyle.MIRROR_WAVE] = _make(
    SpectrumStyle.MIRROR_WAVE,
    color1=(0, 200, 255), color2=(255, 100, 200),
    sensitivity=1.1, glow=0.5,
)

SPECTRUM_PRESETS[SpectrumStyle.MINIMAL_BARS] = _make(
    SpectrumStyle.MINIMAL_BARS,
    color1=(200, 200, 200), color2=(100, 200, 255),
    sensitivity=1.0, glow=0.3, bar_width=2,
)

SPECTRUM_PRESETS[SpectrumStyle.CINEMATIC_GLOW] = _make(
    SpectrumStyle.CINEMATIC_GLOW,
    color1=(255, 150, 0), color2=(255, 0, 100),
    sensitivity=1.3, glow=1.0, blur=3.0,
)

SPECTRUM_PRESETS[SpectrumStyle.AUDIO_RING] = _make(
    SpectrumStyle.AUDIO_RING,
    color1=(0, 150, 255), color2=(150, 0, 255),
    sensitivity=1.0, glow=0.7, position="center", height_ratio=0.35,
)

SPECTRUM_PRESETS[SpectrumStyle.LIQUID_WAVE] = _make(
    SpectrumStyle.LIQUID_WAVE,
    color1=(0, 100, 255), color2=(0, 255, 200),
    sensitivity=1.2, glow=0.6,
)
