"""Background source manager.

Supports:
- solid color fallback
- single image or video
- multi-image / multi-video with smooth crossfade
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import cv2
import numpy as np

from ..config import BackgroundConfig
from ..utils.colors import hex_to_rgb
from ..utils.paths import is_image, is_video

logger = logging.getLogger(__name__)


@dataclass
class _Source:
    path: str
    is_video: bool
    image: np.ndarray | None = None
    cap: cv2.VideoCapture | None = None
    fps: float = 30.0
    duration: float = 0.0
    frame_count: int = 0
    last_frame: np.ndarray | None = None


class BackgroundProvider:
    """Yields background frames for a given timestamp."""

    def __init__(self, cfg: BackgroundConfig, width: int, height: int):
        self.cfg = cfg
        self.width = width
        self.height = height
        self.sources: list[_Source] = []
        self._load_sources()

    def close(self) -> None:
        for s in self.sources:
            if s.cap is not None:
                try:
                    s.cap.release()
                except Exception:
                    pass

    def _load_sources(self) -> None:
        files = [p for p in self.cfg.files if p and os.path.exists(p)]
        if not self.cfg.enabled_multi and files:
            files = files[:1]
        for path in files:
            try:
                if is_video(path):
                    cap = cv2.VideoCapture(path)
                    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                    fc = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                    self.sources.append(
                        _Source(
                            path=path,
                            is_video=True,
                            cap=cap,
                            fps=fps,
                            duration=fc / fps if fps else 0.0,
                            frame_count=fc,
                        )
                    )
                elif is_image(path):
                    img = cv2.imread(path, cv2.IMREAD_COLOR)
                    if img is None:
                        logger.warning("Gagal membaca gambar background: %s", path)
                        continue
                    img = _fit(img, self.width, self.height, self.cfg.fit_mode)
                    self.sources.append(_Source(path=path, is_video=False, image=img))
            except Exception as exc:
                logger.warning("Gagal memuat background %s: %s", path, exc)

    def get_frame(self, t: float) -> np.ndarray:
        """Return BGR uint8 (H, W, 3) for time t (seconds)."""
        if not self.sources:
            return self._solid_color()
        if len(self.sources) == 1:
            return self._post_process(self._frame_from_source(self.sources[0], t))

        # multi-source with crossfade
        cycle = max(0.5, self.cfg.cycle_seconds)
        fade = min(self.cfg.crossfade_seconds, cycle * 0.6)
        idx_float = t / cycle
        idx = int(idx_float) % len(self.sources)
        next_idx = (idx + 1) % len(self.sources)
        offset_in_cycle = (t % cycle) - (cycle - fade)
        if offset_in_cycle > 0 and fade > 0:
            ratio = max(0.0, min(1.0, offset_in_cycle / fade))
            a = self._frame_from_source(self.sources[idx], t)
            b = self._frame_from_source(self.sources[next_idx], t)
            blend = cv2.addWeighted(a, 1.0 - ratio, b, ratio, 0)
            return self._post_process(blend)
        return self._post_process(self._frame_from_source(self.sources[idx], t))

    def _frame_from_source(self, source: _Source, t: float) -> np.ndarray:
        if not source.is_video and source.image is not None:
            return source.image
        if source.is_video and source.cap is not None:
            target_frame = (
                int(t * source.fps) % source.frame_count
                if source.frame_count > 0
                else int(t * source.fps)
            )
            current = int(source.cap.get(cv2.CAP_PROP_POS_FRAMES))
            if target_frame != current:
                source.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            ok, frame = source.cap.read()
            if not ok or frame is None:
                # rewind & retry once
                source.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = source.cap.read()
            if ok and frame is not None:
                fitted = _fit(frame, self.width, self.height, self.cfg.fit_mode)
                source.last_frame = fitted
                return fitted
            if source.last_frame is not None:
                return source.last_frame
        return self._solid_color()

    def _post_process(self, frame: np.ndarray) -> np.ndarray:
        out = frame
        if self.cfg.blur > 0:
            k = max(3, int(self.cfg.blur) | 1)
            out = cv2.GaussianBlur(out, (k, k), 0)
        if self.cfg.darken > 0:
            out = cv2.addWeighted(out, max(0.0, 1.0 - self.cfg.darken), np.zeros_like(out), 0, 0)
        return out

    def _solid_color(self) -> np.ndarray:
        r, g, b = hex_to_rgb(self.cfg.color)
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[..., 0] = b
        frame[..., 1] = g
        frame[..., 2] = r
        return frame


def _fit(img: np.ndarray, width: int, height: int, mode: str) -> np.ndarray:
    h, w = img.shape[:2]
    if w == width and h == height:
        return img
    if mode == "contain":
        scale = min(width / w, height / h)
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
        resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        out = np.zeros((height, width, 3), dtype=np.uint8)
        ox = (width - new_w) // 2
        oy = (height - new_h) // 2
        out[oy : oy + new_h, ox : ox + new_w] = resized
        return out
    # cover (default)
    scale = max(width / w, height / h)
    new_w, new_h = max(width, int(w * scale)), max(height, int(h * scale))
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    ox = (new_w - width) // 2
    oy = (new_h - height) // 2
    return resized[oy : oy + height, ox : ox + width]
