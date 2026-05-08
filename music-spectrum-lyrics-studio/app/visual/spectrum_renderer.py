"""
Audio spectrum visual renderer.
Supports Bar, Circular, Waveform, Neon, Modern, and Smooth Reactive styles.
"""
import math
import logging
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

logger = logging.getLogger(__name__)


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def interpolate_gradient(colors_hex, count):
    """Generate a gradient of colors."""
    colors = [hex_to_rgb(c) for c in colors_hex]
    if len(colors) == 1:
        return [colors[0]] * count
    result = []
    segments = len(colors) - 1
    per_seg = max(1, count // segments)

    for i in range(segments):
        c1, c2 = colors[i], colors[i + 1]
        seg_count = per_seg if i < segments - 1 else count - len(result)
        for j in range(seg_count):
            t = j / max(seg_count - 1, 1)
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            result.append((r, g, b))

    while len(result) < count:
        result.append(result[-1] if result else (255, 255, 255))
    return result[:count]


class SpectrumRenderer:
    """Render audio spectrum visualizations."""

    def __init__(self, width, height, style="Bar Spectrum", low_spec=False):
        self.width = width
        self.height = height
        self.style = style
        self.low_spec = low_spec
        self.settings = {
            "gradient_colors": ["#00ffff", "#ff00ff"],
            "rainbow_mode": False,
            "neon_mode": False,
            "glow": True,
            "rounded": True,
            "bar_count": 64,
            "bar_width": 8,
            "bar_spacing": 3,
            "sensitivity": 1.0,
            "bass_boost": 1.2,
            "treble_reaction": 1.0,
            "max_height": 200,
            "reflection": False,
            "beat_bounce": True,
        }
        self.position = {"x": 0.5, "y": 0.95}
        self._prev_bars = None
        self._smoothing = 0.3

    def apply_preset(self, preset_dict):
        for k, v in preset_dict.items():
            if k in self.settings:
                self.settings[k] = v

    def render(self, frame_image, spectrum_bars, beat_energy=0.0, time_sec=0.0):
        """Render spectrum onto a PIL Image."""
        if spectrum_bars is None:
            return frame_image

        if self._prev_bars is not None and len(self._prev_bars) == len(spectrum_bars):
            smoothed = self._prev_bars * self._smoothing + spectrum_bars * (1 - self._smoothing)
            self._prev_bars = smoothed
            spectrum_bars = smoothed
        else:
            self._prev_bars = spectrum_bars.copy()

        renderer = self._get_style_renderer()
        return renderer(frame_image, spectrum_bars, beat_energy, time_sec)

    def _get_style_renderer(self):
        renderers = {
            "Bar Spectrum": self._render_bar,
            "Circular Spectrum": self._render_circular,
            "Waveform": self._render_waveform,
            "Neon Spectrum": self._render_neon,
            "Modern Visualizer": self._render_modern,
            "Smooth Reactive Spectrum": self._render_smooth_reactive,
        }
        return renderers.get(self.style, self._render_bar)

    def _get_bar_colors(self, count, time_sec=0.0):
        if self.settings["rainbow_mode"]:
            rainbow = []
            for i in range(count):
                hue = (i / count + time_sec * 0.1) % 1.0
                r, g, b = self._hsv_to_rgb(hue, 1.0, 1.0)
                rainbow.append((int(r * 255), int(g * 255), int(b * 255)))
            return rainbow
        return interpolate_gradient(self.settings["gradient_colors"], count)

    def _hsv_to_rgb(self, h, s, v):
        if s == 0.0:
            return v, v, v
        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        i = i % 6
        if i == 0: return v, t, p
        if i == 1: return q, v, p
        if i == 2: return p, v, t
        if i == 3: return p, q, v
        if i == 4: return t, p, v
        return v, p, q

    def _render_bar(self, img, bars, beat_energy, time_sec):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        s = self.settings
        bar_count = len(bars)
        bar_w = s["bar_width"]
        spacing = s["bar_spacing"]
        max_h = s["max_height"]
        rounded = s["rounded"]
        bounce = s.get("beat_bounce", True)

        total_w = bar_count * (bar_w + spacing) - spacing
        base_x = int(self.position["x"] * self.width - total_w / 2)
        base_y = int(self.position["y"] * self.height)

        colors = self._get_bar_colors(bar_count, time_sec)

        bounce_offset = int(beat_energy * 10) if bounce else 0

        for i, val in enumerate(bars):
            h = int(val * max_h) + bounce_offset
            h = max(2, min(h, max_h + 20))
            x = base_x + i * (bar_w + spacing)
            y = base_y - h

            color = colors[i] + (230,)

            if rounded and bar_w > 3:
                radius = min(bar_w // 2, 4)
                draw.rounded_rectangle([x, y, x + bar_w, base_y], radius=radius, fill=color)
            else:
                draw.rectangle([x, y, x + bar_w, base_y], fill=color)

        if s.get("reflection", False) and not self.low_spec:
            ref_overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ref_draw = ImageDraw.Draw(ref_overlay)
            for i, val in enumerate(bars):
                h = int(val * max_h * 0.3)
                x = base_x + i * (bar_w + spacing)
                y = base_y
                color = colors[i] + (80,)
                ref_draw.rectangle([x, y, x + bar_w, y + h], fill=color)
            overlay = Image.alpha_composite(overlay, ref_overlay)

        if s.get("glow", False) and not self.low_spec:
            glow = overlay.filter(ImageFilter.GaussianBlur(radius=6))
            glow_data = np.array(glow)
            glow_data[:, :, 3] = (glow_data[:, :, 3] * 0.4).astype(np.uint8)
            glow = Image.fromarray(glow_data)
            result = Image.alpha_composite(img.convert("RGBA"), glow)
            result = Image.alpha_composite(result, overlay)
            return result

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_circular(self, img, bars, beat_energy, time_sec):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        cx = int(self.position["x"] * self.width)
        cy = int(self.position["y"] * self.height) - 100
        base_r = 80 + int(beat_energy * 15)
        max_h = self.settings["max_height"]
        colors = self._get_bar_colors(len(bars), time_sec)
        bar_w = max(2, self.settings["bar_width"] // 2)

        for i, val in enumerate(bars):
            angle = (2 * math.pi * i / len(bars)) - math.pi / 2
            h = int(val * max_h * 0.6)
            x1 = int(cx + base_r * math.cos(angle))
            y1 = int(cy + base_r * math.sin(angle))
            x2 = int(cx + (base_r + h) * math.cos(angle))
            y2 = int(cy + (base_r + h) * math.sin(angle))
            color = colors[i] + (220,)
            draw.line([x1, y1, x2, y2], fill=color, width=bar_w)

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_waveform(self, img, bars, beat_energy, time_sec):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        max_h = self.settings["max_height"]
        colors = self._get_bar_colors(len(bars), time_sec)
        base_y = int(self.position["y"] * self.height)
        total_w = int(self.width * 0.8)
        start_x = int(self.width * 0.1)

        points_top = []
        points_bot = []
        for i, val in enumerate(bars):
            x = start_x + int(i * total_w / len(bars))
            h = int(val * max_h * 0.5)
            points_top.append((x, base_y - h))
            points_bot.append((x, base_y + h))

        for i in range(len(points_top) - 1):
            color = colors[i] + (200,)
            draw.line([points_top[i], points_top[i + 1]], fill=color, width=3)
            draw.line([points_bot[i], points_bot[i + 1]], fill=color, width=2)

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_neon(self, img, bars, beat_energy, time_sec):
        self.settings["neon_mode"] = True
        self.settings["glow"] = True
        return self._render_bar(img, bars, beat_energy, time_sec)

    def _render_modern(self, img, bars, beat_energy, time_sec):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        bar_count = len(bars)
        max_h = self.settings["max_height"]
        colors = self._get_bar_colors(bar_count, time_sec)
        base_y = int(self.position["y"] * self.height)
        bar_w = max(3, self.width // (bar_count * 2))
        spacing = bar_w // 2
        total_w = bar_count * (bar_w + spacing)
        start_x = int(self.width / 2 - total_w / 2)

        for i, val in enumerate(bars):
            h = int(val * max_h)
            x = start_x + i * (bar_w + spacing)
            segments = max(1, h // 6)
            for s in range(segments):
                sy = base_y - (s + 1) * 6
                alpha = int(230 * (1 - s / max(segments, 1) * 0.3))
                color = colors[i] + (alpha,)
                draw.rectangle([x, sy, x + bar_w, sy + 4], fill=color)

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_smooth_reactive(self, img, bars, beat_energy, time_sec):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        max_h = self.settings["max_height"]
        base_y = int(self.position["y"] * self.height)
        total_w = int(self.width * 0.85)
        start_x = int(self.width * 0.075)
        colors = self._get_bar_colors(len(bars), time_sec)

        points = [(start_x, base_y)]
        for i, val in enumerate(bars):
            x = start_x + int(i * total_w / len(bars))
            h = int(val * max_h * 0.7)
            points.append((x, base_y - h))
        points.append((start_x + total_w, base_y))

        if len(points) >= 3:
            fill_color = colors[len(colors) // 2] + (100,)
            draw.polygon(points, fill=fill_color)
            for i in range(len(points) - 1):
                ci = min(i, len(colors) - 1)
                line_color = colors[ci] + (220,)
                draw.line([points[i], points[i + 1]], fill=line_color, width=2)

        return Image.alpha_composite(img.convert("RGBA"), overlay)
