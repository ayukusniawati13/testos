"""Reusable widgets for the application's main panels."""
from app.gui.widgets.animation_panel import AnimationPanel
from app.gui.widgets.audio_panel import AudioPanel
from app.gui.widgets.background_panel import BackgroundPanel
from app.gui.widgets.batch_panel import BatchPanel
from app.gui.widgets.log_panel import LogPanel
from app.gui.widgets.logo_panel import LogoPanel
from app.gui.widgets.lyric_panel import LyricPanel
from app.gui.widgets.preview_panel import PreviewPanel
from app.gui.widgets.render_panel import RenderPanel
from app.gui.widgets.sidebar import Sidebar
from app.gui.widgets.spectrum_panel import SpectrumPanel

__all__ = [
    "AnimationPanel",
    "AudioPanel",
    "BackgroundPanel",
    "BatchPanel",
    "LogPanel",
    "LogoPanel",
    "LyricPanel",
    "PreviewPanel",
    "RenderPanel",
    "Sidebar",
    "SpectrumPanel",
]
