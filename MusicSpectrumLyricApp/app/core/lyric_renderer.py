"""Lyric text renderer with fade transitions and styling."""

import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from app.core.lrc_parser import LyricLine


class LyricConfig:
    def __init__(self):
        self.font_family: str = "Arial"
        self.font_size: int = 48
        self.color: tuple = (255, 255, 255)
        self.shadow_color: tuple = (0, 0, 0)
        self.shadow_offset: int = 3
        self.stroke_color: tuple = (0, 0, 0)
        self.stroke_width: int = 2
        self.glow: float = 0.5
        self.glow_color: tuple = (100, 150, 255)
        self.position: str = "bottom"
        self.alignment: str = "center"
        self.show_next_line: bool = True
        self.fade_duration: float = 0.5
        self.margin_bottom: int = 80
        self.margin_top: int = 80


class LyricRenderer:
    def __init__(self, config: LyricConfig | None = None):
        self.config = config or LyricConfig()
        self._font: ImageFont.FreeTypeFont | None = None
        self._small_font: ImageFont.FreeTypeFont | None = None

    def _get_font(self, size: int | None = None) -> ImageFont.FreeTypeFont:
        sz = size or self.config.font_size
        try:
            return ImageFont.truetype(self.config.font_family, sz)
        except (OSError, IOError):
            for fallback in ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf",
                             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                             "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                             "C:/Windows/Fonts/arial.ttf"]:
                try:
                    return ImageFont.truetype(fallback, sz)
                except (OSError, IOError):
                    continue
            return ImageFont.load_default()

    def get_active_lyric(self, lyrics: list[LyricLine], current_time: float
                         ) -> tuple[LyricLine | None, LyricLine | None, float]:
        if not lyrics:
            return None, None, 0.0

        if current_time < lyrics[0].time:
            return None, None, 0.0

        active_idx = -1
        for i, line in enumerate(lyrics):
            if line.time <= current_time:
                active_idx = i
            else:
                break

        if active_idx < 0:
            return None, None, 0.0

        active = lyrics[active_idx]
        next_line = lyrics[active_idx + 1] if active_idx + 1 < len(lyrics) else None

        if next_line:
            duration = next_line.time - active.time
        else:
            duration = 5.0

        elapsed = current_time - active.time
        fade = self.config.fade_duration

        if elapsed < fade:
            opacity = elapsed / fade
        elif next_line and (next_line.time - current_time) < fade:
            opacity = (next_line.time - current_time) / fade
        elif duration > 4.0 and elapsed > duration - fade * 2:
            remaining = duration - elapsed
            opacity = max(0, remaining / (fade * 2))
        else:
            opacity = 1.0

        opacity = max(0.0, min(1.0, opacity))
        return active, next_line, opacity

    def render(self, width: int, height: int, lyrics: list[LyricLine],
               current_time: float) -> Image.Image:
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        active, next_line, opacity = self.get_active_lyric(lyrics, current_time)

        if active is None:
            return img

        font = self._get_font()
        small_font = self._get_font(int(self.config.font_size * 0.7))

        self._draw_text_line(img, active.text, font, opacity, is_main=True,
                             width=width, height=height, line_offset=0)

        if self.config.show_next_line and next_line:
            next_opacity = opacity * 0.5
            self._draw_text_line(img, next_line.text, small_font, next_opacity,
                                 is_main=False, width=width, height=height, line_offset=1)

        return img

    def _draw_text_line(self, img: Image.Image, text: str,
                        font: ImageFont.FreeTypeFont, opacity: float,
                        is_main: bool, width: int, height: int,
                        line_offset: int) -> None:
        if opacity <= 0:
            return

        draw = ImageDraw.Draw(img)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        if self.config.alignment == "center":
            x = (width - tw) // 2
        elif self.config.alignment == "left":
            x = 40
        else:
            x = width - tw - 40

        if self.config.position == "bottom":
            base_y = height - self.config.margin_bottom - th
        elif self.config.position == "top":
            base_y = self.config.margin_top
        else:
            base_y = (height - th) // 2

        line_spacing = int(th * 1.6)
        y = base_y + line_offset * line_spacing
        if not is_main:
            y += 10

        alpha = int(255 * opacity)

        if self.config.glow > 0 and is_main:
            glow_img = Image.new("RGBA", img.size, (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_img)
            gc = self.config.glow_color
            glow_alpha = int(alpha * self.config.glow * 0.6)
            glow_draw.text((x, y), text, font=font,
                           fill=(gc[0], gc[1], gc[2], glow_alpha))
            glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=8))
            img.paste(Image.alpha_composite(
                Image.new("RGBA", img.size, (0, 0, 0, 0)), glow_img), (0, 0))

        draw = ImageDraw.Draw(img)

        if self.config.shadow_offset > 0:
            sc = self.config.shadow_color
            shadow_alpha = int(alpha * 0.7)
            sx = x + self.config.shadow_offset
            sy = y + self.config.shadow_offset
            draw.text((sx, sy), text, font=font,
                      fill=(sc[0], sc[1], sc[2], shadow_alpha))

        if self.config.stroke_width > 0:
            stc = self.config.stroke_color
            draw.text((x, y), text, font=font,
                      fill=(self.config.color[0], self.config.color[1],
                            self.config.color[2], alpha),
                      stroke_width=self.config.stroke_width,
                      stroke_fill=(stc[0], stc[1], stc[2], alpha))
        else:
            draw.text((x, y), text, font=font,
                      fill=(self.config.color[0], self.config.color[1],
                            self.config.color[2], alpha))
