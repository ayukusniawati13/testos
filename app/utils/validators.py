"""Input / configuration validators."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence, Tuple

from app.utils.file_utils import AUDIO_EXTS, IMAGE_EXTS, VIDEO_EXTS


class ValidationError(ValueError):
    """Raised when user-supplied data fails validation."""


def is_audio_file(path: Path | str) -> bool:
    return Path(path).suffix.lower() in AUDIO_EXTS


def is_image_file(path: Path | str) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTS


def is_video_file(path: Path | str) -> bool:
    return Path(path).suffix.lower() in VIDEO_EXTS


def ensure_exists(path: Path | str, label: str = "file") -> Path:
    p = Path(path)
    if not p.exists():
        raise ValidationError(f"{label} does not exist: {p}")
    return p


def ensure_audio(path: Path | str) -> Path:
    p = ensure_exists(path, "audio file")
    if not is_audio_file(p):
        raise ValidationError(
            f"Unsupported audio extension '{p.suffix}'. "
            f"Allowed: {', '.join(AUDIO_EXTS)}"
        )
    return p


def ensure_resolution(value: Sequence[int]) -> Tuple[int, int]:
    if len(value) != 2:
        raise ValidationError("Resolution must be (width, height).")
    width, height = int(value[0]), int(value[1])
    if width <= 0 or height <= 0:
        raise ValidationError("Resolution components must be positive.")
    if width % 2 or height % 2:
        # H.264/H.265 require even dimensions.
        raise ValidationError("Resolution width/height must be even numbers.")
    return width, height


def ensure_fps(fps: int) -> int:
    if fps not in (24, 25, 30, 50, 60):
        raise ValidationError(
            f"Unsupported fps {fps}. Choose one of 24, 25, 30, 50, 60."
        )
    return fps


def ensure_choice(value: str, choices: Iterable[str], label: str = "value") -> str:
    choices_list = list(choices)
    if value not in choices_list:
        raise ValidationError(
            f"Invalid {label} '{value}'. Allowed: {', '.join(choices_list)}"
        )
    return value
