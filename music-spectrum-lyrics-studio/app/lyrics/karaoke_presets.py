"""
Karaoke style presets management.
"""
import os
import json
import logging
from app.core.config import KARAOKE_PRESETS, DIRS

logger = logging.getLogger(__name__)


class KaraokePresetsManager:
    """Manage karaoke style presets."""

    def __init__(self):
        self.presets = dict(KARAOKE_PRESETS)
        self._load_custom_presets()

    def _load_custom_presets(self):
        preset_dir = os.path.join(DIRS["presets"], "karaoke")
        if not os.path.isdir(preset_dir):
            return
        for fname in os.listdir(preset_dir):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(preset_dir, fname), "r", encoding="utf-8") as f:
                        preset = json.load(f)
                    name = preset.get("name", os.path.splitext(fname)[0])
                    self.presets[name] = preset
                except Exception as e:
                    logger.warning(f"Failed to load preset {fname}: {e}")

    def get_preset(self, name):
        return self.presets.get(name, {})

    def get_preset_names(self):
        return list(self.presets.keys())

    def save_preset(self, name, settings):
        preset_dir = os.path.join(DIRS["presets"], "karaoke")
        os.makedirs(preset_dir, exist_ok=True)
        settings["name"] = name
        filepath = os.path.join(preset_dir, f"{name}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        self.presets[name] = settings
        logger.info(f"Saved karaoke preset: {name}")

    def delete_preset(self, name):
        if name in KARAOKE_PRESETS:
            logger.warning(f"Cannot delete built-in preset: {name}")
            return False
        preset_dir = os.path.join(DIRS["presets"], "karaoke")
        filepath = os.path.join(preset_dir, f"{name}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
        self.presets.pop(name, None)
        return True
