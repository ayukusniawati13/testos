"""Spectrum rendering engine with 12 modern visualization styles."""

import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


class SpectrumStyle:
    BAR_MODERN = "Bar Spectrum Modern"
    CIRCULAR = "Circular Spectrum"
    WAVEFORM = "Waveform Line"
    RADIAL_PULSE = "Radial Pulse"
    NEON_EQ = "Neon Equalizer"
    SMOOTH_BLOB = "Smooth Blob Spectrum"
    PARTICLE = "Particle Spectrum"
    MIRROR_WAVE = "Mirror Wave"
    MINIMAL_BARS = "Minimal Thin Bars"
    CINEMATIC_GLOW = "Cinematic Glow Spectrum"
    AUDIO_RING = "Audio Ring Spectrum"
    LIQUID_WAVE = "Liquid Wave Spectrum"

    ALL = [
        BAR_MODERN, CIRCULAR, WAVEFORM, RADIAL_PULSE, NEON_EQ,
        SMOOTH_BLOB, PARTICLE, MIRROR_WAVE, MINIMAL_BARS,
        CINEMATIC_GLOW, AUDIO_RING, LIQUID_WAVE,
    ]


class SpectrumConfig:
    def __init__(self):
        self.style: str = SpectrumStyle.BAR_MODERN
        self.sensitivity: float = 1.0
        self.height_ratio: float = 0.3
        self.position: str = "bottom"
        self.opacity: float = 0.85
        self.glow: float = 0.5
        self.blur: float = 2.0
        self.color1: tuple = (0, 200, 255)
        self.color2: tuple = (255, 0, 200)
        self.use_gradient: bool = True
        self.bar_width: int = 8
        self.bar_gap: int = 3
        self.smoothing: float = 0.3


class SpectrumEngine:
    def __init__(self, config: SpectrumConfig | None = None):
        self.config = config or SpectrumConfig()
        self._prev_bands: np.ndarray | None = None

    def render(self, width: int, height: int, bands: np.ndarray,
               beat_strength: float = 0.0) -> Image.Image:
        bands = np.clip(bands * self.config.sensitivity, 0, 1)

        if self._prev_bands is not None:
            s = self.config.smoothing
            bands = self._prev_bands * s + bands * (1 - s)
        self._prev_bands = bands.copy()

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        style = self.config.style
        if style == SpectrumStyle.BAR_MODERN:
            self._draw_bar_modern(draw, width, height, bands, beat_strength)
        elif style == SpectrumStyle.CIRCULAR:
            self._draw_circular(draw, width, height, bands, beat_strength)
        elif style == SpectrumStyle.WAVEFORM:
            self._draw_waveform(draw, width, height, bands, beat_strength)
        elif style == SpectrumStyle.RADIAL_PULSE:
            self._draw_radial_pulse(draw, width, height, bands, beat_strength)
        elif style == SpectrumStyle.NEON_EQ:
            self._draw_neon_eq(draw, width, height, bands, beat_strength)
        elif style == SpectrumStyle.SMOOTH_BLOB:
            self._draw_smooth_blob(draw, width, height, bands, beat_strength)
        elif style == SpectrumStyle.PARTICLE:
            self._draw_particle(draw, width, height, bands, beat_strength)
        elif style == SpectrumStyle.MIRROR_WAVE:
            self._draw_mirror_wave(draw, width, height, bands, beat_strength)
        elif style == SpectrumStyle.MINIMAL_BARS:
            self._draw_minimal_bars(draw, width, height, bands, beat_strength)
        elif style == SpectrumStyle.CINEMATIC_GLOW:
            self._draw_cinematic_glow(draw, width, height, bands, beat_strength)
        elif style == SpectrumStyle.AUDIO_RING:
            self._draw_audio_ring(draw, width, height, bands, beat_strength)
        elif style == SpectrumStyle.LIQUID_WAVE:
            self._draw_liquid_wave(draw, width, height, bands, beat_strength)

        if self.config.glow > 0:
            glow_layer = img.filter(ImageFilter.GaussianBlur(
                radius=int(self.config.blur * self.config.glow * 3)))
            base = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            base = Image.alpha_composite(base, glow_layer)
            base = Image.alpha_composite(base, img)
            img = base

        if self.config.opacity < 1.0:
            alpha = img.split()[3]
            alpha = alpha.point(lambda p: int(p * self.config.opacity))
            img.putalpha(alpha)

        return img

    def _get_color_at(self, t: float) -> tuple:
        if not self.config.use_gradient:
            return self.config.color1 + (255,)
        c1 = self.config.color1
        c2 = self.config.color2
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        return (r, g, b, 255)

    def _get_y_offset(self, height: int, spec_height: int) -> int:
        pos = self.config.position
        if pos == "bottom":
            return height - spec_height
        elif pos == "top":
            return 0
        elif pos == "center":
            return (height - spec_height) // 2
        return height - spec_height

    def _draw_bar_modern(self, draw: ImageDraw.Draw, w: int, h: int,
                         bands: np.ndarray, beat: float) -> None:
        n = len(bands)
        spec_h = int(h * self.config.height_ratio)
        y_off = self._get_y_offset(h, spec_h)
        total_bar = self.config.bar_width + self.config.bar_gap
        start_x = (w - n * total_bar) // 2

        for i, val in enumerate(bands):
            bar_h = int(val * spec_h * (1 + beat * 0.3))
            bar_h = max(2, bar_h)
            x = start_x + i * total_bar
            y = y_off + spec_h - bar_h
            color = self._get_color_at(i / max(1, n - 1))
            rx, ry = 3, 3
            draw.rounded_rectangle(
                [x, y, x + self.config.bar_width, y_off + spec_h],
                radius=rx, fill=color
            )

    def _draw_circular(self, draw: ImageDraw.Draw, w: int, h: int,
                       bands: np.ndarray, beat: float) -> None:
        cx, cy = w // 2, h // 2
        base_r = min(w, h) * 0.15
        max_r = min(w, h) * self.config.height_ratio * 0.5
        n = len(bands)

        for i, val in enumerate(bands):
            angle = (2 * math.pi * i) / n - math.pi / 2
            r_inner = base_r * (1 + beat * 0.1)
            r_outer = r_inner + val * max_r * (1 + beat * 0.2)
            x1 = cx + math.cos(angle) * r_inner
            y1 = cy + math.sin(angle) * r_inner
            x2 = cx + math.cos(angle) * r_outer
            y2 = cy + math.sin(angle) * r_outer
            color = self._get_color_at(i / max(1, n - 1))
            draw.line([(x1, y1), (x2, y2)], fill=color, width=3)

    def _draw_waveform(self, draw: ImageDraw.Draw, w: int, h: int,
                       bands: np.ndarray, beat: float) -> None:
        n = len(bands)
        spec_h = int(h * self.config.height_ratio)
        y_off = self._get_y_offset(h, spec_h)
        mid_y = y_off + spec_h // 2
        points = []
        for i, val in enumerate(bands):
            x = int(w * i / max(1, n - 1))
            amp = val * (spec_h // 2) * (1 + beat * 0.2)
            y = mid_y - int(amp * math.sin(i * 0.3))
            points.append((x, y))
        if len(points) >= 2:
            color = self._get_color_at(0.5)
            draw.line(points, fill=color, width=3)

    def _draw_radial_pulse(self, draw: ImageDraw.Draw, w: int, h: int,
                           bands: np.ndarray, beat: float) -> None:
        cx, cy = w // 2, h // 2
        avg = float(np.mean(bands))
        base_r = min(w, h) * 0.1
        n_rings = 5
        for ring in range(n_rings):
            t = ring / max(1, n_rings - 1)
            r = base_r + avg * min(w, h) * 0.25 * (1 + ring * 0.4) * (1 + beat * 0.3)
            color = self._get_color_at(t)
            alpha = max(40, int(200 - ring * 35))
            c = (color[0], color[1], color[2], alpha)
            bbox = [cx - r, cy - r, cx + r, cy + r]
            draw.ellipse(bbox, outline=c, width=2)

    def _draw_neon_eq(self, draw: ImageDraw.Draw, w: int, h: int,
                      bands: np.ndarray, beat: float) -> None:
        n = len(bands)
        spec_h = int(h * self.config.height_ratio)
        y_off = self._get_y_offset(h, spec_h)
        bar_w = max(2, w // (n * 2))
        gap = bar_w // 2
        total = bar_w + gap
        start_x = (w - n * total) // 2
        n_segments = 10

        for i, val in enumerate(bands):
            bar_h = int(val * spec_h * (1 + beat * 0.3))
            seg_h = max(1, bar_h // n_segments)
            x = start_x + i * total
            for s in range(n_segments):
                seg_y = y_off + spec_h - (s + 1) * (seg_h + 2)
                if seg_y < y_off + spec_h - bar_h:
                    break
                t = s / max(1, n_segments - 1)
                color = self._get_color_at(t)
                draw.rectangle([x, seg_y, x + bar_w, seg_y + seg_h], fill=color)

    def _draw_smooth_blob(self, draw: ImageDraw.Draw, w: int, h: int,
                          bands: np.ndarray, beat: float) -> None:
        cx, cy = w // 2, h // 2
        base_r = min(w, h) * 0.15
        n = max(len(bands), 36)
        sub = np.interp(np.linspace(0, len(bands) - 1, n),
                        np.arange(len(bands)), bands)
        points = []
        for i in range(n):
            angle = 2 * math.pi * i / n
            r = base_r + sub[i] * min(w, h) * self.config.height_ratio * 0.3 * (1 + beat * 0.2)
            x = cx + math.cos(angle) * r
            y = cy + math.sin(angle) * r
            points.append((x, y))
        if len(points) >= 3:
            color = self._get_color_at(0.3)
            draw.polygon(points, fill=(*color[:3], 100), outline=color)

    def _draw_particle(self, draw: ImageDraw.Draw, w: int, h: int,
                       bands: np.ndarray, beat: float) -> None:
        n = len(bands)
        spec_h = int(h * self.config.height_ratio)
        y_off = self._get_y_offset(h, spec_h)
        rng = np.random.RandomState(42)

        for i, val in enumerate(bands):
            n_particles = max(1, int(val * 8))
            for _ in range(n_particles):
                x = int(w * i / max(1, n - 1)) + rng.randint(-10, 11)
                y = y_off + spec_h - int(val * spec_h * rng.random() * (1 + beat * 0.3))
                r = max(1, int(val * 4))
                color = self._get_color_at(i / max(1, n - 1))
                alpha = max(80, int(255 * val))
                c = (color[0], color[1], color[2], alpha)
                draw.ellipse([x - r, y - r, x + r, y + r], fill=c)

    def _draw_mirror_wave(self, draw: ImageDraw.Draw, w: int, h: int,
                          bands: np.ndarray, beat: float) -> None:
        n = len(bands)
        spec_h = int(h * self.config.height_ratio)
        y_off = self._get_y_offset(h, spec_h)
        mid_y = y_off + spec_h // 2

        top_pts = []
        bot_pts = []
        for i, val in enumerate(bands):
            x = int(w * i / max(1, n - 1))
            amp = val * (spec_h // 2) * (1 + beat * 0.25)
            top_pts.append((x, mid_y - int(amp)))
            bot_pts.append((x, mid_y + int(amp)))

        if len(top_pts) >= 2:
            c1 = self._get_color_at(0.3)
            c2 = self._get_color_at(0.7)
            draw.line(top_pts, fill=c1, width=3)
            draw.line(bot_pts, fill=c2, width=3)

    def _draw_minimal_bars(self, draw: ImageDraw.Draw, w: int, h: int,
                           bands: np.ndarray, beat: float) -> None:
        n = len(bands)
        spec_h = int(h * self.config.height_ratio)
        y_off = self._get_y_offset(h, spec_h)
        bar_w = 2
        total = max(3, w // n)
        start_x = (w - n * total) // 2

        for i, val in enumerate(bands):
            bar_h = int(val * spec_h * (1 + beat * 0.2))
            bar_h = max(1, bar_h)
            x = start_x + i * total
            y = y_off + spec_h - bar_h
            color = self._get_color_at(i / max(1, n - 1))
            draw.rectangle([x, y, x + bar_w, y_off + spec_h], fill=color)

    def _draw_cinematic_glow(self, draw: ImageDraw.Draw, w: int, h: int,
                             bands: np.ndarray, beat: float) -> None:
        n = len(bands)
        spec_h = int(h * self.config.height_ratio)
        y_off = self._get_y_offset(h, spec_h)
        bar_w = max(4, w // (n + 10))
        total = bar_w + 4
        start_x = (w - n * total) // 2

        for i, val in enumerate(bands):
            bar_h = int(val * spec_h * (1 + beat * 0.35))
            bar_h = max(3, bar_h)
            x = start_x + i * total
            y = y_off + spec_h - bar_h
            color = self._get_color_at(i / max(1, n - 1))
            for g in range(3, 0, -1):
                alpha = int(60 * g / 3)
                gc = (color[0], color[1], color[2], alpha)
                draw.rectangle([x - g, y - g, x + bar_w + g, y_off + spec_h + g], fill=gc)
            draw.rectangle([x, y, x + bar_w, y_off + spec_h], fill=color)

    def _draw_audio_ring(self, draw: ImageDraw.Draw, w: int, h: int,
                         bands: np.ndarray, beat: float) -> None:
        cx, cy = w // 2, h // 2
        base_r = min(w, h) * 0.18
        ring_width = min(w, h) * self.config.height_ratio * 0.15
        n = len(bands)

        for ring_idx in range(3):
            r = base_r + ring_idx * ring_width * 1.5
            for i, val in enumerate(bands):
                angle_start = 360 * i / n
                angle_end = 360 * (i + 1) / n
                ext = val * ring_width * (1 + beat * 0.2)
                color = self._get_color_at((i + ring_idx * n // 3) / max(1, n - 1) % 1.0)
                alpha = max(60, int(200 - ring_idx * 50))
                c = (color[0], color[1], color[2], alpha)
                r_outer = r + ext
                bbox = [cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer]
                draw.arc(bbox, angle_start, angle_end, fill=c, width=max(2, int(ring_width * 0.3)))

    def _draw_liquid_wave(self, draw: ImageDraw.Draw, w: int, h: int,
                          bands: np.ndarray, beat: float) -> None:
        n = len(bands)
        spec_h = int(h * self.config.height_ratio)
        y_off = self._get_y_offset(h, spec_h)
        mid_y = y_off + spec_h // 2

        n_layers = 3
        for layer in range(n_layers):
            points = [(0, y_off + spec_h)]
            phase = layer * 1.2
            for i in range(n):
                x = int(w * i / max(1, n - 1))
                amp = bands[i] * (spec_h // 2) * (0.4 + layer * 0.3) * (1 + beat * 0.2)
                y = mid_y - int(amp * math.sin(i * 0.2 + phase))
                points.append((x, y))
            points.append((w, y_off + spec_h))

            t = layer / max(1, n_layers - 1)
            color = self._get_color_at(t)
            alpha = max(50, int(150 - layer * 40))
            c = (*color[:3], alpha)
            if len(points) >= 3:
                draw.polygon(points, fill=c)
