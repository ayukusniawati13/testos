"""Spectrum visualizer styles.

Each style implements `draw(frame_bgr, bands, loudness, ctx)` where:
- frame_bgr: numpy uint8 array (H, W, 3) BGR (OpenCV) to be modified IN PLACE
- bands: 1-D numpy float32 array in [0, 1] (length = SpectrumConfig.bar_count)
- loudness: float in [0, 1] for this frame
- ctx: SpectrumDrawContext with config + helper colors

All styles render into a region implied by the spectrum config (position, height_pct).
Styles return None; OpenCV draws onto the passed-in frame.

The list `SPECTRUM_STYLES` is the canonical ordered registry used by the GUI.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np

from ..config import SpectrumConfig
from ..utils.colors import hex_to_rgb, hsv_to_rgb, lerp_color


@dataclass
class SpectrumDrawContext:
    width: int
    height: int
    config: SpectrumConfig
    color_a: tuple[int, int, int]
    color_b: tuple[int, int, int]
    region_top: int
    region_bottom: int
    region_height: int
    frame_index: int = 0
    fps: int = 30


def make_context(cfg: SpectrumConfig, width: int, height: int, frame_index: int = 0, fps: int = 30) -> SpectrumDrawContext:
    rh = int(height * cfg.height_pct / 100.0)
    rh = max(40, min(rh, height))
    if cfg.position == "bottom":
        top = height - rh
        bottom = height
    elif cfg.position == "top":
        top = 0
        bottom = rh
    else:
        top = (height - rh) // 2
        bottom = top + rh
    a = hex_to_rgb(cfg.color_a)
    b = hex_to_rgb(cfg.color_b)
    return SpectrumDrawContext(
        width=width,
        height=height,
        config=cfg,
        color_a=a,
        color_b=b,
        region_top=top,
        region_bottom=bottom,
        region_height=rh,
        frame_index=frame_index,
        fps=fps,
    )


def _bgr(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return (color[2], color[1], color[0])


def _blend(dst: np.ndarray, src: np.ndarray, alpha: float = 1.0) -> None:
    if alpha >= 1.0:
        np.copyto(dst, src)
        return
    cv2.addWeighted(src, alpha, dst, 1 - alpha, 0, dst=dst)


def _additive_blit(dst: np.ndarray, overlay: np.ndarray) -> None:
    """Overlay (HxWx4 BGRA) on top of dst (HxWx3 BGR) using its alpha channel additively."""
    if overlay.shape[2] == 4:
        alpha = overlay[..., 3:4].astype(np.float32) / 255.0
        np.add(dst, (overlay[..., :3].astype(np.float32) * alpha).astype(np.uint8), out=dst, casting="unsafe")
    else:
        np.add(dst, overlay, out=dst, casting="unsafe")


def _glow(layer: np.ndarray, strength: float) -> np.ndarray:
    if strength <= 0:
        return layer
    k = max(3, int(7 * strength) | 1)
    blurred = cv2.GaussianBlur(layer, (k, k), 0)
    return cv2.addWeighted(layer, 1.0, blurred, strength * 0.8, 0)


# ---------------------------------------------------------------------------
# Style implementations
# ---------------------------------------------------------------------------

def _draw_bars(frame: np.ndarray, bands: np.ndarray, loudness: float, ctx: SpectrumDrawContext, rounded: bool = False, mirror: bool = False) -> None:
    n = len(bands)
    if n == 0:
        return
    bar_w = ctx.width / n
    gap = max(1, int(bar_w * 0.18))
    inner = max(1, int(bar_w) - gap)
    y_bottom = ctx.region_bottom - 2
    y_top = ctx.region_top
    max_h = y_bottom - y_top if not mirror else (y_bottom - y_top) // 2 - 2
    overlay = np.zeros_like(frame)
    for i, value in enumerate(bands):
        v = float(value)
        h = int(v * max_h)
        if h < 2:
            continue
        cx = int(i * bar_w + bar_w / 2)
        x1 = cx - inner // 2
        x2 = x1 + inner
        c = lerp_color(ctx.color_a, ctx.color_b, v)
        c_bgr = _bgr(c)
        if mirror:
            mid_y = (y_top + y_bottom) // 2
            cv2.rectangle(overlay, (x1, mid_y - h), (x2, mid_y), c_bgr, thickness=-1)
            cv2.rectangle(overlay, (x1, mid_y), (x2, mid_y + h), c_bgr, thickness=-1)
        else:
            top_y = y_bottom - h
            if rounded:
                r = max(2, inner // 2)
                cv2.rectangle(overlay, (x1, top_y + r), (x2, y_bottom), c_bgr, thickness=-1)
                cv2.circle(overlay, (cx, top_y + r), r, c_bgr, thickness=-1)
            else:
                cv2.rectangle(overlay, (x1, top_y), (x2, y_bottom), c_bgr, thickness=-1)
    glow_strength = 0.4 + 0.4 * loudness
    overlay = _glow(overlay, glow_strength)
    cv2.add(frame, overlay, dst=frame)


def style_bars_modern(frame, bands, loudness, ctx):
    _draw_bars(frame, bands, loudness, ctx, rounded=False, mirror=False)


def style_bars_rounded(frame, bands, loudness, ctx):
    _draw_bars(frame, bands, loudness, ctx, rounded=True, mirror=False)


def style_bars_mirror(frame, bands, loudness, ctx):
    _draw_bars(frame, bands, loudness, ctx, rounded=False, mirror=True)


def style_bars_gradient_glow(frame, bands, loudness, ctx):
    overlay = np.zeros_like(frame)
    n = len(bands)
    bar_w = ctx.width / n
    inner = max(2, int(bar_w * 0.55))
    y_bottom = ctx.region_bottom - 2
    max_h = ctx.region_height - 4
    for i, value in enumerate(bands):
        v = float(value)
        h = int(v * max_h)
        if h < 3:
            continue
        cx = int(i * bar_w + bar_w / 2)
        # Vertical gradient inside each bar
        for j in range(h):
            t = j / max(1, h)
            c = lerp_color(ctx.color_a, ctx.color_b, t)
            cv2.rectangle(overlay, (cx - inner // 2, y_bottom - j), (cx + inner // 2, y_bottom - j + 1), _bgr(c), thickness=-1)
    overlay = _glow(overlay, 1.0)
    cv2.add(frame, overlay, dst=frame)


def style_equalizer_blocks(frame, bands, loudness, ctx):
    overlay = np.zeros_like(frame)
    n = len(bands)
    bar_w = ctx.width / n
    inner = max(2, int(bar_w * 0.62))
    block_h = max(4, int(ctx.region_height / 18))
    gap = max(1, block_h // 4)
    y_bottom = ctx.region_bottom - 2
    for i, value in enumerate(bands):
        v = float(value)
        count = int(v * (ctx.region_height / (block_h + gap)))
        cx = int(i * bar_w + bar_w / 2)
        for k in range(count):
            y2 = y_bottom - k * (block_h + gap)
            y1 = y2 - block_h
            t = k / max(1, count)
            c = lerp_color(ctx.color_a, ctx.color_b, t)
            cv2.rectangle(overlay, (cx - inner // 2, y1), (cx + inner // 2, y2), _bgr(c), thickness=-1)
    overlay = _glow(overlay, 0.5 + 0.3 * loudness)
    cv2.add(frame, overlay, dst=frame)


def style_dotted_bars(frame, bands, loudness, ctx):
    overlay = np.zeros_like(frame)
    n = len(bands)
    bar_w = ctx.width / n
    dot_r = max(2, int(bar_w * 0.32))
    spacing = dot_r * 2 + max(2, dot_r // 2)
    y_bottom = ctx.region_bottom - dot_r - 2
    for i, value in enumerate(bands):
        v = float(value)
        count = int(v * (ctx.region_height / spacing))
        cx = int(i * bar_w + bar_w / 2)
        for k in range(count):
            cy = y_bottom - k * spacing
            t = k / max(1, count)
            c = lerp_color(ctx.color_a, ctx.color_b, t)
            cv2.circle(overlay, (cx, cy), dot_r, _bgr(c), thickness=-1, lineType=cv2.LINE_AA)
    overlay = _glow(overlay, 0.45 + 0.2 * loudness)
    cv2.add(frame, overlay, dst=frame)


def style_wave_smooth(frame, bands, loudness, ctx):
    n = len(bands)
    overlay = np.zeros_like(frame)
    xs = np.linspace(0, ctx.width - 1, n)
    ys = ctx.region_bottom - (bands * (ctx.region_height - 6) + 3)
    # Build a smooth polyline (Catmull-Rom-ish via cv2.polylines on dense interp)
    if n > 2:
        xs_dense = np.linspace(0, ctx.width - 1, n * 8)
        ys_dense = np.interp(xs_dense, xs, ys)
        pts = np.stack([xs_dense, ys_dense], axis=1).astype(np.int32)
    else:
        pts = np.stack([xs, ys], axis=1).astype(np.int32)
    # Fill below curve with gradient
    fill_pts = np.vstack([pts, [[ctx.width - 1, ctx.region_bottom], [0, ctx.region_bottom]]])
    cv2.fillPoly(overlay, [fill_pts.astype(np.int32)], _bgr(lerp_color(ctx.color_a, ctx.color_b, 0.4)))
    # Stroke
    cv2.polylines(overlay, [pts], isClosed=False, color=_bgr(ctx.color_b), thickness=4, lineType=cv2.LINE_AA)
    overlay = _glow(overlay, 0.4 + 0.3 * loudness)
    cv2.addWeighted(frame, 1.0, overlay, 0.85, 0, dst=frame)


def style_wave_mirror(frame, bands, loudness, ctx):
    n = len(bands)
    overlay = np.zeros_like(frame)
    mid_y = (ctx.region_top + ctx.region_bottom) // 2
    half = (ctx.region_bottom - ctx.region_top) // 2 - 4
    xs = np.linspace(0, ctx.width - 1, n)
    amp = bands * half
    if n > 2:
        xs_dense = np.linspace(0, ctx.width - 1, n * 8)
        amp_dense = np.interp(xs_dense, xs, amp)
    else:
        xs_dense, amp_dense = xs, amp
    pts_top = np.stack([xs_dense, mid_y - amp_dense], axis=1).astype(np.int32)
    pts_bot = np.stack([xs_dense, mid_y + amp_dense], axis=1).astype(np.int32)
    poly = np.vstack([pts_top, pts_bot[::-1]])
    cv2.fillPoly(overlay, [poly], _bgr(lerp_color(ctx.color_a, ctx.color_b, 0.35)))
    cv2.polylines(overlay, [pts_top], False, _bgr(ctx.color_b), 3, lineType=cv2.LINE_AA)
    cv2.polylines(overlay, [pts_bot], False, _bgr(ctx.color_a), 3, lineType=cv2.LINE_AA)
    overlay = _glow(overlay, 0.6)
    cv2.addWeighted(frame, 1.0, overlay, 0.9, 0, dst=frame)


def style_ribbon(frame, bands, loudness, ctx):
    overlay = np.zeros_like(frame)
    mid_y = (ctx.region_top + ctx.region_bottom) // 2
    n = len(bands)
    xs = np.linspace(0, ctx.width - 1, n)
    base = bands * (ctx.region_height // 2)
    phase = ctx.frame_index / max(ctx.fps, 1)
    wobble = np.sin(np.linspace(0, math.pi * 4, n) + phase * 2.0) * 10
    upper = mid_y - base + wobble
    lower = mid_y + base * 0.6 + wobble
    if n > 2:
        xs_d = np.linspace(0, ctx.width - 1, n * 8)
        upper_d = np.interp(xs_d, xs, upper)
        lower_d = np.interp(xs_d, xs, lower)
    else:
        xs_d, upper_d, lower_d = xs, upper, lower
    poly = np.vstack([
        np.stack([xs_d, upper_d], axis=1),
        np.stack([xs_d[::-1], lower_d[::-1]], axis=1),
    ]).astype(np.int32)
    cv2.fillPoly(overlay, [poly], _bgr(lerp_color(ctx.color_a, ctx.color_b, 0.5)))
    overlay = _glow(overlay, 0.7)
    cv2.addWeighted(frame, 1.0, overlay, 0.85, 0, dst=frame)


def style_circular_bars(frame, bands, loudness, ctx):
    overlay = np.zeros_like(frame)
    cx, cy = ctx.width // 2, ctx.height // 2
    n = len(bands)
    inner_r = int(min(ctx.width, ctx.height) * 0.18)
    max_len = int(min(ctx.width, ctx.height) * 0.32)
    for i, v in enumerate(bands):
        angle = (i / n) * math.tau - math.pi / 2
        length = inner_r + int(float(v) * max_len)
        x1 = int(cx + inner_r * math.cos(angle))
        y1 = int(cy + inner_r * math.sin(angle))
        x2 = int(cx + length * math.cos(angle))
        y2 = int(cy + length * math.sin(angle))
        c = lerp_color(ctx.color_a, ctx.color_b, float(v))
        cv2.line(overlay, (x1, y1), (x2, y2), _bgr(c), thickness=max(2, ctx.width // 540), lineType=cv2.LINE_AA)
    # central ring pulse
    r = inner_r - 6 - int(loudness * 8)
    cv2.circle(overlay, (cx, cy), max(r, 12), _bgr(ctx.color_b), thickness=2, lineType=cv2.LINE_AA)
    overlay = _glow(overlay, 0.6 + 0.4 * loudness)
    cv2.add(frame, overlay, dst=frame)


def style_circular_wave(frame, bands, loudness, ctx):
    overlay = np.zeros_like(frame)
    cx, cy = ctx.width // 2, ctx.height // 2
    n = len(bands)
    base_r = int(min(ctx.width, ctx.height) * 0.22)
    max_r = int(min(ctx.width, ctx.height) * 0.14)
    pts = []
    for i, v in enumerate(bands):
        angle = (i / n) * math.tau
        r = base_r + int(float(v) * max_r)
        pts.append((int(cx + r * math.cos(angle)), int(cy + r * math.sin(angle))))
    # close polyline
    if pts:
        arr = np.array(pts + [pts[0]], dtype=np.int32)
        cv2.polylines(overlay, [arr], True, _bgr(ctx.color_b), 3, lineType=cv2.LINE_AA)
        cv2.fillPoly(overlay, [arr], _bgr(lerp_color(ctx.color_a, ctx.color_b, 0.35)))
    overlay = _glow(overlay, 0.6)
    cv2.addWeighted(frame, 1.0, overlay, 0.85, 0, dst=frame)


def style_pulse_ring(frame, bands, loudness, ctx):
    overlay = np.zeros_like(frame)
    cx, cy = ctx.width // 2, ctx.height // 2
    base_r = int(min(ctx.width, ctx.height) * 0.18)
    rings = 5
    for k in range(rings):
        t = k / rings
        r = base_r + int(t * min(ctx.width, ctx.height) * 0.18)
        thickness = max(1, int(8 * (1 - t) * (0.4 + 0.6 * loudness)))
        c = lerp_color(ctx.color_a, ctx.color_b, t)
        cv2.circle(overlay, (cx, cy), r, _bgr(c), thickness=thickness, lineType=cv2.LINE_AA)
    # Bass kick — extra ring on beat
    if loudness > 0.5:
        cv2.circle(overlay, (cx, cy), base_r // 2, _bgr(ctx.color_b), thickness=-1, lineType=cv2.LINE_AA)
    overlay = _glow(overlay, 0.5 + loudness)
    cv2.add(frame, overlay, dst=frame)


def style_radial_petals(frame, bands, loudness, ctx):
    overlay = np.zeros_like(frame)
    cx, cy = ctx.width // 2, ctx.height // 2
    n = len(bands)
    inner_r = int(min(ctx.width, ctx.height) * 0.10)
    max_r = int(min(ctx.width, ctx.height) * 0.32)
    for i, v in enumerate(bands):
        v = float(v)
        if v < 0.05:
            continue
        angle = (i / n) * math.tau - math.pi / 2
        length = inner_r + int(v * max_r)
        width = max(2, int(length * 0.18))
        c = lerp_color(ctx.color_a, ctx.color_b, v)
        # draw petal: two filled triangles or thick line
        x1 = int(cx + inner_r * math.cos(angle))
        y1 = int(cy + inner_r * math.sin(angle))
        x2 = int(cx + length * math.cos(angle))
        y2 = int(cy + length * math.sin(angle))
        cv2.line(overlay, (x1, y1), (x2, y2), _bgr(c), thickness=width, lineType=cv2.LINE_AA)
    overlay = _glow(overlay, 0.7)
    cv2.add(frame, overlay, dst=frame)


def style_particles(frame, bands, loudness, ctx):
    overlay = np.zeros_like(frame)
    n = len(bands)
    bar_w = ctx.width / n
    rng = np.random.default_rng(ctx.frame_index * 17 + 3)
    for i, v in enumerate(bands):
        v = float(v)
        if v < 0.08:
            continue
        count = int(2 + v * 8)
        cx = int(i * bar_w + bar_w / 2)
        for _ in range(count):
            dy = int(rng.uniform(0, v * ctx.region_height))
            jitter = int(rng.uniform(-bar_w / 2, bar_w / 2))
            r = max(1, int(2 + rng.uniform(0, 3) * v))
            t = dy / max(1, ctx.region_height)
            c = lerp_color(ctx.color_a, ctx.color_b, t)
            cv2.circle(overlay, (cx + jitter, ctx.region_bottom - dy), r, _bgr(c), thickness=-1, lineType=cv2.LINE_AA)
    overlay = _glow(overlay, 0.5)
    cv2.add(frame, overlay, dst=frame)


_SPECTROGRAM_CACHE: list[np.ndarray | None] = [None]


def style_spectrogram_trail(frame, bands, loudness, ctx):
    """Scrolling spectrogram trail."""
    n = len(bands)
    cache = _SPECTROGRAM_CACHE[0]
    if cache is None or cache.shape[1] != ctx.width or cache.shape[0] != ctx.region_height:
        cache = np.zeros((ctx.region_height, ctx.width, 3), dtype=np.uint8)
        _SPECTROGRAM_CACHE[0] = cache
    # shift left by 4 px
    shift = max(2, ctx.width // 480)
    cache[:, :-shift] = cache[:, shift:]
    col = np.zeros((ctx.region_height, shift, 3), dtype=np.uint8)
    band_h = ctx.region_height / n
    for i, v in enumerate(bands):
        v = float(v)
        c = lerp_color(ctx.color_a, ctx.color_b, v)
        y2 = int(ctx.region_height - i * band_h)
        y1 = int(ctx.region_height - (i + 1) * band_h)
        cv2.rectangle(col, (0, y1), (shift, y2), (int(c[2] * v), int(c[1] * v), int(c[0] * v)), -1)
    cache[:, -shift:] = col
    target = frame[ctx.region_top:ctx.region_bottom, :, :]
    cv2.addWeighted(target, 0.0, cache, 1.0, 0, dst=target)


def style_cinematic_glow(frame, bands, loudness, ctx):
    """Soft horizontal glow band tied to low/mid frequencies."""
    n = len(bands)
    overlay = np.zeros_like(frame)
    low = float(np.mean(bands[: n // 3])) if n else 0.0
    high = float(np.mean(bands[n // 3 :])) if n else 0.0
    mid_y = ctx.region_bottom - int((0.2 + 0.5 * low) * ctx.region_height / 2)
    color = lerp_color(ctx.color_a, ctx.color_b, high)
    radius = int(40 + 100 * (low + loudness))
    cv2.circle(overlay, (ctx.width // 2, mid_y), radius, _bgr(color), -1, lineType=cv2.LINE_AA)
    overlay = cv2.GaussianBlur(overlay, (0, 0), sigmaX=radius * 0.6, sigmaY=radius * 0.6)
    cv2.addWeighted(frame, 1.0, overlay, 0.8, 0, dst=frame)


def style_neon_equalizer(frame, bands, loudness, ctx):
    overlay = np.zeros_like(frame)
    n = len(bands)
    bar_w = ctx.width / n
    inner = max(2, int(bar_w * 0.5))
    y_bottom = ctx.region_bottom - 2
    max_h = ctx.region_height - 4
    for i, v in enumerate(bands):
        v = float(v)
        h = int(v * max_h)
        if h < 2:
            continue
        cx = int(i * bar_w + bar_w / 2)
        hue = (i / n + ctx.frame_index / 240.0) % 1.0
        c = hsv_to_rgb(hue, 0.85, 1.0)
        cv2.rectangle(overlay, (cx - inner // 2, y_bottom - h), (cx + inner // 2, y_bottom), _bgr(c), -1)
    overlay = _glow(overlay, 0.9)
    cv2.add(frame, overlay, dst=frame)


def style_liquid_wave(frame, bands, loudness, ctx):
    """Layered translucent waves."""
    overlay = np.zeros_like(frame)
    n = len(bands)
    xs = np.linspace(0, ctx.width - 1, n)
    for layer, scale in enumerate([1.0, 0.7, 0.45]):
        ys = ctx.region_bottom - (bands * (ctx.region_height - 8) * scale + 4)
        ys = ys + math.sin(ctx.frame_index / 12.0 + layer) * 4
        pts = np.stack([xs, ys], axis=1).astype(np.int32)
        poly = np.vstack([pts, [[ctx.width - 1, ctx.region_bottom], [0, ctx.region_bottom]]])
        c = lerp_color(ctx.color_a, ctx.color_b, layer / 2.0)
        col = (c[2] // (layer + 1), c[1] // (layer + 1), c[0] // (layer + 1))
        cv2.fillPoly(overlay, [poly.astype(np.int32)], col)
    overlay = _glow(overlay, 0.4)
    cv2.add(frame, overlay, dst=frame)


def style_minimal_line(frame, bands, loudness, ctx):
    overlay = np.zeros_like(frame)
    n = len(bands)
    xs = np.linspace(0, ctx.width - 1, n)
    ys = ctx.region_bottom - (bands * (ctx.region_height - 6) + 3)
    pts = np.stack([xs, ys], axis=1).astype(np.int32)
    cv2.polylines(overlay, [pts], False, _bgr(ctx.color_b), 3, lineType=cv2.LINE_AA)
    overlay = _glow(overlay, 0.3)
    cv2.add(frame, overlay, dst=frame)


# Registry
SPECTRUM_STYLES: dict[str, callable] = {
    "Bars Modern": style_bars_modern,
    "Bars Rounded": style_bars_rounded,
    "Bars Mirror": style_bars_mirror,
    "Bars Gradient Glow": style_bars_gradient_glow,
    "Equalizer Blocks": style_equalizer_blocks,
    "Dotted Bars": style_dotted_bars,
    "Wave Smooth": style_wave_smooth,
    "Wave Mirror": style_wave_mirror,
    "Ribbon": style_ribbon,
    "Circular Bars": style_circular_bars,
    "Circular Wave": style_circular_wave,
    "Pulse Ring": style_pulse_ring,
    "Radial Petals": style_radial_petals,
    "Particles": style_particles,
    "Spectrogram Trail": style_spectrogram_trail,
    "Cinematic Glow": style_cinematic_glow,
    "Neon Equalizer": style_neon_equalizer,
    "Liquid Wave": style_liquid_wave,
    "Minimal Line": style_minimal_line,
}


def style_names() -> list[str]:
    return list(SPECTRUM_STYLES.keys())


def draw_spectrum(
    frame_bgr: np.ndarray,
    bands: np.ndarray,
    loudness: float,
    cfg: SpectrumConfig,
    *,
    frame_index: int = 0,
    fps: int = 30,
) -> None:
    style = SPECTRUM_STYLES.get(cfg.style)
    if style is None:
        style = next(iter(SPECTRUM_STYLES.values()))
    h, w = frame_bgr.shape[:2]
    ctx = make_context(cfg, w, h, frame_index=frame_index, fps=fps)
    bands = np.asarray(bands, dtype=np.float32)
    if len(bands) != cfg.bar_count:
        # interpolate to bar_count
        x_src = np.linspace(0, 1, len(bands))
        x_dst = np.linspace(0, 1, cfg.bar_count)
        bands = np.interp(x_dst, x_src, bands).astype(np.float32)
    bands = np.clip(bands * cfg.sensitivity, 0.0, 1.0)
    style(frame_bgr, bands, float(loudness), ctx)
