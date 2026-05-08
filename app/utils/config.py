"""Application configuration storage.

Configuration is persisted as JSON under
``~/.spectrum_lyric_video_maker/config.json``. The class exposes
:meth:`AppConfig.get`/:meth:`set`/:meth:`save` as a thin layer on top of a
dict so feature modules can read defaults without hard dependencies.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from app.utils import file_utils


CONFIG_DIR_NAME = ".spectrum_lyric_video_maker"
CONFIG_FILE_NAME = "config.json"


def default_config() -> Dict[str, Any]:
    root = file_utils.project_root()
    return {
        "version": 1,
        "ffmpeg_path": "",  # auto-detected when empty
        "output_dir": str((root / "output").resolve()),
        "temp_dir": str((root / "temp").resolve()),
        "presets_dir": str((root / "presets").resolve()),
        "log_level": "INFO",
        "render": {
            "resolution": [1920, 1080],
            "fps": 30,
            "codec": "h264",
            "preset": "medium",
            "crf": 20,
            "video_bitrate": "",  # empty = use CRF
            "audio_bitrate": "192k",
        },
        "spectrum": {
            "style": "bar",
            "color_mode": "gradient",
            "primary_color": "#7c5cff",
            "secondary_color": "#21d4fd",
            "smoothing": 0.6,
            "bar_count": 64,
            "x": 0.5,
            "y": 0.85,
            "scale": 1.0,
            "rotation": 0.0,
            "opacity": 1.0,
            "anchor": "center",
            "effects": {
                "glow": True,
                "blur": False,
                "shadow": True,
                "pulse": True,
                "particle": False,
                "reflection": False,
            },
        },
        "lyrics": {
            "enabled": True,
            "model": "base",
            "language": "auto",
            "display_mode": "highlight",  # line / karaoke / highlight / fade
            "font_family": "Inter",
            "font_size": 56,
            "font_color": "#ffffff",
            "highlight_color": "#21d4fd",
            "outline_color": "#000000",
            "y_position": 0.7,
        },
        "background": {
            "type": "solid",  # solid / gradient / image / video / folder
            "color": "#0f1116",
            "gradient": ["#0f1116", "#1f2233"],
            "fit_mode": "cover",
        },
        "logo": {
            "enabled": False,
            "path": "",
            "position": "bottom_right",
            "x": 0.95,
            "y": 0.95,
            "size": 0.12,
            "opacity": 0.85,
            "margin": 24,
            "fade_in": 0.5,
            "fade_out": 0.5,
        },
        "animation_overlay": {
            "enabled": False,
            "path": "",
            "placement": "start",  # start / middle / end / custom
            "start_at": 0.0,
            "duration": 3.0,
            "opacity": 1.0,
            "blend": "normal",
        },
        "batch": {
            "match_strategy": "random",  # random / same_name / by_orientation / one_for_all
            "shared_background": "",
        },
    }


def _config_path() -> Path:
    return Path.home() / CONFIG_DIR_NAME / CONFIG_FILE_NAME


@dataclass
class AppConfig:
    """Lightweight typed wrapper around the on-disk JSON config."""

    data: Dict[str, Any] = field(default_factory=default_config)
    path: Path = field(default_factory=_config_path)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "AppConfig":
        path = path or _config_path()
        if path.is_file():
            try:
                with path.open("r", encoding="utf-8") as fh:
                    raw = json.load(fh)
                merged = _deep_merge(default_config(), raw)
                return cls(data=merged, path=path)
            except (OSError, json.JSONDecodeError):
                pass
        return cls(data=default_config(), path=path)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2, sort_keys=False)

    # Convenience accessors --------------------------------------------------

    def get(self, dotted_key: str, default: Any = None) -> Any:
        node: Any = self.data
        for part in dotted_key.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    def set(self, dotted_key: str, value: Any) -> None:
        parts = dotted_key.split(".")
        node = self.data
        for part in parts[:-1]:
            if part not in node or not isinstance(node[part], dict):
                node[part] = {}
            node = node[part]
        node[parts[-1]] = value


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out
