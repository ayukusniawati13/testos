"""
Logo/watermark manager with animation support.
"""
import math
import logging
from PIL import Image, ImageEnhance

logger = logging.getLogger(__name__)


class LogoManager:
    """Manage logo overlay with position, opacity, and animation."""

    POSITION_MAP = {
        "Top Left": (0.05, 0.05),
        "Top Right": (0.95, 0.05),
        "Bottom Left": (0.05, 0.95),
        "Bottom Right": (0.95, 0.95),
        "Center": (0.5, 0.5),
    }

    def __init__(self):
        self.logo_image = None
        self.enabled = False
        self.position = "Top Right"
        self.size = 100
        self.opacity = 0.8
        self.margin = 20
        self.animation = "None"
        self._cached_logo = None

    def load_logo(self, filepath):
        """Load logo image."""
        try:
            self.logo_image = Image.open(filepath).convert("RGBA")
            self._cached_logo = None
            logger.info(f"Logo loaded: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load logo: {e}")
            return False

    def _get_resized_logo(self):
        if not self.logo_image:
            return None

        if self._cached_logo and self._cached_logo.size[0] == self.size:
            return self._cached_logo

        orig_w, orig_h = self.logo_image.size
        ratio = self.size / max(orig_w, orig_h)
        new_w = int(orig_w * ratio)
        new_h = int(orig_h * ratio)
        self._cached_logo = self.logo_image.resize((new_w, new_h), Image.LANCZOS)
        return self._cached_logo

    def render(self, frame_image, time_sec, duration):
        """Render logo onto frame."""
        if not self.enabled or not self.logo_image:
            return frame_image

        logo = self._get_resized_logo()
        if not logo:
            return frame_image

        logo = logo.copy()

        anim_opacity = self._get_animation_opacity(time_sec, duration)
        final_opacity = self.opacity * anim_opacity

        anim_scale = self._get_animation_scale(time_sec, duration)

        if anim_scale != 1.0:
            sw = int(logo.size[0] * anim_scale)
            sh = int(logo.size[1] * anim_scale)
            if sw > 0 and sh > 0:
                logo = logo.resize((sw, sh), Image.LANCZOS)

        if final_opacity < 1.0:
            alpha = logo.split()[3]
            alpha = alpha.point(lambda p: int(p * final_opacity))
            logo.putalpha(alpha)

        frame_w, frame_h = frame_image.size
        logo_w, logo_h = logo.size

        x_ratio, y_ratio = self.POSITION_MAP.get(self.position, (0.95, 0.05))

        if "Left" in self.position:
            x = self.margin
        elif "Right" in self.position:
            x = frame_w - logo_w - self.margin
        else:
            x = int(frame_w / 2 - logo_w / 2)

        if "Top" in self.position:
            y = self.margin
        elif "Bottom" in self.position:
            y = frame_h - logo_h - self.margin
        else:
            y = int(frame_h / 2 - logo_h / 2)

        result = frame_image.copy().convert("RGBA")
        result.paste(logo, (x, y), logo)
        return result

    def _get_animation_opacity(self, time_sec, duration):
        fade_dur = 1.0

        if self.animation == "Fade In":
            if time_sec < fade_dur:
                return time_sec / fade_dur
            return 1.0

        elif self.animation == "Fade Out":
            if time_sec > duration - fade_dur:
                return (duration - time_sec) / fade_dur
            return 1.0

        elif self.animation == "Pulse":
            return 0.7 + 0.3 * abs(math.sin(time_sec * 2))

        return 1.0

    def _get_animation_scale(self, time_sec, duration):
        if self.animation == "Zoom":
            if time_sec < 0.5:
                return 0.5 + time_sec
            return 1.0
        return 1.0
