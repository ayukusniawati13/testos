"""Logo overlay (with optional circular crop)."""

from __future__ import annotations

import logging
import os

import cv2
import numpy as np
from PIL import Image

from ..config import LogoConfig

logger = logging.getLogger(__name__)


class LogoOverlay:
    def __init__(self, cfg: LogoConfig, width: int, height: int):
        self.cfg = cfg
        self.width = width
        self.height = height
        self._cached: np.ndarray | None = None  # BGRA uint8
        self._origin: tuple[int, int] | None = None
        if cfg.enabled and cfg.path and os.path.exists(cfg.path):
            self._prepare()

    def _prepare(self) -> None:
        try:
            img = Image.open(self.cfg.path).convert("RGBA")
        except Exception as exc:
            logger.warning("Gagal memuat logo %s: %s", self.cfg.path, exc)
            return
        size = max(8, int(self.width * (self.cfg.size_pct / 100.0)))
        img = img.resize((size, size), Image.LANCZOS)
        if self.cfg.circular:
            mask = Image.new("L", (size, size), 0)
            from PIL import ImageDraw

            ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
            channels = list(img.split())
            if len(channels) < 4:
                channels.append(mask)
            else:
                # multiply existing alpha with mask
                existing = channels[3]
                new_alpha = Image.eval(existing, lambda v: v)
                new_alpha = Image.composite(existing, Image.new("L", (size, size), 0), mask)
                channels[3] = new_alpha
            img = Image.merge("RGBA", channels)
        if self.cfg.opacity < 1.0:
            alpha = img.split()[3].point(lambda v: int(v * self.cfg.opacity))
            img.putalpha(alpha)
        arr = np.array(img)  # RGBA
        bgra = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)
        self._cached = bgra
        self._origin = self._compute_origin(size)

    def _compute_origin(self, size: int) -> tuple[int, int]:
        margin_x = int(self.width * (self.cfg.x_pct / 100.0))
        margin_y = int(self.height * (self.cfg.y_pct / 100.0))
        anchor = self.cfg.anchor
        if anchor == "top_right":
            x = self.width - size - margin_x
            y = margin_y
        elif anchor == "bottom_left":
            x = margin_x
            y = self.height - size - margin_y
        elif anchor == "bottom_right":
            x = self.width - size - margin_x
            y = self.height - size - margin_y
        elif anchor == "center":
            x = (self.width - size) // 2
            y = (self.height - size) // 2
        else:  # top_left
            x = margin_x
            y = margin_y
        return x, y

    def draw(self, frame_bgr: np.ndarray) -> None:
        if self._cached is None or self._origin is None:
            return
        logo = self._cached
        x, y = self._origin
        h, w = logo.shape[:2]
        # clip to frame bounds
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(frame_bgr.shape[1], x + w)
        y2 = min(frame_bgr.shape[0], y + h)
        if x1 >= x2 or y1 >= y2:
            return
        roi = frame_bgr[y1:y2, x1:x2]
        crop = logo[(y1 - y) : (y1 - y) + (y2 - y1), (x1 - x) : (x1 - x) + (x2 - x1)]
        alpha = crop[..., 3:4].astype(np.float32) / 255.0
        roi_f = roi.astype(np.float32)
        crop_f = crop[..., :3].astype(np.float32)
        blended = roi_f * (1.0 - alpha) + crop_f * alpha
        np.copyto(roi, blended.astype(np.uint8))
