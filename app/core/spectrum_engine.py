"""Spectrum visualisation rendering.

Each :class:`SpectrumStyle` knows how to draw a single frame given a band
vector + reactive features (energy, bass, mid, treble, beat-pulse). All
styles share the same configuration / position / colour pipeline so they can
be hot-swapped from the GUI.

The module is GUI/Qt-free -- it only depends on Pillow + numpy. The render
engine feeds frames produced here into FFmpeg.
"""
from __future__ import annotations

import colorsys
import math
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFilter

RGBA = Tuple[int, int, int, int]


SUPPORTED_STYLES: Tuple[str, ...] = (
    "bar",
    "circular",
    "wave",
    "radial",
    "particle",
    "glow",
)
SUPPORTED_COLOR_MODES: Tuple[str, ...] = (
    "gradient",
    "neon",
    "rainbow",
    "custom",
    "auto",
)
ANCHOR_OFFSETS: Dict[str, Tuple[float, float]] = {
    "top_left": (0.0, 0.0),
    "top": (0.5, 0.0),
    "top_right": (1.0, 0.0),
    "left": (0.0, 0.5),
    "center": (0.5, 0.5),
    "right": (1.0, 0.5),
    "bottom_left": (0.0, 1.0),
    "bottom": (0.5, 1.0),
    "bottom_right": (1.0, 1.0),
}


@dataclass
class SpectrumEffects:
    glow: bool = True
    blur: bool = False
    shadow: bool = True
    pulse: bool = True
    particle: bool = False
    reflection: bool = False


@dataclass
class SpectrumConfig:
    """User-facing spectrum styling parameters."""

    style: str = "bar"
    color_mode: str = "gradient"
    primary_color: str = "#7c5cff"
    secondary_color: str = "#21d4fd"
    bar_count: int = 64
    smoothing: float = 0.6
    x: float = 0.5
    y: float = 0.85
    scale: float = 1.0
    rotation: float = 0.0
    opacity: float = 1.0
    anchor: str = "center"
    effects: SpectrumEffects = field(default_factory=SpectrumEffects)
    custom_palette: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict) -> "SpectrumConfig":
        effects_data = data.get("effects") or {}
        effects = SpectrumEffects(
            glow=bool(effects_data.get("glow", True)),
            blur=bool(effects_data.get("blur", False)),
            shadow=bool(effects_data.get("shadow", True)),
            pulse=bool(effects_data.get("pulse", True)),
            particle=bool(effects_data.get("particle", False)),
            reflection=bool(effects_data.get("reflection", False)),
        )
        return cls(
            style=str(data.get("style", "bar")),
            color_mode=str(data.get("color_mode", "gradient")),
            primary_color=str(data.get("primary_color", "#7c5cff")),
            secondary_color=str(data.get("secondary_color", "#21d4fd")),
            bar_count=int(data.get("bar_count", 64)),
            smoothing=float(data.get("smoothing", 0.6)),
            x=float(data.get("x", 0.5)),
            y=float(data.get("y", 0.85)),
            scale=float(data.get("scale", 1.0)),
            rotation=float(data.get("rotation", 0.0)),
            opacity=float(data.get("opacity", 1.0)),
            anchor=str(data.get("anchor", "center")),
            effects=effects,
            custom_palette=list(data.get("custom_palette") or []),
        )


@dataclass
class FrameContext:
    """Per-frame inputs handed to a :class:`SpectrumStyle`."""

    bands: Sequence[float]  # length = config.bar_count, values in [0, 1]
    energy: float
    bass: float
    mid: float
    treble: float
    beat_pulse: float  # 0..1, decays after each beat
    width: int
    height: int
    time: float


def hex_to_rgba(value: str, alpha: int = 255) -> RGBA:
    s = value.lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) == 6:
        r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
        return r, g, b, alpha
    if len(s) == 8:
        r, g, b, a = (int(s[i : i + 2], 16) for i in (0, 2, 4, 6))
        return r, g, b, a
    raise ValueError(f"Invalid color literal: {value!r}")


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_color(c1: RGBA, c2: RGBA, t: float) -> RGBA:
    return (
        int(round(lerp(c1[0], c2[0], t))),
        int(round(lerp(c1[1], c2[1], t))),
        int(round(lerp(c1[2], c2[2], t))),
        int(round(lerp(c1[3], c2[3], t))),
    )


def _resolve_palette(cfg: SpectrumConfig, n: int) -> List[RGBA]:
    """Return ``n`` colours according to the configured color mode."""
    primary = hex_to_rgba(cfg.primary_color)
    secondary = hex_to_rgba(cfg.secondary_color)
    palette: List[RGBA] = []
    if cfg.color_mode == "rainbow":
        for i in range(n):
            hue = (i / max(1, n - 1)) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 0.85, 1.0)
            palette.append((int(r * 255), int(g * 255), int(b * 255), 255))
    elif cfg.color_mode == "neon":
        # Pulsing neon between primary and a brighter complement.
        bright = _brighten(primary, 0.4)
        for i in range(n):
            t = 0.5 + 0.5 * math.sin(i * math.pi * 2 / max(1, n))
            palette.append(lerp_color(primary, bright, t))
    elif cfg.color_mode == "custom" and cfg.custom_palette:
        stops = [hex_to_rgba(c) for c in cfg.custom_palette]
        for i in range(n):
            t = i / max(1, n - 1)
            palette.append(_sample_gradient(stops, t))
    elif cfg.color_mode == "auto":
        # Auto = same as gradient for now; the render engine may override the
        # secondary colour using a sampled background palette.
        for i in range(n):
            t = i / max(1, n - 1)
            palette.append(lerp_color(primary, secondary, t))
    else:  # gradient (default)
        for i in range(n):
            t = i / max(1, n - 1)
            palette.append(lerp_color(primary, secondary, t))
    return palette


def _brighten(color: RGBA, amount: float) -> RGBA:
    h, l, s = colorsys.rgb_to_hls(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
    l = max(0.0, min(1.0, l + amount))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return int(r * 255), int(g * 255), int(b * 255), color[3]


def _sample_gradient(stops: List[RGBA], t: float) -> RGBA:
    if not stops:
        return (255, 255, 255, 255)
    if len(stops) == 1:
        return stops[0]
    pos = t * (len(stops) - 1)
    idx = int(pos)
    frac = pos - idx
    if idx >= len(stops) - 1:
        return stops[-1]
    return lerp_color(stops[idx], stops[idx + 1], frac)


# ----------------------------------------------------------------- positioning


def anchored_offset(width: int, height: int, anchor: str) -> Tuple[int, int]:
    ax, ay = ANCHOR_OFFSETS.get(anchor, (0.5, 0.5))
    return int(width * ax), int(height * ay)


# ----------------------------------------------------------------- styles


StyleRenderer = Callable[[ImageDraw.ImageDraw, SpectrumConfig, FrameContext, List[RGBA]], None]


def _draw_bar(draw: ImageDraw.ImageDraw, cfg: SpectrumConfig, ctx: FrameContext, palette: List[RGBA]) -> None:
    n = len(ctx.bands)
    if n == 0:
        return
    canvas_w = ctx.width
    canvas_h = ctx.height
    bar_w = max(2.0, canvas_w / (n * 1.6))
    spacing = (canvas_w - bar_w * n) / max(1, n - 1) if n > 1 else 0
    base_y = canvas_h * 0.5  # local coordinates: spectrum drawn in its own canvas
    max_height = canvas_h * 0.4

    pulse = 1.0 + (0.15 * ctx.beat_pulse if cfg.effects.pulse else 0.0)
    for i, value in enumerate(ctx.bands):
        h = max(2.0, value * max_height * pulse)
        x0 = i * (bar_w + spacing)
        y0 = base_y - h
        y1 = base_y + 1
        color = palette[i % len(palette)]
        draw.rounded_rectangle(
            [x0, y0, x0 + bar_w, y1],
            radius=int(bar_w / 2),
            fill=color,
        )
        if cfg.effects.reflection:
            mirror = lerp_color(color, (0, 0, 0, 0), 0.7)
            draw.rounded_rectangle(
                [x0, base_y + 2, x0 + bar_w, base_y + h * 0.5 + 2],
                radius=int(bar_w / 2),
                fill=mirror,
            )


def _draw_circular(draw: ImageDraw.ImageDraw, cfg: SpectrumConfig, ctx: FrameContext, palette: List[RGBA]) -> None:
    n = len(ctx.bands)
    if n == 0:
        return
    cx = ctx.width / 2
    cy = ctx.height / 2
    radius = min(ctx.width, ctx.height) * 0.28
    bar_len = min(ctx.width, ctx.height) * 0.18
    pulse = 1.0 + (0.2 * ctx.beat_pulse if cfg.effects.pulse else 0.0)

    # Inner ring outline.
    ring = palette[0]
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=(ring[0], ring[1], ring[2], 110),
        width=2,
    )

    for i, value in enumerate(ctx.bands):
        angle = (i / n) * math.tau - math.pi / 2
        length = bar_len * (0.4 + 0.6 * value) * pulse
        x1 = cx + math.cos(angle) * radius
        y1 = cy + math.sin(angle) * radius
        x2 = cx + math.cos(angle) * (radius + length)
        y2 = cy + math.sin(angle) * (radius + length)
        color = palette[i % len(palette)]
        draw.line([x1, y1, x2, y2], fill=color, width=max(2, int(ctx.width / 320)))


def _draw_wave(draw: ImageDraw.ImageDraw, cfg: SpectrumConfig, ctx: FrameContext, palette: List[RGBA]) -> None:
    n = len(ctx.bands)
    if n < 2:
        return
    width, height = ctx.width, ctx.height
    middle = height / 2
    amp = height * 0.4 * (0.6 + 0.4 * ctx.energy)
    points: List[Tuple[float, float]] = []
    for i, value in enumerate(ctx.bands):
        x = (i / (n - 1)) * width
        sin_y = math.sin((i / n) * math.tau * 2 + ctx.time * 4) * amp * 0.25
        y = middle - value * amp + sin_y
        points.append((x, y))

    color = palette[len(palette) // 2]
    draw.line(points, fill=color, width=max(3, int(width / 240)))
    if cfg.effects.reflection:
        reflect = lerp_color(color, (0, 0, 0, 0), 0.6)
        mirror_points = [(x, height - y) for x, y in points]
        draw.line(mirror_points, fill=reflect, width=max(2, int(width / 320)))


def _draw_radial(draw: ImageDraw.ImageDraw, cfg: SpectrumConfig, ctx: FrameContext, palette: List[RGBA]) -> None:
    n = len(ctx.bands)
    if n == 0:
        return
    cx = ctx.width / 2
    cy = ctx.height / 2
    base_radius = min(ctx.width, ctx.height) * 0.18
    pulse = 1.0 + (0.25 * ctx.beat_pulse if cfg.effects.pulse else 0.0)
    for i, value in enumerate(ctx.bands):
        angle = (i / n) * math.tau
        r = base_radius + value * min(ctx.width, ctx.height) * 0.32 * pulse
        x = cx + math.cos(angle) * r
        y = cy + math.sin(angle) * r
        size = max(3, int(value * ctx.width / 60 + 2))
        color = palette[i % len(palette)]
        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)


def _draw_particle(
    draw: ImageDraw.ImageDraw, cfg: SpectrumConfig, ctx: FrameContext, palette: List[RGBA]
) -> None:
    rng = random.Random(int(ctx.time * 60))
    width, height = ctx.width, ctx.height
    n_particles = 60 + int(60 * ctx.energy)
    for i in range(n_particles):
        x = rng.uniform(0, width)
        y = rng.uniform(0, height)
        radius = rng.uniform(1.0, 4.0) + ctx.beat_pulse * 4.0
        color = palette[i % len(palette)]
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)


def _draw_glow(
    draw: ImageDraw.ImageDraw, cfg: SpectrumConfig, ctx: FrameContext, palette: List[RGBA]
) -> None:
    cx = ctx.width / 2
    cy = ctx.height / 2
    base = min(ctx.width, ctx.height) * 0.25
    radius = base * (1.0 + 0.6 * ctx.energy + 0.4 * ctx.beat_pulse)
    for ring in range(6, 0, -1):
        alpha = int(180 * (ring / 6) * (0.4 + 0.6 * ctx.energy))
        color = list(palette[ring % len(palette)])
        color[3] = alpha
        r = radius * (ring / 6)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(color))


_STYLE_RENDERERS: Dict[str, StyleRenderer] = {
    "bar": _draw_bar,
    "circular": _draw_circular,
    "wave": _draw_wave,
    "radial": _draw_radial,
    "particle": _draw_particle,
    "glow": _draw_glow,
}


# ------------------------------------------------------------------ engine


class SpectrumEngine:
    """High-level facade used by the render engine."""

    def __init__(self, config: SpectrumConfig) -> None:
        self.config = config
        self._beat_decay = 0.0
        self._previous_bands: Optional[List[float]] = None

    @property
    def config_dict(self) -> Dict:
        return {
            "style": self.config.style,
            "color_mode": self.config.color_mode,
            "primary_color": self.config.primary_color,
            "secondary_color": self.config.secondary_color,
            "bar_count": self.config.bar_count,
            "smoothing": self.config.smoothing,
            "x": self.config.x,
            "y": self.config.y,
            "scale": self.config.scale,
            "rotation": self.config.rotation,
            "opacity": self.config.opacity,
            "anchor": self.config.anchor,
            "effects": vars(self.config.effects),
        }

    def update_beat(self, beat_active: bool, dt: float) -> float:
        """Track a beat envelope used by reactive styles. Returns its value."""
        if beat_active:
            self._beat_decay = 1.0
        else:
            self._beat_decay = max(0.0, self._beat_decay - dt * 2.5)
        return self._beat_decay

    def render_frame(
        self,
        size: Tuple[int, int],
        bands: Sequence[float],
        energy: float,
        bass: float,
        mid: float,
        treble: float,
        beat_pulse: float,
        time: float,
    ) -> Image.Image:
        """Render an RGBA layer the same size as the output canvas."""
        width, height = size

        # Local canvas dedicated to the spectrum, scaled and rotated later.
        local_w = max(64, int(width * 0.85 * self.config.scale))
        local_h = max(64, int(height * 0.45 * self.config.scale))
        local = Image.new("RGBA", (local_w, local_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(local, "RGBA")

        ctx = FrameContext(
            bands=self._smooth_bands(bands),
            energy=float(energy),
            bass=float(bass),
            mid=float(mid),
            treble=float(treble),
            beat_pulse=float(beat_pulse),
            width=local_w,
            height=local_h,
            time=time,
        )
        palette = _resolve_palette(self.config, max(8, self.config.bar_count))

        renderer = _STYLE_RENDERERS.get(self.config.style, _draw_bar)
        renderer(draw, self.config, ctx, palette)

        # Effects pipeline (order matters: blur first, glow on top, shadow under).
        layer = local
        if self.config.effects.blur:
            layer = layer.filter(ImageFilter.GaussianBlur(radius=2))
        if self.config.effects.glow:
            glow = layer.filter(ImageFilter.GaussianBlur(radius=8))
            layer = Image.alpha_composite(glow, layer)
        if self.config.effects.shadow:
            shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
            shadow.paste((0, 0, 0, 140), mask=layer.split()[3])
            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=6))
            shifted = Image.new("RGBA", layer.size, (0, 0, 0, 0))
            shifted.paste(shadow, (4, 6))
            layer = Image.alpha_composite(shifted, layer)

        # Rotation.
        if abs(self.config.rotation) > 0.001:
            layer = layer.rotate(self.config.rotation, expand=True, resample=Image.BICUBIC)

        # Opacity.
        if self.config.opacity < 0.999:
            alpha = layer.split()[3].point(lambda v: int(v * self.config.opacity))
            layer.putalpha(alpha)

        # Compose onto the final canvas at the configured (x, y) anchor.
        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        ax, ay = ANCHOR_OFFSETS.get(self.config.anchor, (0.5, 0.5))
        cx = int(width * self.config.x - layer.width * ax)
        cy = int(height * self.config.y - layer.height * ay)
        canvas.alpha_composite(layer, (cx, cy))
        return canvas

    # -------------------------------------------------------------- helpers

    def _smooth_bands(self, bands: Sequence[float]) -> List[float]:
        bands_list = [max(0.0, min(1.0, float(v))) for v in bands]
        if self._previous_bands is None or len(self._previous_bands) != len(bands_list):
            self._previous_bands = bands_list[:]
            return bands_list
        smoothing = max(0.0, min(0.95, self.config.smoothing))
        out: List[float] = []
        for prev, current in zip(self._previous_bands, bands_list):
            out.append(prev * smoothing + current * (1 - smoothing))
        self._previous_bands = out
        return out


def list_styles() -> List[str]:
    return list(SUPPORTED_STYLES)


def list_color_modes() -> List[str]:
    return list(SUPPORTED_COLOR_MODES)


def is_style(value: str) -> bool:
    return value in SUPPORTED_STYLES


__all__ = [
    "SpectrumConfig",
    "SpectrumEffects",
    "SpectrumEngine",
    "FrameContext",
    "SUPPORTED_STYLES",
    "SUPPORTED_COLOR_MODES",
    "list_styles",
    "list_color_modes",
    "is_style",
    "hex_to_rgba",
]
