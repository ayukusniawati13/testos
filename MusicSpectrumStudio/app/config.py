"""Configuration model and persistence."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any

from .constants import API_KEYS_PATH, CONFIG_PATH

logger = logging.getLogger(__name__)


@dataclass
class ApiKeyEntry:
    label: str = ""
    key: str = ""
    enabled: bool = True


@dataclass
class LogoConfig:
    path: str = ""
    enabled: bool = False
    circular: bool = True
    size_pct: float = 12.0  # percentage of width
    x_pct: float = 4.0      # left margin
    y_pct: float = 4.0      # top margin
    anchor: str = "top_left"  # top_left, top_right, bottom_left, bottom_right, center
    opacity: float = 1.0


@dataclass
class SpectrumConfig:
    style: str = "Bars Modern"
    color_a: str = "#7C4DFF"
    color_b: str = "#00E5FF"
    sensitivity: float = 1.0
    smoothing: float = 0.65
    height_pct: float = 30.0
    position: str = "bottom"  # bottom, center, top
    bar_count: int = 64


@dataclass
class LyricsConfig:
    enabled: bool = True
    style: str = "Centered Modern"
    font_family: str = "Inter"
    font_size: int = 56
    primary_color: str = "#FFFFFF"
    accent_color: str = "#FFD54F"
    outline_color: str = "#000000"
    outline_width: int = 4
    fade_ms: int = 350
    position: str = "bottom"  # bottom, top, center
    max_lines: int = 2
    line_gap_seconds: float = 0.6  # gap that triggers hide between lines
    margin_pct: float = 8.0


@dataclass
class BackgroundConfig:
    files: list[str] = field(default_factory=list)
    enabled_multi: bool = False
    crossfade_seconds: float = 1.5
    cycle_seconds: float = 8.0
    blur: int = 0
    darken: float = 0.25
    fit_mode: str = "cover"  # cover, contain
    color: str = "#0B0F1A"  # fallback


@dataclass
class EffectsConfig:
    sparkle: bool = False
    sparkle_intensity: float = 0.5
    glow: bool = True
    glow_strength: float = 0.5
    vignette: bool = True
    vignette_strength: float = 0.4
    grain: bool = False
    grain_strength: float = 0.15
    beat_flash: bool = False
    light_leaks: bool = False


@dataclass
class BatchConfig:
    enabled: bool = False
    music_folder: str = ""
    background_folder: str = ""
    background_match: str = "order"  # order, name, random


@dataclass
class TranscribeConfig:
    model: str = "whisper-large-v3-turbo"
    language: str = ""  # blank = auto
    ai_correct: bool = True
    correct_model: str = "llama-3.3-70b-versatile"


@dataclass
class RenderConfig:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    crf: int = 18
    preset: str = "medium"
    audio_bitrate: str = "192k"


@dataclass
class AppConfig:
    audio_file: str = ""
    output_dir: str = ""
    spectrum: SpectrumConfig = field(default_factory=SpectrumConfig)
    lyrics: LyricsConfig = field(default_factory=LyricsConfig)
    background: BackgroundConfig = field(default_factory=BackgroundConfig)
    effects: EffectsConfig = field(default_factory=EffectsConfig)
    logo: LogoConfig = field(default_factory=LogoConfig)
    batch: BatchConfig = field(default_factory=BatchConfig)
    transcribe: TranscribeConfig = field(default_factory=TranscribeConfig)
    render: RenderConfig = field(default_factory=RenderConfig)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppConfig:
        cfg = cls()
        for k, v in data.items():
            if not hasattr(cfg, k):
                continue
            current = getattr(cfg, k)
            if hasattr(current, "__dataclass_fields__") and isinstance(v, dict):
                _populate_dataclass(current, v)
            else:
                setattr(cfg, k, v)
        return cfg

    def save(self, path: str | None = None) -> None:
        target = path or CONFIG_PATH
        try:
            with open(target, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
        except OSError as exc:
            logger.warning("Failed to save config: %s", exc)

    @classmethod
    def load(cls, path: str | None = None) -> AppConfig:
        target = path or CONFIG_PATH
        try:
            with open(target, encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except FileNotFoundError:
            return cls()
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load config (%s); using defaults", exc)
            return cls()


def _populate_dataclass(target: Any, data: dict[str, Any]) -> None:
    for k, v in data.items():
        if hasattr(target, k):
            setattr(target, k, v)


def load_api_keys() -> list[ApiKeyEntry]:
    try:
        with open(API_KEYS_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        return [ApiKeyEntry(**item) for item in raw if isinstance(item, dict)]
    except FileNotFoundError:
        return []
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        logger.warning("Failed to load api keys (%s)", exc)
        return []


def save_api_keys(keys: list[ApiKeyEntry]) -> None:
    try:
        with open(API_KEYS_PATH, "w", encoding="utf-8") as f:
            json.dump([asdict(k) for k in keys], f, indent=2)
    except OSError as exc:
        logger.warning("Failed to save api keys: %s", exc)
