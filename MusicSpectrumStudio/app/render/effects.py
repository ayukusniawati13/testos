"""Video post effects: sparkle, glow, vignette, grain, beat flash, light leaks."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np

from ..config import EffectsConfig


@dataclass
class EffectContext:
    width: int
    height: int
    frame_index: int
    fps: int
    loudness: float
    beat: bool
    rng: np.random.Generator

    @classmethod
    def make(cls, width: int, height: int, frame_index: int, fps: int, loudness: float, beat: bool) -> EffectContext:
        return cls(
            width=width,
            height=height,
            frame_index=frame_index,
            fps=fps,
            loudness=loudness,
            beat=beat,
            rng=np.random.default_rng(frame_index * 7919 + 13),
        )


def apply_effects(frame: np.ndarray, cfg: EffectsConfig, ctx: EffectContext) -> None:
    if cfg.light_leaks:
        _light_leaks(frame, ctx)
    if cfg.glow and cfg.glow_strength > 0:
        _bloom(frame, ctx, cfg.glow_strength)
    if cfg.sparkle and cfg.sparkle_intensity > 0:
        _sparkle(frame, ctx, cfg.sparkle_intensity)
    if cfg.beat_flash and ctx.beat:
        _flash(frame, intensity=0.35)
    if cfg.vignette and cfg.vignette_strength > 0:
        _vignette(frame, cfg.vignette_strength)
    if cfg.grain and cfg.grain_strength > 0:
        _grain(frame, ctx, cfg.grain_strength)


def _bloom(frame: np.ndarray, ctx: EffectContext, strength: float) -> None:
    """Soft highlight bloom."""
    bright = cv2.threshold(frame, 180, 255, cv2.THRESH_TOZERO)[1]
    blurred = cv2.GaussianBlur(bright, (0, 0), sigmaX=12, sigmaY=12)
    cv2.addWeighted(frame, 1.0, blurred, strength, 0, dst=frame)


def _sparkle(frame: np.ndarray, ctx: EffectContext, intensity: float) -> None:
    count = int(20 + intensity * 80 + ctx.loudness * 40)
    h, w = frame.shape[:2]
    overlay = np.zeros_like(frame)
    for _ in range(count):
        x = int(ctx.rng.integers(0, w))
        y = int(ctx.rng.integers(0, h))
        r = max(1, int(ctx.rng.integers(1, 4)))
        twinkle = 0.5 + 0.5 * math.sin((ctx.frame_index + x + y) / 4.0)
        c = int(255 * twinkle)
        cv2.circle(overlay, (x, y), r, (c, c, c), -1, lineType=cv2.LINE_AA)
    blurred = cv2.GaussianBlur(overlay, (0, 0), sigmaX=2.0, sigmaY=2.0)
    cv2.add(frame, blurred, dst=frame)


def _vignette(frame: np.ndarray, strength: float) -> None:
    h, w = frame.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2.0, h / 2.0
    dist = np.sqrt(((xx - cx) / (w / 2.0)) ** 2 + ((yy - cy) / (h / 2.0)) ** 2)
    mask = np.clip(1.0 - strength * (dist - 0.4), 0.0, 1.0)
    mask = mask[..., None]
    np.multiply(frame, mask, out=frame, casting="unsafe")


def _grain(frame: np.ndarray, ctx: EffectContext, strength: float) -> None:
    noise = (ctx.rng.standard_normal(frame.shape) * 255 * strength).astype(np.int16)
    out = frame.astype(np.int16) + noise
    np.clip(out, 0, 255, out=out)
    np.copyto(frame, out.astype(np.uint8))


def _flash(frame: np.ndarray, intensity: float) -> None:
    white = np.full_like(frame, 255)
    cv2.addWeighted(frame, 1.0, white, intensity, 0, dst=frame)


def _light_leaks(frame: np.ndarray, ctx: EffectContext) -> None:
    h, w = frame.shape[:2]
    overlay = np.zeros_like(frame)
    phase = ctx.frame_index / max(ctx.fps, 1)
    for i, base in enumerate([(255, 120, 60), (60, 180, 255)]):
        cx = int(w * (0.5 + 0.45 * math.sin(phase * 0.8 + i)))
        cy = int(h * (0.5 + 0.35 * math.cos(phase * 0.6 + i)))
        radius = int(min(w, h) * (0.4 + 0.1 * math.sin(phase + i)))
        cv2.circle(overlay, (cx, cy), radius, base, -1)
    overlay = cv2.GaussianBlur(overlay, (0, 0), sigmaX=80, sigmaY=80)
    cv2.addWeighted(frame, 1.0, overlay, 0.25, 0, dst=frame)
