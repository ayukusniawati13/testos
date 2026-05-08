"""
Karaoke visual effects renderer for all 20 karaoke modes.
Renders lyrics onto video frames using PIL/Pillow.
"""
import math
import logging
from PIL import Image, ImageDraw, ImageFont, ImageFilter

logger = logging.getLogger(__name__)


def get_font(family="Arial", size=42, bold=False):
    """Load a font, falling back to default."""
    try:
        font_path = None
        import os
        font_dirs = [
            "/usr/share/fonts",
            "C:/Windows/Fonts",
            os.path.expanduser("~/.fonts"),
        ]
        for fd in font_dirs:
            if os.path.isdir(fd):
                for root, dirs, files in os.walk(fd):
                    for f in files:
                        if family.lower() in f.lower() and f.endswith((".ttf", ".otf")):
                            font_path = os.path.join(root, f)
                            break
                    if font_path:
                        break
            if font_path:
                break

        if font_path:
            return ImageFont.truetype(font_path, size)
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except Exception:
            return ImageFont.load_default()


def hex_to_rgba(hex_color, alpha=255):
    """Convert hex color to RGBA tuple."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, alpha)


def lerp_color(c1, c2, t):
    """Linearly interpolate between two RGBA colors."""
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


class KaraokeRenderer:
    """Render karaoke effects onto frames."""

    def __init__(self, width, height, low_spec=False):
        self.width = width
        self.height = height
        self.low_spec = low_spec

    def render(self, frame_image, display_data, beat_energy=0.0):
        """Render karaoke effect onto a PIL Image."""
        if display_data is None:
            return frame_image

        mode = display_data["mode"]
        renderer = self._get_mode_renderer(mode)
        return renderer(frame_image, display_data, beat_energy)

    def _get_mode_renderer(self, mode):
        renderers = {
            "Normal Lyrics": self._render_normal,
            "Karaoke Line Highlight": self._render_line_highlight,
            "Karaoke Word Highlight": self._render_word_highlight,
            "Karaoke Smooth Sweep": self._render_smooth_sweep,
            "Karaoke Bounce Mode": self._render_bounce,
            "Karaoke Neon Glow Mode": self._render_neon_glow,
            "Karaoke Gradient Flow": self._render_gradient_flow,
            "Karaoke Beat Reactive": self._render_beat_reactive,
            "Karaoke Typewriter Mode": self._render_typewriter,
            "Karaoke Slide Reveal": self._render_slide_reveal,
            "Karaoke Wave Mode": self._render_wave,
            "Karaoke Pulse Mode": self._render_pulse,
            "Karaoke Cinematic Mode": self._render_cinematic,
            "Karaoke Split Lyrics Mode": self._render_split,
            "Karaoke Vertical Lyrics Mode": self._render_vertical,
            "Karaoke Floating Lyrics": self._render_floating,
            "Karaoke Subtitle Professional": self._render_subtitle_pro,
            "Karaoke Dynamic Zoom": self._render_dynamic_zoom,
            "Karaoke Multi Color Reactive": self._render_multi_color,
            "Karaoke Fire/Particle Mode": self._render_fire_particle,
        }
        return renderers.get(mode, self._render_normal)

    def _get_text_params(self, settings):
        font = get_font(settings.get("font_family", "Arial"), settings.get("font_size", 42))
        normal_color = hex_to_rgba(settings.get("normal_color", "#888888"))
        highlight_color = hex_to_rgba(settings.get("highlight_color", "#ffffff"))
        outline_color = hex_to_rgba(settings.get("outline_color", "#000000"))
        outline_w = settings.get("outline_thickness", 2)
        return font, normal_color, highlight_color, outline_color, outline_w

    def _draw_outlined_text(self, draw, x, y, text, font, fill, outline_color, outline_w):
        for dx in range(-outline_w, outline_w + 1):
            for dy in range(-outline_w, outline_w + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        draw.text((x, y), text, font=font, fill=fill)

    def _get_text_position(self, position, text_width, text_height):
        x = int(position.get("x", 0.5) * self.width - text_width / 2)
        y = int(position.get("y", 0.75) * self.height - text_height / 2)
        return x, y

    def _render_normal(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        font, normal_color, _, outline_color, outline_w = self._get_text_params(settings)
        line = data["current_line"]
        if not line:
            return img

        bbox = draw.textbbox((0, 0), line.text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = self._get_text_position(data["position"], tw, th)
        self._draw_outlined_text(draw, x, y, line.text, font, normal_color, outline_color, outline_w)
        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_line_highlight(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        font, normal_color, highlight_color, outline_color, outline_w = self._get_text_params(settings)
        line = data["current_line"]
        if not line:
            return img

        lines_to_show = []
        if data.get("prev_line"):
            lines_to_show.append((data["prev_line"].text, normal_color))
        lines_to_show.append((line.text, highlight_color))
        if data.get("next_line"):
            lines_to_show.append((data["next_line"].text, normal_color))

        line_height = settings.get("font_size", 42) * settings.get("line_spacing", 1.4)
        total_h = line_height * len(lines_to_show)
        base_y = data["position"].get("y", 0.75) * self.height - total_h / 2

        for i, (text, color) in enumerate(lines_to_show):
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            x = int(data["position"].get("x", 0.5) * self.width - tw / 2)
            y = int(base_y + i * line_height)
            self._draw_outlined_text(draw, x, y, text, font, color, outline_color, outline_w)

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_word_highlight(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        font, normal_color, highlight_color, outline_color, outline_w = self._get_text_params(settings)
        line = data["current_line"]
        if not line or not line.words:
            return self._render_normal(img, data, beat_energy)

        active_idx = data["active_word_index"]
        full_text = " ".join(w.text for w in line.words)
        bbox = draw.textbbox((0, 0), full_text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        start_x, y = self._get_text_position(data["position"], tw, th)
        current_x = start_x

        for i, word in enumerate(line.words):
            color = highlight_color if i <= active_idx else normal_color
            word_text = word.text + " "
            self._draw_outlined_text(draw, current_x, y, word_text, font, color, outline_color, outline_w)
            bbox = draw.textbbox((0, 0), word_text, font=font)
            current_x += bbox[2] - bbox[0]

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_smooth_sweep(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        font, normal_color, highlight_color, outline_color, outline_w = self._get_text_params(settings)
        line = data["current_line"]
        if not line:
            return img

        text = line.text
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = self._get_text_position(data["position"], tw, th)

        self._draw_outlined_text(draw, x, y, text, font, normal_color, outline_color, outline_w)

        progress = data["line_progress"]
        mask = Image.new("L", img.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        sweep_x = int(x + tw * progress)
        mask_draw.rectangle([x - 5, y - 5, sweep_x, y + th + 5], fill=255)

        highlight_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        hl_draw = ImageDraw.Draw(highlight_layer)
        self._draw_outlined_text(hl_draw, x, y, text, font, highlight_color, outline_color, outline_w)
        highlight_layer.putalpha(mask)
        overlay = Image.alpha_composite(overlay, highlight_layer)

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_bounce(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        font, normal_color, highlight_color, outline_color, outline_w = self._get_text_params(settings)
        line = data["current_line"]
        if not line or not line.words:
            return self._render_normal(img, data, beat_energy)

        active_idx = data["active_word_index"]
        full_text = " ".join(w.text for w in line.words)
        bbox = draw.textbbox((0, 0), full_text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        start_x, base_y = self._get_text_position(data["position"], tw, th)
        current_x = start_x

        for i, word in enumerate(line.words):
            bounce_offset = 0
            if i == active_idx:
                bounce_offset = int(-10 * abs(math.sin(data["word_progress"] * math.pi)))
            color = highlight_color if i == active_idx else normal_color
            word_text = word.text + " "
            self._draw_outlined_text(draw, current_x, base_y + bounce_offset, word_text, font, color, outline_color, outline_w)
            bbox = draw.textbbox((0, 0), word_text, font=font)
            current_x += bbox[2] - bbox[0]

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_neon_glow(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        settings = data["settings"]
        font, normal_color, highlight_color, outline_color, outline_w = self._get_text_params(settings)
        line = data["current_line"]
        if not line:
            return img

        result = self._render_word_highlight(img, data, beat_energy)
        if not self.low_spec and settings.get("glow_effect", True):
            glow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_layer)
            text = line.text
            bbox = glow_draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x, y = self._get_text_position(data["position"], tw, th)
            glow_color = highlight_color[:3] + (80,)
            glow_draw.text((x, y), text, font=font, fill=glow_color)
            intensity = settings.get("glow_intensity", 0.5)
            blur_radius = int(10 * intensity)
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            result = Image.alpha_composite(result.convert("RGBA"), glow_layer)
        return result

    def _render_gradient_flow(self, img, data, beat_energy):
        return self._render_smooth_sweep(img, data, beat_energy)

    def _render_beat_reactive(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        base_size = settings.get("font_size", 42)
        scale = 1.0 + beat_energy * 0.15
        font = get_font(settings.get("font_family", "Arial"), int(base_size * scale))
        _, normal_color, highlight_color, outline_color, outline_w = self._get_text_params(settings)
        line = data["current_line"]
        if not line:
            return img

        text = line.text
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = self._get_text_position(data["position"], tw, th)

        color = lerp_color(normal_color, highlight_color, beat_energy)
        self._draw_outlined_text(draw, x, y, text, font, color, outline_color, outline_w)
        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_typewriter(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        font, _, highlight_color, outline_color, outline_w = self._get_text_params(settings)
        line = data["current_line"]
        if not line:
            return img

        progress = data["line_progress"]
        chars_to_show = int(len(line.text) * progress)
        visible_text = line.text[:chars_to_show]

        bbox = draw.textbbox((0, 0), line.text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = self._get_text_position(data["position"], tw, th)
        self._draw_outlined_text(draw, x, y, visible_text, font, highlight_color, outline_color, outline_w)
        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_slide_reveal(self, img, data, beat_energy):
        return self._render_smooth_sweep(img, data, beat_energy)

    def _render_wave(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        font, normal_color, highlight_color, outline_color, outline_w = self._get_text_params(settings)
        line = data["current_line"]
        if not line:
            return img

        text = line.text
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        start_x, base_y = self._get_text_position(data["position"], tw, th)

        current_x = start_x
        time_val = data.get("time", 0)
        for i, char in enumerate(text):
            wave_offset = int(5 * math.sin(time_val * 4 + i * 0.5))
            color = highlight_color if data["line_progress"] > i / max(len(text), 1) else normal_color
            self._draw_outlined_text(draw, current_x, base_y + wave_offset, char, font, color, outline_color, outline_w)
            char_bbox = draw.textbbox((0, 0), char, font=font)
            current_x += char_bbox[2] - char_bbox[0]

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_pulse(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        base_size = settings.get("font_size", 42)
        pulse = 1.0 + 0.05 * math.sin(data.get("time", 0) * 6)
        font = get_font(settings.get("font_family", "Arial"), int(base_size * pulse))
        _, normal_color, highlight_color, outline_color, outline_w = self._get_text_params(settings)
        line = data["current_line"]
        if not line:
            return img

        text = line.text
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = self._get_text_position(data["position"], tw, th)
        alpha = int(200 + 55 * math.sin(data.get("time", 0) * 6))
        color = highlight_color[:3] + (alpha,)
        self._draw_outlined_text(draw, x, y, text, font, color, outline_color, outline_w)
        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_cinematic(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        font, _, highlight_color, outline_color, _ = self._get_text_params(settings)
        line = data["current_line"]
        if not line:
            return img

        bar_h = int(settings.get("font_size", 42) * 2.5)
        bar_y = int(data["position"].get("y", 0.75) * self.height - bar_h / 2)
        draw.rectangle([0, bar_y, self.width, bar_y + bar_h], fill=(0, 0, 0, 160))

        text = line.text
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = int(self.width / 2 - tw / 2)
        y = int(bar_y + bar_h / 2 - th / 2)
        draw.text((x, y), text, font=font, fill=highlight_color)
        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_split(self, img, data, beat_energy):
        return self._render_line_highlight(img, data, beat_energy)

    def _render_vertical(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        font, normal_color, highlight_color, outline_color, outline_w = self._get_text_params(settings)
        line = data["current_line"]
        if not line:
            return img

        x = int(data["position"].get("x", 0.5) * self.width)
        base_y = int(data["position"].get("y", 0.5) * self.height)
        char_height = settings.get("font_size", 42) + 4

        for i, char in enumerate(line.text):
            if char == " ":
                continue
            cy = base_y + i * char_height - len(line.text) * char_height // 2
            color = highlight_color if data["line_progress"] > i / max(len(line.text), 1) else normal_color
            bbox = draw.textbbox((0, 0), char, font=font)
            cw = bbox[2] - bbox[0]
            self._draw_outlined_text(draw, x - cw // 2, cy, char, font, color, outline_color, outline_w)

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_floating(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        font, _, highlight_color, outline_color, outline_w = self._get_text_params(settings)
        line = data["current_line"]
        if not line:
            return img

        time_val = data.get("time", 0)
        float_y = 3 * math.sin(time_val * 2)
        float_x = 2 * math.sin(time_val * 1.5)

        text = line.text
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = self._get_text_position(data["position"], tw, th)
        x += int(float_x)
        y += int(float_y)

        alpha = int(180 + 75 * data["line_progress"])
        color = highlight_color[:3] + (alpha,)
        self._draw_outlined_text(draw, x, y, text, font, color, outline_color, outline_w)
        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_subtitle_pro(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        font = get_font(settings.get("font_family", "Arial"), settings.get("font_size", 36))
        line = data["current_line"]
        if not line:
            return img

        text = line.text
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pad = 16
        x = int(self.width / 2 - tw / 2)
        y = int(self.height * 0.88 - th / 2)

        draw.rectangle([x - pad, y - pad // 2, x + tw + pad, y + th + pad // 2], fill=(0, 0, 0, 180))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_dynamic_zoom(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        base_size = settings.get("font_size", 42)
        _, normal_color, highlight_color, outline_color, outline_w = self._get_text_params(settings)
        line = data["current_line"]
        if not line or not line.words:
            return self._render_normal(img, data, beat_energy)

        active_idx = data["active_word_index"]
        full_text = " ".join(w.text for w in line.words)
        font_normal = get_font(settings.get("font_family", "Arial"), base_size)
        font_zoom = get_font(settings.get("font_family", "Arial"), int(base_size * 1.15))

        bbox = draw.textbbox((0, 0), full_text, font=font_normal)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        start_x, y = self._get_text_position(data["position"], tw, th)
        current_x = start_x

        for i, word in enumerate(line.words):
            is_active = i == active_idx
            font = font_zoom if is_active else font_normal
            color = highlight_color if is_active else normal_color
            word_text = word.text + " "
            y_offset = -3 if is_active else 0
            self._draw_outlined_text(draw, current_x, y + y_offset, word_text, font, color, outline_color, outline_w)
            bbox = draw.textbbox((0, 0), word_text, font=font_normal)
            current_x += bbox[2] - bbox[0]

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_multi_color(self, img, data, beat_energy):
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        settings = data["settings"]
        font, normal_color, highlight_color, outline_color, outline_w = self._get_text_params(settings)
        line = data["current_line"]
        if not line or not line.words:
            return self._render_normal(img, data, beat_energy)

        active_idx = data["active_word_index"]
        colors = [
            (255, 0, 100, 255), (0, 255, 150, 255), (100, 100, 255, 255),
            (255, 200, 0, 255), (255, 100, 0, 255), (0, 200, 255, 255),
        ]
        full_text = " ".join(w.text for w in line.words)
        bbox = draw.textbbox((0, 0), full_text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        start_x, y = self._get_text_position(data["position"], tw, th)
        current_x = start_x

        for i, word in enumerate(line.words):
            if i <= active_idx:
                color = colors[i % len(colors)]
            else:
                color = normal_color
            word_text = word.text + " "
            self._draw_outlined_text(draw, current_x, y, word_text, font, color, outline_color, outline_w)
            bbox = draw.textbbox((0, 0), word_text, font=font)
            current_x += bbox[2] - bbox[0]

        return Image.alpha_composite(img.convert("RGBA"), overlay)

    def _render_fire_particle(self, img, data, beat_energy):
        if self.low_spec:
            return self._render_word_highlight(img, data, beat_energy)
        result = self._render_word_highlight(img, data, beat_energy)
        if beat_energy > 0.5:
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            import random
            time_val = data.get("time", 0)
            random.seed(int(time_val * 10))
            for _ in range(int(beat_energy * 15)):
                px = random.randint(0, self.width)
                py = random.randint(int(self.height * 0.6), self.height)
                size = random.randint(2, 5)
                alpha = random.randint(100, 200)
                color = random.choice([
                    (255, 100, 0, alpha), (255, 200, 0, alpha),
                    (255, 50, 0, alpha), (255, 150, 50, alpha),
                ])
                draw.ellipse([px, py, px + size, py + size], fill=color)
            result = Image.alpha_composite(result.convert("RGBA"), overlay)
        return result
