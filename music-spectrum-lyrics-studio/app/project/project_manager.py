"""
Project manager - save/load project state, autosave, template management.
"""
import os
import json
import logging
import time
from datetime import datetime
from app.core.config import DIRS

logger = logging.getLogger(__name__)


class ProjectData:
    """Complete project state."""

    def __init__(self):
        self.name = "Untitled"
        self.audio_path = ""
        self.background_path = ""
        self.output_path = ""
        self.spectrum_style = "Bar Spectrum"
        self.spectrum_preset = "Neon Rainbow"
        self.spectrum_settings = {}
        self.spectrum_position = {"x": 0.5, "y": 0.95}
        self.karaoke_mode = "Karaoke Word Highlight"
        self.karaoke_preset = "TikTok Modern Lyrics"
        self.karaoke_settings = {}
        self.lyrics_position = {"x": 0.5, "y": 0.75}
        self.lyrics_source = ""
        self.sync_offset = 0.0
        self.logo_path = ""
        self.logo_enabled = False
        self.logo_settings = {}
        self.cta_enabled = False
        self.cta_settings = {}
        self.resolution_width = 1920
        self.resolution_height = 1080
        self.fps = 30
        self.aspect_ratio = "16:9 YouTube"
        self.quality_mode = "Balanced"
        self.ffmpeg_preset = "medium"
        self.whisper_model = "Auto Best Model"
        self.whisper_device = "auto"
        self.whisper_compute_type = "auto"
        self.whisper_language = "auto"
        self.created_at = datetime.now().isoformat()
        self.modified_at = datetime.now().isoformat()

    def to_dict(self):
        self.modified_at = datetime.now().isoformat()
        return {
            "name": self.name,
            "audio_path": self.audio_path,
            "background_path": self.background_path,
            "output_path": self.output_path,
            "spectrum_style": self.spectrum_style,
            "spectrum_preset": self.spectrum_preset,
            "spectrum_settings": self.spectrum_settings,
            "spectrum_position": self.spectrum_position,
            "karaoke_mode": self.karaoke_mode,
            "karaoke_preset": self.karaoke_preset,
            "karaoke_settings": self.karaoke_settings,
            "lyrics_position": self.lyrics_position,
            "lyrics_source": self.lyrics_source,
            "sync_offset": self.sync_offset,
            "logo_path": self.logo_path,
            "logo_enabled": self.logo_enabled,
            "logo_settings": self.logo_settings,
            "cta_enabled": self.cta_enabled,
            "cta_settings": self.cta_settings,
            "resolution_width": self.resolution_width,
            "resolution_height": self.resolution_height,
            "fps": self.fps,
            "aspect_ratio": self.aspect_ratio,
            "quality_mode": self.quality_mode,
            "ffmpeg_preset": self.ffmpeg_preset,
            "whisper_model": self.whisper_model,
            "whisper_device": self.whisper_device,
            "whisper_compute_type": self.whisper_compute_type,
            "whisper_language": self.whisper_language,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }

    @classmethod
    def from_dict(cls, data):
        proj = cls()
        for key, value in data.items():
            if hasattr(proj, key):
                setattr(proj, key, value)
        return proj


class ProjectManager:
    """Manage project files and autosave."""

    def __init__(self):
        self.current_project = ProjectData()
        self.project_file = None
        self.autosave_enabled = True
        self.autosave_interval = 60
        self._last_autosave = 0

    def new_project(self):
        self.current_project = ProjectData()
        self.project_file = None

    def save_project(self, filepath=None):
        """Save project to JSON file."""
        if filepath:
            self.project_file = filepath
        elif not self.project_file:
            name = self.current_project.name or "untitled"
            self.project_file = os.path.join(DIRS["projects"], f"{name}.json")

        os.makedirs(os.path.dirname(self.project_file), exist_ok=True)
        with open(self.project_file, "w", encoding="utf-8") as f:
            json.dump(self.current_project.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Project saved: {self.project_file}")
        return self.project_file

    def load_project(self, filepath):
        """Load project from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.current_project = ProjectData.from_dict(data)
        self.project_file = filepath
        logger.info(f"Project loaded: {filepath}")
        return self.current_project

    def autosave(self):
        """Perform autosave if enabled and interval has passed."""
        if not self.autosave_enabled:
            return
        now = time.time()
        if now - self._last_autosave < self.autosave_interval:
            return

        autosave_dir = os.path.join(DIRS["projects"], "autosave")
        os.makedirs(autosave_dir, exist_ok=True)
        name = self.current_project.name or "untitled"
        filepath = os.path.join(autosave_dir, f"{name}_autosave.json")

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.current_project.to_dict(), f, indent=2, ensure_ascii=False)
            self._last_autosave = now
        except Exception as e:
            logger.warning(f"Autosave failed: {e}")

    def list_projects(self):
        """List saved projects."""
        projects = []
        proj_dir = DIRS["projects"]
        if os.path.isdir(proj_dir):
            for fname in os.listdir(proj_dir):
                if fname.endswith(".json"):
                    projects.append(os.path.join(proj_dir, fname))
        return projects

    def delete_project(self, filepath):
        """Delete a project file."""
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Project deleted: {filepath}")

    def export_template(self, filepath):
        """Export current settings as a reusable template."""
        data = self.current_project.to_dict()
        data.pop("audio_path", None)
        data.pop("background_path", None)
        data.pop("output_path", None)
        data["type"] = "template"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Template exported: {filepath}")

    def import_template(self, filepath):
        """Import settings from a template."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        keep = {
            "audio_path": self.current_project.audio_path,
            "background_path": self.current_project.background_path,
            "output_path": self.current_project.output_path,
        }
        self.current_project = ProjectData.from_dict(data)
        for k, v in keep.items():
            setattr(self.current_project, k, v)
        logger.info(f"Template imported: {filepath}")
