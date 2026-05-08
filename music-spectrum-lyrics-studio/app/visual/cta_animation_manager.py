"""
CTA (Call to Action) animation manager.
Supports built-in presets and custom CTA animations.
"""
import math
import logging
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

logger = logging.getLogger(__name__)


class CTAManager:
    """Manage CTA overlays with animation."""

    def __init__(self):
        self.enabled = False
        self.cta_type = "Subscribe"
        self.custom_text = ""
        self.timing = "End"
        self.custom_timestamp = 0.0
        self.duration_sec = 5.0
        self.preset = "Subscribe Button Pop Up"
        self.position = "Bottom Right"
        self.size = 200
        self.opacity = 0.9
        self.fade_in = True
        self.fade_out = True
        self.loop = False
        self.play_once = True
        self.custom_animation_path = None
        self.custom_animation_frames = None
        self.chroma_key_enabled = False
        self.chroma_key_color = "#00ff00"
        self.chroma_key_threshold = 40

    def get_cta_text(self):
        if self.cta_type == "Custom":
            return self.custom_text or "Subscribe"
        return self.cta_type

    def get_start_time(self, video_duration):
        """Calculate when CTA should start showing."""
        if self.timing == "Start":
            return 0.0
        elif self.timing == "Middle":
            return video_duration / 2 - self.duration_sec / 2
        elif self.timing == "End":
            return max(0, video_duration - self.duration_sec - 2.0)
        elif self.timing == "Custom Timestamp":
            return self.custom_timestamp
        return max(0, video_duration - self.duration_sec)

    def is_visible(self, time_sec, video_duration):
        """Check if CTA should be visible at given time."""
        if not self.enabled:
            return False
        start = self.get_start_time(video_duration)
        end = start + self.duration_sec
        return start <= time_sec <= end

    def load_custom_animation(self, filepath):
        """Load custom CTA animation (GIF, WEBM, PNG sequence)."""
        try:
            ext = os.path.splitext(filepath)[1].lower()
            if ext == ".gif":
                self._load_gif(filepath)
            elif ext in [".png", ".jpg", ".jpeg"]:
                self.custom_animation_frames = [Image.open(filepath).convert("RGBA")]
            else:
                self.custom_animation_path = filepath
            logger.info(f"Custom CTA loaded: {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load CTA: {e}")
            return False

    def _load_gif(self, filepath):
        """Load GIF frames."""
        gif = Image.open(filepath)
        frames = []
        try:
            while True:
                frames.append(gif.copy().convert("RGBA"))
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass
        self.custom_animation_frames = frames

    def render(self, frame_image, time_sec, video_duration):
        """Render CTA onto frame."""
        if not self.is_visible(time_sec, video_duration):
            return frame_image

        start = self.get_start_time(video_duration)
        local_time = time_sec - start
        progress = local_time / self.duration_sec

        if self.custom_animation_frames:
            return self._render_custom(frame_image, local_time, progress)
        return self._render_builtin(frame_image, local_time, progress)

    def _render_builtin(self, frame_image, local_time, progress):
        """Render built-in CTA preset."""
        overlay = Image.new("RGBA", frame_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        text = self.get_cta_text()
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except Exception:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

        btn_w = tw + 40
        btn_h = th + 20
        frame_w, frame_h = frame_image.size

        x, y = self._get_cta_position(frame_w, frame_h, btn_w, btn_h)

        opacity = self._get_opacity(local_time)

        if "Pop" in self.preset or "Bounce" in self.preset:
            scale = self._bounce_scale(local_time)
            btn_w = int(btn_w * scale)
            btn_h = int(btn_h * scale)

        if "Slide" in self.preset:
            x = self._slide_x(x, frame_w, local_time)

        btn_color = (255, 0, 0, int(220 * opacity))
        text_color = (255, 255, 255, int(255 * opacity))

        draw.rounded_rectangle(
            [x, y, x + btn_w, y + btn_h],
            radius=8, fill=btn_color
        )
        text_x = x + (btn_w - tw) // 2
        text_y = y + (btn_h - th) // 2
        draw.text((text_x, text_y), text, font=font, fill=text_color)

        return Image.alpha_composite(frame_image.convert("RGBA"), overlay)

    def _render_custom(self, frame_image, local_time, progress):
        """Render custom CTA animation."""
        frames = self.custom_animation_frames
        if not frames:
            return frame_image

        frame_idx = int(local_time * 10) % len(frames)
        if not self.loop and frame_idx >= len(frames):
            frame_idx = len(frames) - 1
        cta_frame = frames[frame_idx].copy()

        if self.chroma_key_enabled:
            cta_frame = self._apply_chroma_key(cta_frame)

        ratio = self.size / max(cta_frame.size)
        new_w = int(cta_frame.size[0] * ratio)
        new_h = int(cta_frame.size[1] * ratio)
        cta_frame = cta_frame.resize((new_w, new_h), Image.LANCZOS)

        opacity = self._get_opacity(local_time)
        if opacity < 1.0:
            alpha = cta_frame.split()[3]
            alpha = alpha.point(lambda p: int(p * opacity))
            cta_frame.putalpha(alpha)

        frame_w, frame_h = frame_image.size
        x, y = self._get_cta_position(frame_w, frame_h, new_w, new_h)

        result = frame_image.copy().convert("RGBA")
        result.paste(cta_frame, (x, y), cta_frame)
        return result

    def _apply_chroma_key(self, image):
        """Simple chroma key (green screen removal)."""
        import numpy as np
        data = np.array(image)
        key_color = self._hex_to_rgb(self.chroma_key_color)
        threshold = self.chroma_key_threshold

        diff = np.sqrt(np.sum((data[:, :, :3].astype(float) - key_color) ** 2, axis=2))
        mask = diff < threshold
        data[mask, 3] = 0
        return Image.fromarray(data)

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip("#")
        return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

    def _get_cta_position(self, frame_w, frame_h, cta_w, cta_h):
        positions = {
            "Top Left": (20, 20),
            "Top Right": (frame_w - cta_w - 20, 20),
            "Bottom Left": (20, frame_h - cta_h - 20),
            "Bottom Right": (frame_w - cta_w - 20, frame_h - cta_h - 20),
            "Center": (frame_w // 2 - cta_w // 2, frame_h // 2 - cta_h // 2),
        }
        return positions.get(self.position, (frame_w - cta_w - 20, frame_h - cta_h - 20))

    def _get_opacity(self, local_time):
        fade_dur = 0.5
        opacity = self.opacity

        if self.fade_in and local_time < fade_dur:
            opacity *= local_time / fade_dur
        if self.fade_out and local_time > self.duration_sec - fade_dur:
            opacity *= (self.duration_sec - local_time) / fade_dur

        return max(0, min(1, opacity))

    def _bounce_scale(self, local_time):
        if local_time < 0.3:
            return 0.5 + local_time / 0.3 * 0.7
        elif local_time < 0.5:
            return 1.2 - (local_time - 0.3) / 0.2 * 0.2
        return 1.0

    def _slide_x(self, target_x, frame_w, local_time):
        if local_time < 0.5:
            return int(frame_w + (target_x - frame_w) * (local_time / 0.5))
        return target_x
