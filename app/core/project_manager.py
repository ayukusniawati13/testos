"""Preset / project persistence.

A *preset* is a JSON snapshot of all visual / render settings for a single
project (spectrum + lyrics + render). Users can save / load them via the
Presets tab. Project files (``.slvm``) are JSON envelopes with metadata.
"""
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.utils import file_utils
from app.utils.logger import get_logger

logger = get_logger("project_manager")


PRESET_VERSION = 1
PROJECT_FILE_VERSION = 1


class ProjectManager:
    """Save / load presets and full project files."""

    def __init__(self, presets_dir: Path | str) -> None:
        self.presets_dir = file_utils.ensure_dir(Path(presets_dir))

    # ------------------------------------------------------------- presets

    def list_presets(self) -> List[Path]:
        return sorted(p for p in self.presets_dir.glob("*.json") if p.is_file())

    def save_preset(self, name: str, payload: Dict[str, Any]) -> Path:
        safe = file_utils.safe_filename(name)
        target = self.presets_dir / f"{safe}.json"
        target = file_utils.unique_path(target)
        data = {
            "version": PRESET_VERSION,
            "saved_at": datetime.utcnow().isoformat() + "Z",
            "payload": _to_jsonable(payload),
        }
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("Preset saved: %s", target)
        return target

    def load_preset(self, path: Path | str) -> Dict[str, Any]:
        p = Path(path)
        with p.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if isinstance(raw, dict) and "payload" in raw:
            return raw["payload"]
        return raw  # backward compatibility

    def delete_preset(self, path: Path | str) -> None:
        p = Path(path)
        if p.is_file():
            p.unlink()
            logger.info("Preset deleted: %s", p)

    # ----------------------------------------------------------- projects

    def save_project(self, target: Path | str, payload: Dict[str, Any]) -> Path:
        p = Path(target).with_suffix(".slvm.json")
        file_utils.ensure_dir(p.parent)
        data = {
            "version": PROJECT_FILE_VERSION,
            "saved_at": datetime.utcnow().isoformat() + "Z",
            "payload": _to_jsonable(payload),
        }
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info("Project saved: %s", p)
        return p

    def load_project(self, source: Path | str) -> Dict[str, Any]:
        with Path(source).open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        if isinstance(raw, dict) and "payload" in raw:
            return raw["payload"]
        return raw


def _to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(v) for v in value]
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    return str(value)
