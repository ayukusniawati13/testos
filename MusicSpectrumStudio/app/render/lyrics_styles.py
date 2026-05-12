"""Lyric overlay renderer with several styles, fade in/out, gap handling."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ..config import LyricsConfig
from ..core.fonts import load_font
from ..core.transcribe import LyricLine, TranscriptionResult
from ..utils.colors import hex_to_rgb

LYRIC_STYLES = [
    "Centered Modern",
    "Bottom Subtitle",
    "Karaoke Highlight",
    "Glow Large",
    "Boxed Pill",
    "Cinematic Top",
    "Side Aligned",
    "Typewriter",
]


@dataclass
class LyricRenderState:
    transcription: TranscriptionResult
    width: int
    height: int


def _line_visibility(line: LyricLine, t: float, fade_s: float, hide_before_next: float, next_line: LyricLine | None) -> float:
    """Return alpha 0..1 for line at time t."""
    if t < line.start - fade_s or t > line.end + fade_s:
        return 0.0
    # If there's a sufficient gap to the next line, hide *before* the next starts
    if next_line and (next_line.start - line.end) > hide_before_next and t >= line.end:
        # fade out fully within fade_s
        rel = (t - line.end) / max(fade_s, 0.05)
        return max(0.0, 1.0 - rel)
    if t < line.start:
        rel = (t - (line.start - fade_s)) / max(fade_s, 0.05)
        return max(0.0, min(1.0, rel))
    if t > line.end:
        rel = (t - line.end) / max(fade_s, 0.05)
        return max(0.0, 1.0 - rel)
    return 1.0


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for word in words:
        attempt = " ".join(cur + [word])
        if font.getlength(attempt) <= max_width or not cur:
            cur.append(word)
        else:
            lines.append(" ".join(cur))
            cur = [word]
    if cur:
        lines.append(" ".join(cur))
    return lines


def _draw_centered_modern(
    pil_img: Image.Image,
    text: str,
    cfg: LyricsConfig,
    width: int,
    height: int,
    alpha: float,
    position: str,
) -> None:
    font = load_font(cfg.font_family, cfg.font_size)
    margin_x = int(width * 0.06)
    margin_y = int(height * cfg.margin_pct / 100.0)
    lines = _wrap_text(text, font, width - 2 * margin_x)
    metrics = font.getmetrics()
    line_height = metrics[0] + metrics[1] + int(cfg.font_size * 0.18)
    block_h = line_height * len(lines)
    if position == "top":
        y = margin_y
    elif position == "center":
        y = (height - block_h) // 2
    else:
        y = height - margin_y - block_h

    draw = ImageDraw.Draw(pil_img, "RGBA")
    primary = hex_to_rgb(cfg.primary_color)
    outline = hex_to_rgb(cfg.outline_color)
    fill_alpha = int(255 * alpha)
    outline_alpha = int(255 * alpha)
    for i, line in enumerate(lines):
        w = font.getlength(line)
        x = (width - w) / 2
        if cfg.outline_width > 0:
            for ox in range(-cfg.outline_width, cfg.outline_width + 1):
                for oy in range(-cfg.outline_width, cfg.outline_width + 1):
                    if ox * ox + oy * oy <= cfg.outline_width * cfg.outline_width:
                        draw.text((x + ox, y + i * line_height + oy), line, font=font, fill=(*outline, outline_alpha))
        draw.text((x, y + i * line_height), line, font=font, fill=(*primary, fill_alpha))


def _draw_bottom_subtitle(pil_img, text, cfg, width, height, alpha, position):
    """Subtitle with translucent pill bg behind text."""
    font = load_font(cfg.font_family, cfg.font_size)
    margin_x = int(width * 0.08)
    margin_y = int(height * cfg.margin_pct / 100.0)
    lines = _wrap_text(text, font, width - 2 * margin_x)
    metrics = font.getmetrics()
    line_height = metrics[0] + metrics[1] + int(cfg.font_size * 0.18)
    block_h = line_height * len(lines)
    if position == "top":
        y = margin_y
    elif position == "center":
        y = (height - block_h) // 2
    else:
        y = height - margin_y - block_h
    primary = hex_to_rgb(cfg.primary_color)
    draw = ImageDraw.Draw(pil_img, "RGBA")
    fill_alpha = int(255 * alpha)
    bg_alpha = int(140 * alpha)
    for i, line in enumerate(lines):
        w = font.getlength(line)
        x = (width - w) / 2
        # pill bg
        pad_x = int(cfg.font_size * 0.6)
        pad_y = int(cfg.font_size * 0.2)
        rect = (int(x - pad_x), int(y + i * line_height - pad_y), int(x + w + pad_x), int(y + i * line_height + line_height))
        draw.rounded_rectangle(rect, radius=line_height // 2, fill=(0, 0, 0, bg_alpha))
        draw.text((x, y + i * line_height), line, font=font, fill=(*primary, fill_alpha))


def _draw_karaoke_highlight(
    pil_img,
    text,
    cfg,
    width,
    height,
    alpha,
    position,
    *,
    line: LyricLine,
    t: float,
) -> None:
    """Highlight currently-active word(s)."""
    font = load_font(cfg.font_family, cfg.font_size)
    margin_x = int(width * 0.06)
    margin_y = int(height * cfg.margin_pct / 100.0)
    # We render as a single visual line by horizontally laying out words, wrapping naturally.
    words = line.words or []
    if not words:
        return _draw_centered_modern(pil_img, text, cfg, width, height, alpha, position)
    space_w = font.getlength(" ")
    lines_words: list[list[tuple[float, str, float, float]]] = []
    cur: list[tuple[float, str, float, float]] = []
    cur_w = 0.0
    max_w = width - 2 * margin_x
    for w in words:
        word_w = font.getlength(w.word)
        if cur and cur_w + space_w + word_w > max_w:
            lines_words.append(cur)
            cur = []
            cur_w = 0.0
        cur.append((word_w, w.word, w.start, w.end))
        cur_w += word_w + (space_w if cur else 0)
    if cur:
        lines_words.append(cur)

    metrics = font.getmetrics()
    line_h = metrics[0] + metrics[1] + int(cfg.font_size * 0.2)
    block_h = line_h * len(lines_words)
    if position == "top":
        y = margin_y
    elif position == "center":
        y = (height - block_h) // 2
    else:
        y = height - margin_y - block_h

    draw = ImageDraw.Draw(pil_img, "RGBA")
    primary = hex_to_rgb(cfg.primary_color)
    accent = hex_to_rgb(cfg.accent_color)
    outline = hex_to_rgb(cfg.outline_color)
    fill_alpha = int(255 * alpha)
    for row, ws in enumerate(lines_words):
        total = sum(w for w, *_ in ws) + space_w * (len(ws) - 1)
        x = (width - total) / 2
        for word_w, word_text, ws_start, ws_end in ws:
            color = accent if ws_start <= t <= ws_end + 0.05 else primary
            if cfg.outline_width > 0:
                for ox in range(-cfg.outline_width, cfg.outline_width + 1):
                    for oy in range(-cfg.outline_width, cfg.outline_width + 1):
                        if ox * ox + oy * oy <= cfg.outline_width * cfg.outline_width:
                            draw.text((x + ox, y + row * line_h + oy), word_text, font=font, fill=(*outline, fill_alpha))
            draw.text((x, y + row * line_h), word_text, font=font, fill=(*color, fill_alpha))
            x += word_w + space_w


def _draw_glow_large(pil_img, text, cfg, width, height, alpha, position):
    font = load_font(cfg.font_family, int(cfg.font_size * 1.15))
    margin_x = int(width * 0.06)
    lines = _wrap_text(text, font, width - 2 * margin_x)
    metrics = font.getmetrics()
    lh = metrics[0] + metrics[1] + int(cfg.font_size * 0.22)
    block_h = lh * len(lines)
    if position == "top":
        y = int(height * cfg.margin_pct / 100.0)
    elif position == "center":
        y = (height - block_h) // 2
    else:
        y = height - int(height * cfg.margin_pct / 100.0) - block_h
    # render to temp image to apply glow blur
    layer = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer, "RGBA")
    primary = hex_to_rgb(cfg.primary_color)
    accent = hex_to_rgb(cfg.accent_color)
    for i, line in enumerate(lines):
        w = font.getlength(line)
        x = (width - w) / 2
        draw.text((x, y + i * lh), line, font=font, fill=(*accent, int(220 * alpha)))
    glow = layer.filter(ImageFilter.GaussianBlur(radius=10))
    pil_img.alpha_composite(glow)
    layer2 = Image.new("RGBA", pil_img.size, (0, 0, 0, 0))
    draw2 = ImageDraw.Draw(layer2, "RGBA")
    for i, line in enumerate(lines):
        w = font.getlength(line)
        x = (width - w) / 2
        draw2.text((x, y + i * lh), line, font=font, fill=(*primary, int(255 * alpha)))
    pil_img.alpha_composite(layer2)


def _draw_typewriter(pil_img, text, cfg, width, height, alpha, position, *, line: LyricLine, t: float):
    if not line.words:
        return _draw_centered_modern(pil_img, text, cfg, width, height, alpha, position)
    visible_words = [w.word for w in line.words if w.start <= t + 0.05]
    if not visible_words:
        return
    visible_text = " ".join(visible_words)
    _draw_centered_modern(pil_img, visible_text, cfg, width, height, alpha, position)


def render_lyrics_frame(
    state: LyricRenderState,
    cfg: LyricsConfig,
    t: float,
) -> Image.Image | None:
    if not cfg.enabled or not state.transcription.lines:
        return None
    fade_s = cfg.fade_ms / 1000.0
    active: list[tuple[float, LyricLine, LyricLine | None]] = []
    for i, line in enumerate(state.transcription.lines):
        nxt = state.transcription.lines[i + 1] if i + 1 < len(state.transcription.lines) else None
        a = _line_visibility(line, t, fade_s, cfg.line_gap_seconds, nxt)
        if a > 0.001:
            active.append((a, line, nxt))
    if not active:
        return None

    pil_img = Image.new("RGBA", (state.width, state.height), (0, 0, 0, 0))
    style = cfg.style
    for a, line, _nxt in active[: max(1, cfg.max_lines)]:
        if style == "Karaoke Highlight":
            _draw_karaoke_highlight(pil_img, line.text, cfg, state.width, state.height, a, cfg.position, line=line, t=t)
        elif style == "Bottom Subtitle":
            _draw_bottom_subtitle(pil_img, line.text, cfg, state.width, state.height, a, cfg.position)
        elif style == "Glow Large":
            _draw_glow_large(pil_img, line.text, cfg, state.width, state.height, a, cfg.position)
        elif style == "Boxed Pill":
            _draw_bottom_subtitle(pil_img, line.text, cfg, state.width, state.height, a, cfg.position)
        elif style == "Cinematic Top":
            _draw_centered_modern(pil_img, line.text, cfg, state.width, state.height, a, "top")
        elif style == "Side Aligned":
            _draw_centered_modern(pil_img, line.text, cfg, state.width, state.height, a, cfg.position)
        elif style == "Typewriter":
            _draw_typewriter(pil_img, line.text, cfg, state.width, state.height, a, cfg.position, line=line, t=t)
        else:
            _draw_centered_modern(pil_img, line.text, cfg, state.width, state.height, a, cfg.position)
    return pil_img


def composite_lyrics(frame_bgr: np.ndarray, overlay: Image.Image | None) -> None:
    if overlay is None:
        return
    arr = np.array(overlay)  # RGBA
    if arr.shape[2] != 4:
        return
    alpha = arr[..., 3:4].astype(np.float32) / 255.0
    rgb = arr[..., :3][:, :, ::-1]  # to BGR
    np.copyto(frame_bgr, (frame_bgr.astype(np.float32) * (1.0 - alpha) + rgb.astype(np.float32) * alpha).astype(np.uint8))
