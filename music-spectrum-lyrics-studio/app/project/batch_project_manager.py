"""
Batch project manager - manage batch render configurations.
"""
import os
import json
import logging
from app.core.config import DIRS

logger = logging.getLogger(__name__)


class BatchProjectManager:
    """Manage batch render project configurations."""

    def __init__(self):
        self.batch_configs_dir = os.path.join(DIRS["projects"], "batch")
        os.makedirs(self.batch_configs_dir, exist_ok=True)

    def save_batch_config(self, name, config):
        """Save a batch configuration."""
        filepath = os.path.join(self.batch_configs_dir, f"{name}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"Batch config saved: {filepath}")
        return filepath

    def load_batch_config(self, name):
        """Load a batch configuration."""
        filepath = os.path.join(self.batch_configs_dir, f"{name}.json")
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_batch_configs(self):
        """List available batch configurations."""
        configs = []
        for fname in os.listdir(self.batch_configs_dir):
            if fname.endswith(".json"):
                configs.append(os.path.splitext(fname)[0])
        return configs

    def delete_batch_config(self, name):
        """Delete a batch configuration."""
        filepath = os.path.join(self.batch_configs_dir, f"{name}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Batch config deleted: {name}")
            return True
        return False

    def create_default_config(self):
        """Create a default batch configuration dict."""
        return {
            "audio_folder": "",
            "background_folder": "",
            "output_folder": DIRS["output"],
            "bg_mode": "Random Background",
            "auto_lyrics": True,
            "auto_sync": True,
            "use_metadata": True,
            "logo_enabled": False,
            "cta_enabled": False,
            "spectrum_style": "Bar Spectrum",
            "spectrum_preset": "Neon Rainbow",
            "karaoke_mode": "Karaoke Word Highlight",
            "karaoke_preset": "TikTok Modern Lyrics",
            "resolution_width": 1920,
            "resolution_height": 1080,
            "fps": 30,
            "quality_mode": "Balanced",
            "whisper_model": "Auto Best Model",
        }
