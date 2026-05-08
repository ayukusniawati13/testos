"""
Application configuration and constants.
"""
import os
import json
import sys

APP_NAME = "Music Spectrum Lyrics Studio"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Music Spectrum Lyrics Studio"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DIRS = {
    "assets": os.path.join(BASE_DIR, "assets"),
    "icons": os.path.join(BASE_DIR, "assets", "icons"),
    "fonts": os.path.join(BASE_DIR, "assets", "fonts"),
    "cta": os.path.join(BASE_DIR, "assets", "cta"),
    "logos": os.path.join(BASE_DIR, "assets", "logos"),
    "samples": os.path.join(BASE_DIR, "assets", "samples"),
    "placeholders": os.path.join(BASE_DIR, "assets", "placeholders"),
    "presets": os.path.join(BASE_DIR, "presets"),
    "projects": os.path.join(BASE_DIR, "projects"),
    "output": os.path.join(BASE_DIR, "output"),
    "temp": os.path.join(BASE_DIR, "temp"),
    "cache": os.path.join(BASE_DIR, "cache"),
    "logs": os.path.join(BASE_DIR, "logs"),
    "config": os.path.join(BASE_DIR, "config"),
}

SETTINGS_FILE = os.path.join(DIRS["config"], "settings.json")

SUPPORTED_AUDIO = [".mp3", ".wav", ".m4a", ".flac"]
SUPPORTED_IMAGE_BG = [".jpg", ".jpeg", ".png", ".webp"]
SUPPORTED_VIDEO_BG = [".mp4", ".mov", ".webm", ".avi"]
SUPPORTED_BG = SUPPORTED_IMAGE_BG + SUPPORTED_VIDEO_BG
SUPPORTED_LOGO = [".png", ".jpg", ".jpeg"]
SUPPORTED_CTA = [".gif", ".webm", ".mp4", ".mov", ".png"]

AUDIO_FILTER = "Audio Files ({})".format(" ".join(f"*{e}" for e in SUPPORTED_AUDIO))
BG_FILTER = "Background Files ({})".format(" ".join(f"*{e}" for e in SUPPORTED_BG))
LOGO_FILTER = "Logo Files ({})".format(" ".join(f"*{e}" for e in SUPPORTED_LOGO))
CTA_FILTER = "CTA Files ({})".format(" ".join(f"*{e}" for e in SUPPORTED_CTA))

SPECTRUM_STYLES = [
    "Bar Spectrum",
    "Circular Spectrum",
    "Waveform",
    "Neon Spectrum",
    "Modern Visualizer",
    "Smooth Reactive Spectrum",
]

SPECTRUM_PRESETS = {
    "Neon Rainbow": {
        "gradient_colors": ["#ff0000", "#ff7700", "#ffff00", "#00ff00", "#0000ff", "#8b00ff"],
        "rainbow_mode": True, "neon_mode": True, "glow": True, "rounded": True,
        "bar_count": 64, "bar_width": 8, "bar_spacing": 3, "sensitivity": 1.2,
        "bass_boost": 1.5, "treble_reaction": 1.0, "max_height": 200,
    },
    "Cyberpunk": {
        "gradient_colors": ["#ff00ff", "#00ffff"],
        "rainbow_mode": False, "neon_mode": True, "glow": True, "rounded": False,
        "bar_count": 80, "bar_width": 6, "bar_spacing": 2, "sensitivity": 1.4,
        "bass_boost": 1.8, "treble_reaction": 1.2, "max_height": 220,
    },
    "Ocean Blue": {
        "gradient_colors": ["#001a33", "#004080", "#0080ff", "#00bfff"],
        "rainbow_mode": False, "neon_mode": False, "glow": True, "rounded": True,
        "bar_count": 48, "bar_width": 10, "bar_spacing": 4, "sensitivity": 1.0,
        "bass_boost": 1.2, "treble_reaction": 0.8, "max_height": 180,
    },
    "Sunset Glow": {
        "gradient_colors": ["#ff4500", "#ff6347", "#ff8c00", "#ffd700"],
        "rainbow_mode": False, "neon_mode": False, "glow": True, "rounded": True,
        "bar_count": 56, "bar_width": 9, "bar_spacing": 3, "sensitivity": 1.1,
        "bass_boost": 1.3, "treble_reaction": 1.0, "max_height": 190,
    },
    "Fire Beat": {
        "gradient_colors": ["#ff0000", "#ff4500", "#ff8c00", "#ffd700"],
        "rainbow_mode": False, "neon_mode": True, "glow": True, "rounded": False,
        "bar_count": 72, "bar_width": 7, "bar_spacing": 2, "sensitivity": 1.5,
        "bass_boost": 2.0, "treble_reaction": 1.3, "max_height": 250,
    },
    "Purple Night": {
        "gradient_colors": ["#2d0053", "#6a0dad", "#9b30ff", "#da70d6"],
        "rainbow_mode": False, "neon_mode": True, "glow": True, "rounded": True,
        "bar_count": 60, "bar_width": 8, "bar_spacing": 3, "sensitivity": 1.0,
        "bass_boost": 1.4, "treble_reaction": 0.9, "max_height": 200,
    },
    "Minimal Clean": {
        "gradient_colors": ["#ffffff", "#cccccc"],
        "rainbow_mode": False, "neon_mode": False, "glow": False, "rounded": True,
        "bar_count": 32, "bar_width": 12, "bar_spacing": 6, "sensitivity": 0.8,
        "bass_boost": 1.0, "treble_reaction": 0.7, "max_height": 150,
    },
    "Colorful Pop": {
        "gradient_colors": ["#ff1493", "#00ff7f", "#1e90ff", "#ffd700", "#ff4500"],
        "rainbow_mode": True, "neon_mode": False, "glow": True, "rounded": True,
        "bar_count": 64, "bar_width": 8, "bar_spacing": 3, "sensitivity": 1.3,
        "bass_boost": 1.6, "treble_reaction": 1.1, "max_height": 210,
    },
}

KARAOKE_MODES = [
    "Normal Lyrics",
    "Karaoke Line Highlight",
    "Karaoke Word Highlight",
    "Karaoke Smooth Sweep",
    "Karaoke Bounce Mode",
    "Karaoke Neon Glow Mode",
    "Karaoke Gradient Flow",
    "Karaoke Beat Reactive",
    "Karaoke Typewriter Mode",
    "Karaoke Slide Reveal",
    "Karaoke Wave Mode",
    "Karaoke Pulse Mode",
    "Karaoke Cinematic Mode",
    "Karaoke Split Lyrics Mode",
    "Karaoke Vertical Lyrics Mode",
    "Karaoke Floating Lyrics",
    "Karaoke Subtitle Professional",
    "Karaoke Dynamic Zoom",
    "Karaoke Multi Color Reactive",
    "Karaoke Fire/Particle Mode",
]

KARAOKE_PRESETS = {
    "EDM Neon Karaoke": {
        "mode": "Karaoke Neon Glow Mode",
        "font_size": 42, "highlight_color": "#00ffff", "normal_color": "#666666",
        "outline_color": "#000000", "outline_thickness": 2, "glow_effect": True,
        "glow_intensity": 0.8, "transition_speed": 0.3,
    },
    "TikTok Modern Lyrics": {
        "mode": "Karaoke Word Highlight",
        "font_size": 48, "highlight_color": "#ffffff", "normal_color": "#888888",
        "outline_color": "#000000", "outline_thickness": 3, "glow_effect": False,
        "transition_speed": 0.2,
    },
    "Anime Karaoke": {
        "mode": "Karaoke Smooth Sweep",
        "font_size": 38, "highlight_color": "#ff69b4", "normal_color": "#ffffff",
        "outline_color": "#000000", "outline_thickness": 2, "glow_effect": True,
        "glow_intensity": 0.5, "transition_speed": 0.25,
    },
    "Cyberpunk Glow": {
        "mode": "Karaoke Neon Glow Mode",
        "font_size": 44, "highlight_color": "#ff00ff", "normal_color": "#003333",
        "outline_color": "#00ffff", "outline_thickness": 2, "glow_effect": True,
        "glow_intensity": 1.0, "transition_speed": 0.35,
    },
    "LoFi Chill Lyrics": {
        "mode": "Karaoke Floating Lyrics",
        "font_size": 36, "highlight_color": "#ffeedd", "normal_color": "#aa8866",
        "outline_color": "#000000", "outline_thickness": 1, "glow_effect": False,
        "transition_speed": 0.5,
    },
    "Minimal Subtitle": {
        "mode": "Karaoke Subtitle Professional",
        "font_size": 32, "highlight_color": "#ffffff", "normal_color": "#cccccc",
        "outline_color": "#000000", "outline_thickness": 2, "glow_effect": False,
        "transition_speed": 0.15,
    },
    "Concert Style": {
        "mode": "Karaoke Beat Reactive",
        "font_size": 50, "highlight_color": "#ffdd00", "normal_color": "#ffffff",
        "outline_color": "#000000", "outline_thickness": 3, "glow_effect": True,
        "glow_intensity": 0.6, "transition_speed": 0.2,
    },
    "Night Drive Neon": {
        "mode": "Karaoke Gradient Flow",
        "font_size": 40, "highlight_color": "#ff4500", "normal_color": "#333333",
        "outline_color": "#ff6347", "outline_thickness": 2, "glow_effect": True,
        "glow_intensity": 0.7, "transition_speed": 0.3,
    },
    "Cinematic Clean": {
        "mode": "Karaoke Cinematic Mode",
        "font_size": 38, "highlight_color": "#ffffff", "normal_color": "#555555",
        "outline_color": "#000000", "outline_thickness": 1, "glow_effect": False,
        "transition_speed": 0.4,
    },
    "Bass Reactive Lyrics": {
        "mode": "Karaoke Multi Color Reactive",
        "font_size": 46, "highlight_color": "#00ff00", "normal_color": "#333333",
        "outline_color": "#000000", "outline_thickness": 2, "glow_effect": True,
        "glow_intensity": 0.9, "transition_speed": 0.2,
    },
}

POSITION_PRESETS = {
    "bottom": {"x": 0.5, "y": 0.9},
    "top": {"x": 0.5, "y": 0.1},
    "left": {"x": 0.1, "y": 0.5},
    "right": {"x": 0.9, "y": 0.5},
    "center": {"x": 0.5, "y": 0.5},
}

ASPECT_RATIOS = {
    "16:9 YouTube": (16, 9),
    "9:16 TikTok/Reels/Shorts": (9, 16),
    "1:1 Instagram Square": (1, 1),
    "4:5 Instagram Feed": (4, 5),
    "Custom": None,
}

RESOLUTIONS = {
    "360p": 360,
    "480p": 480,
    "720p HD": 720,
    "1080p Full HD": 1080,
    "1440p 2K": 1440,
    "2160p 4K": 2160,
}

PLATFORM_PRESETS = {
    "YouTube 1080p": {"width": 1920, "height": 1080, "fps": 30},
    "TikTok/Reels/Shorts": {"width": 1080, "height": 1920, "fps": 30},
    "Instagram Square": {"width": 1080, "height": 1080, "fps": 30},
    "Instagram Feed": {"width": 1080, "height": 1350, "fps": 30},
    "YouTube 4K": {"width": 3840, "height": 2160, "fps": 30},
}

QUALITY_MODES = {
    "Low Spec": {
        "preview_duration": 10,
        "preview_resolution": 480,
        "render_resolution": 720,
        "fps": 24,
        "ffmpeg_preset": "ultrafast",
        "glow_enabled": False,
        "reflection_enabled": False,
        "particle_enabled": False,
        "spectrum_detail": "low",
    },
    "Balanced": {
        "preview_duration": 15,
        "preview_resolution": 720,
        "render_resolution": 1080,
        "fps": 30,
        "ffmpeg_preset": "medium",
        "glow_enabled": True,
        "reflection_enabled": True,
        "particle_enabled": True,
        "spectrum_detail": "medium",
    },
    "High Quality": {
        "preview_duration": 20,
        "preview_resolution": 1080,
        "render_resolution": 1080,
        "fps": 60,
        "ffmpeg_preset": "slow",
        "glow_enabled": True,
        "reflection_enabled": True,
        "particle_enabled": True,
        "spectrum_detail": "high",
    },
}

WHISPER_MODELS = [
    "Auto Best Model",
    "Whisper Large",
    "Whisper Large-v3",
    "WhisperX High Accuracy",
    "Faster-Whisper Large",
    "Faster-Whisper Medium",
    "Faster-Whisper Small",
]

SYNC_ACCURACY_MODES = ["Fast Sync", "Balanced Sync", "High Accuracy Sync"]

LYRICS_SOURCES = [
    "Metadata Lyrics",
    "Synchronized Metadata",
    "External Lyrics File",
    "Whisper Generated",
    "WhisperX Synced",
    "Manual Lyrics",
]

LOGO_POSITIONS = [
    "Top Left", "Top Right", "Bottom Left", "Bottom Right", "Center",
]

LOGO_ANIMATIONS = ["None", "Fade In", "Fade Out", "Pulse", "Zoom"]

CTA_TYPES = ["Subscribe", "Like", "Share", "Comment", "Follow", "Custom"]
CTA_TIMING = ["Start", "Middle", "End", "Custom Timestamp"]
CTA_PRESETS = [
    "Subscribe Button Pop Up",
    "Like and Subscribe",
    "Bell Notification",
    "Smooth Slide In",
    "Bounce Subscribe",
    "Minimal Clean CTA",
    "YouTube Style Subscribe",
]

BATCH_BG_MODES = ["Random Background", "Sequential Background", "Match by Filename"]

DEFAULT_SETTINGS = {
    "quality_mode": "Balanced",
    "output_dir": DIRS["output"],
    "spectrum_style": "Bar Spectrum",
    "spectrum_preset": "Neon Rainbow",
    "spectrum_position": "bottom",
    "lyrics_position": "above_spectrum",
    "karaoke_mode": "Karaoke Word Highlight",
    "karaoke_preset": "TikTok Modern Lyrics",
    "whisper_model": "Auto Best Model",
    "sync_accuracy": "Balanced Sync",
    "device": "auto",
    "compute_type": "auto",
    "language": "auto",
    "word_level_timestamp": True,
    "forced_alignment": True,
    "aspect_ratio": "16:9 YouTube",
    "resolution": "1080p Full HD",
    "fps": 30,
    "logo_enabled": False,
    "logo_position": "Top Right",
    "logo_opacity": 0.8,
    "logo_size": 100,
    "cta_enabled": False,
    "cta_type": "Subscribe",
    "cta_timing": "End",
    "autosave": True,
    "theme": "dark",
}


def ensure_dirs():
    for d in DIRS.values():
        os.makedirs(d, exist_ok=True)


def load_settings():
    ensure_dirs()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            merged = {**DEFAULT_SETTINGS, **saved}
            return merged
        except Exception:
            return dict(DEFAULT_SETTINGS)
    return dict(DEFAULT_SETTINGS)


def save_settings(settings):
    ensure_dirs()
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to save settings: {e}")
