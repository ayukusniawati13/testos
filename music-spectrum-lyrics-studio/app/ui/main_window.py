"""
Main application window - Music Spectrum Lyrics Studio.
"""
import os
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QStatusBar, QMenuBar, QMenu, QFileDialog, QMessageBox,
    QSplitter, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction

from app.core.config import APP_NAME, APP_VERSION, DIRS, QUALITY_MODES, ensure_dirs
from app.ui.styles import DARK_THEME
from app.ui.components.audio_panel import AudioPanel
from app.ui.components.background_panel import BackgroundPanel
from app.ui.components.spectrum_panel import SpectrumPanel
from app.ui.components.karaoke_panel import KaraokePanel
from app.ui.components.lyrics_panel import LyricsPanel
from app.ui.components.logo_panel import LogoPanel
from app.ui.components.cta_panel import CTAPanel
from app.ui.components.render_panel import RenderPanel
from app.ui.components.batch_folder_panel import BatchFolderPanel
from app.ui.components.log_panel import LogPanel
from app.ui.components.settings_panel import SettingsPanel

from app.project.project_manager import ProjectManager
from app.lyrics.karaoke_engine import KaraokeEngine
from app.visual.spectrum_renderer import SpectrumRenderer
from app.visual.logo_manager import LogoManager
from app.visual.cta_animation_manager import CTAManager

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1100, 750)
        self.resize(1280, 800)

        ensure_dirs()

        self.project_manager = ProjectManager()
        self.karaoke_engine = KaraokeEngine()
        self.logo_manager = LogoManager()
        self.cta_manager = CTAManager()
        self.audio_analyzer = None
        self.lyrics_data = None
        self.audio_duration = 0.0

        self._analysis_thread = None
        self._transcription_thread = None
        self._render_thread = None
        self._batch_thread = None

        self._setup_ui()
        self._setup_menu()
        self._setup_statusbar()
        self._connect_signals()
        self._init_checks()

        self.setStyleSheet(DARK_THEME)

        self._autosave_timer = QTimer()
        self._autosave_timer.timeout.connect(self._autosave)
        self._autosave_timer.start(60000)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)

        header = QLabel(APP_NAME)
        header.setObjectName("headerLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        self.tabs = QTabWidget()

        # Audio tab
        self.audio_panel = AudioPanel()
        audio_scroll = self._scrollable(self.audio_panel)
        self.tabs.addTab(audio_scroll, "Music")

        # Background tab
        self.bg_panel = BackgroundPanel()
        bg_scroll = self._scrollable(self.bg_panel)
        self.tabs.addTab(bg_scroll, "Background")

        # Spectrum tab
        self.spectrum_panel = SpectrumPanel()
        spec_scroll = self._scrollable(self.spectrum_panel)
        self.tabs.addTab(spec_scroll, "Spectrum")

        # Lyrics tab
        self.lyrics_panel = LyricsPanel()
        lyrics_scroll = self._scrollable(self.lyrics_panel)
        self.tabs.addTab(lyrics_scroll, "Lyrics")

        # Karaoke tab
        self.karaoke_panel = KaraokePanel()
        karaoke_scroll = self._scrollable(self.karaoke_panel)
        self.tabs.addTab(karaoke_scroll, "Karaoke")

        # Logo tab
        self.logo_panel = LogoPanel()
        logo_scroll = self._scrollable(self.logo_panel)
        self.tabs.addTab(logo_scroll, "Logo")

        # CTA tab
        self.cta_panel = CTAPanel()
        cta_scroll = self._scrollable(self.cta_panel)
        self.tabs.addTab(cta_scroll, "CTA")

        # Render tab
        self.render_panel = RenderPanel()
        render_scroll = self._scrollable(self.render_panel)
        self.tabs.addTab(render_scroll, "Render")

        # Batch tab
        self.batch_panel = BatchFolderPanel()
        batch_scroll = self._scrollable(self.batch_panel)
        self.tabs.addTab(batch_scroll, "Batch")

        # Log tab
        self.log_panel = LogPanel()
        self.tabs.addTab(self.log_panel, "Log")

        # Settings tab
        self.settings_panel = SettingsPanel()
        settings_scroll = self._scrollable(self.settings_panel)
        self.tabs.addTab(settings_scroll, "Settings")

        main_layout.addWidget(self.tabs)

    def _scrollable(self, widget):
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        return scroll

    def _setup_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_action = QAction("New Project", self)
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)

        open_action = QAction("Open Project", self)
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)

        save_action = QAction("Save Project", self)
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save Project As...", self)
        save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        export_template = QAction("Export Template", self)
        export_template.triggered.connect(self._export_template)
        file_menu.addAction(export_template)

        import_template = QAction("Import Template", self)
        import_template.triggered.connect(self._import_template)
        file_menu.addAction(import_template)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_statusbar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _connect_signals(self):
        self.audio_panel.audio_selected.connect(self._on_audio_selected)
        self.lyrics_panel.generate_requested.connect(self._generate_lyrics)
        self.karaoke_panel.sync_requested.connect(self._generate_lyrics)
        self.karaoke_panel.resync_requested.connect(self._generate_lyrics)
        self.karaoke_panel.shift_requested.connect(self._shift_lyrics)
        self.karaoke_panel.btn_reset_sync.clicked.connect(self._reset_sync)
        self.render_panel.render_requested.connect(self._start_render)
        self.render_panel.preview_requested.connect(self._start_preview)
        self.render_panel.cancel_requested.connect(self._cancel_render)
        self.batch_panel.batch_start_requested.connect(self._start_batch)
        self.batch_panel.batch_cancel_requested.connect(self._cancel_batch)
        self.lyrics_panel.btn_clear_cache.clicked.connect(self._clear_whisper_cache)
        self.lyrics_panel.btn_export_lrc.clicked.connect(self._export_lrc)
        self.lyrics_panel.btn_export_srt.clicked.connect(self._export_srt)
        self.lyrics_panel.import_requested.connect(self._import_lyrics_file)

    def _init_checks(self):
        try:
            self.log_panel.check_ffmpeg()
        except Exception as e:
            logger.warning(f"FFmpeg check failed: {e}")
        try:
            self.log_panel.update_system_info()
        except Exception as e:
            logger.warning(f"System info check failed: {e}")
        logger.info(f"{APP_NAME} v{APP_VERSION} started")

    def _on_audio_selected(self, path):
        try:
            logger.info(f"Audio selected: {path}")
            self.status_bar.showMessage(f"Loading: {os.path.basename(path)}")

            from app.lyrics.metadata_lyrics_extractor import MetadataLyricsExtractor
            extractor = MetadataLyricsExtractor(path)
            self.lyrics_data = extractor.extract_metadata()

            self.audio_panel.update_metadata(self.lyrics_data)
            if self.lyrics_data:
                self.lyrics_panel.update_source(self.lyrics_data.source)
                if self.lyrics_data.raw_text:
                    self.lyrics_panel.set_lyrics_text(self.lyrics_data.raw_text)
                elif self.lyrics_data.lines:
                    text = "\n".join(l.text for l in self.lyrics_data.lines)
                    self.lyrics_panel.set_lyrics_text(text)

            from app.audio.analyzer import AudioAnalysisThread
            self._analysis_thread = AudioAnalysisThread(path, cache_dir=DIRS["cache"])
            self._analysis_thread.progress.connect(
                lambda p, m: self.status_bar.showMessage(f"Analysis: {m} ({p}%)")
            )
            self._analysis_thread.finished.connect(self._on_analysis_done)
            self._analysis_thread.error.connect(
                lambda e: self._show_error("Analysis Error", e)
            )
            self._analysis_thread.start()
        except Exception as e:
            self._show_error("Audio Load Error", str(e))

    def _on_analysis_done(self, analyzer):
        try:
            self.audio_analyzer = analyzer
            self.audio_duration = analyzer.duration
            self.audio_panel.update_duration(self.audio_duration)
            self.render_panel.update_estimates(self.audio_duration)
            self.status_bar.showMessage(
                f"Ready - Duration: {self.audio_duration:.1f}s, "
                f"Tempo: {analyzer.tempo:.0f} BPM"
            )
            logger.info(f"Analysis complete: {self.audio_duration:.1f}s, {analyzer.tempo:.0f} BPM")
        except Exception as e:
            self._show_error("Analysis Error", str(e))

    def _generate_lyrics(self):
        try:
            audio_path = self.audio_panel.get_audio_path()
            if not audio_path:
                self._show_error("Error", "Please select a music file first")
                return

            if self.lyrics_data and self.lyrics_data.has_synced:
                reply = QMessageBox.question(
                    self, "Lyrics Found",
                    "Synchronized lyrics already exist. Re-generate with AI?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    self.karaoke_engine.set_lyrics(self.lyrics_data)
                    quality, detail = self.karaoke_engine.get_sync_quality()
                    self.karaoke_panel.update_sync_quality(quality, detail)
                    return

            lyrics_settings = self.lyrics_panel.get_settings()
            self.status_bar.showMessage("Generating lyrics with AI...")
            logger.info(f"Starting transcription: model={lyrics_settings['model']}")

            from app.lyrics.whisper_engine import TranscriptionThread
            self._transcription_thread = TranscriptionThread(
                audio_path=audio_path,
                model_name=lyrics_settings["model"],
                device=lyrics_settings["device"],
                compute_type=lyrics_settings["compute_type"],
                language=lyrics_settings["language"],
                word_timestamps=lyrics_settings["word_timestamp"],
                cache_dir=DIRS["cache"],
            )
            self._transcription_thread.progress.connect(
                lambda p, m: self.status_bar.showMessage(f"Lyrics: {m} ({p}%)")
            )
            self._transcription_thread.finished.connect(self._on_lyrics_done)
            self._transcription_thread.error.connect(
                lambda e: self._show_error("Transcription Error", e)
            )
            self._transcription_thread.start()
        except Exception as e:
            self._show_error("Lyrics Error", str(e))

    def _on_lyrics_done(self, lyrics_data):
        try:
            self.lyrics_data = lyrics_data
            self.karaoke_engine.set_lyrics(lyrics_data)
            self.lyrics_panel.update_source(lyrics_data.source)

            text = "\n".join(l.text for l in lyrics_data.lines)
            self.lyrics_panel.set_lyrics_text(text)

            quality, detail = self.karaoke_engine.get_sync_quality()
            self.karaoke_panel.update_sync_quality(quality, detail)

            self.status_bar.showMessage(f"Lyrics ready: {len(lyrics_data.lines)} lines - {quality}")
            logger.info(f"Lyrics generated: {len(lyrics_data.lines)} lines, quality={quality}")
        except Exception as e:
            self._show_error("Lyrics Error", str(e))

    def _shift_lyrics(self, offset):
        try:
            self.karaoke_engine.shift_all(offset)
            self.status_bar.showMessage(f"Lyrics shifted by {offset:+.1f}s (total: {self.karaoke_engine.sync_offset:+.2f}s)")
        except Exception as e:
            self._show_error("Shift Error", str(e))

    def _reset_sync(self):
        try:
            self.karaoke_engine.reset_sync()
            self.status_bar.showMessage("Sync reset")
        except Exception as e:
            self._show_error("Reset Error", str(e))

    def _import_lyrics_file(self, path):
        try:
            from app.lyrics.metadata_lyrics_extractor import MetadataLyricsExtractor
            extractor = MetadataLyricsExtractor(path)
            ext_data = extractor._parse_external_lyrics(path)
            if ext_data and ext_data.lines:
                self.lyrics_data = ext_data
                self.karaoke_engine.set_lyrics(ext_data)
                self.lyrics_panel.update_source(ext_data.source)
                text = "\n".join(l.text for l in ext_data.lines)
                self.lyrics_panel.set_lyrics_text(text)
                quality, detail = self.karaoke_engine.get_sync_quality()
                self.karaoke_panel.update_sync_quality(quality, detail)
                self.status_bar.showMessage(f"Lyrics imported: {len(ext_data.lines)} lines")
            else:
                self._show_error("Import Error", "Failed to parse lyrics file")
        except Exception as e:
            self._show_error("Import Error", str(e))

    def _start_render(self):
        try:
            audio_path = self.audio_panel.get_audio_path()
            if not audio_path:
                self._show_error("Error", "Please select a music file first")
                return
            if not self.audio_analyzer:
                self._show_error("Error", "Audio analysis not complete")
                return

            render_settings = self.render_panel.get_settings()
            spectrum_settings = self.spectrum_panel.get_settings()
            karaoke_settings = self.karaoke_panel.get_settings()
            logo_settings = self.logo_panel.get_settings()
            cta_settings = self.cta_panel.get_settings()

            name = os.path.splitext(os.path.basename(audio_path))[0]
            output_path = os.path.join(render_settings["output_dir"], f"{name}.mp4")

            from app.render.video_renderer import VideoRenderer, RenderThread
            renderer = VideoRenderer(render_settings)
            renderer.set_audio(audio_path, self.audio_analyzer, self.audio_duration)
            renderer.set_background(self.bg_panel.get_background_path())
            renderer.set_output(output_path)

            spectrum = SpectrumRenderer(
                render_settings["width"], render_settings["height"],
                spectrum_settings.get("style", "Bar Spectrum"),
                low_spec=render_settings["quality_mode"] == "Low Spec"
            )
            spectrum.apply_preset(spectrum_settings)
            spectrum.position = {
                "x": spectrum_settings.get("position_x", 0.5),
                "y": spectrum_settings.get("position_y", 0.95),
            }
            renderer.spectrum_renderer = spectrum

            self.karaoke_engine.mode = karaoke_settings.get("mode", "Karaoke Word Highlight")
            self.karaoke_engine.settings.update({
                "font_family": karaoke_settings.get("font_family", "Arial"),
                "font_size": karaoke_settings.get("font_size", 42),
                "normal_color": karaoke_settings.get("normal_color", "#888888"),
                "highlight_color": karaoke_settings.get("highlight_color", "#ffffff"),
                "outline_color": karaoke_settings.get("outline_color", "#000000"),
                "outline_thickness": karaoke_settings.get("outline_thickness", 2),
                "glow_effect": karaoke_settings.get("glow_effect", False),
                "glow_intensity": karaoke_settings.get("glow_intensity", 0.5),
                "transition_speed": karaoke_settings.get("transition_speed", 0.3),
                "line_spacing": karaoke_settings.get("line_spacing", 1.4),
            })
            self.karaoke_engine.position = {
                "x": karaoke_settings.get("lyrics_position_x", 0.5),
                "y": karaoke_settings.get("lyrics_position_y", 0.75),
            }
            renderer.karaoke_engine = self.karaoke_engine

            if logo_settings.get("enabled") and logo_settings.get("path"):
                self.logo_manager.enabled = True
                self.logo_manager.load_logo(logo_settings["path"])
                self.logo_manager.position = logo_settings.get("position", "Top Right")
                self.logo_manager.size = logo_settings.get("size", 100)
                self.logo_manager.opacity = logo_settings.get("opacity", 0.8)
                self.logo_manager.margin = logo_settings.get("margin", 20)
                self.logo_manager.animation = logo_settings.get("animation", "None")
                renderer.logo_manager = self.logo_manager

            if cta_settings.get("enabled"):
                self.cta_manager.enabled = True
                self.cta_manager.cta_type = cta_settings.get("type", "Subscribe")
                self.cta_manager.custom_text = cta_settings.get("custom_text", "")
                self.cta_manager.timing = cta_settings.get("timing", "End")
                self.cta_manager.custom_timestamp = cta_settings.get("custom_timestamp", 0)
                self.cta_manager.duration_sec = cta_settings.get("duration", 5)
                self.cta_manager.preset = cta_settings.get("preset", "Subscribe Button Pop Up")
                self.cta_manager.position = cta_settings.get("position", "Bottom Right")
                self.cta_manager.size = cta_settings.get("size", 200)
                self.cta_manager.opacity = cta_settings.get("opacity", 0.9)
                self.cta_manager.fade_in = cta_settings.get("fade_in", True)
                self.cta_manager.fade_out = cta_settings.get("fade_out", True)
                self.cta_manager.loop = cta_settings.get("loop", False)
                if cta_settings.get("custom_path"):
                    self.cta_manager.load_custom_animation(cta_settings["custom_path"])
                self.cta_manager.chroma_key_enabled = cta_settings.get("chroma_key", False)
                renderer.cta_manager = self.cta_manager

            self._render_thread = RenderThread(renderer)
            self._render_thread.progress.connect(self.render_panel.update_progress)
            self._render_thread.finished.connect(self._on_render_done)
            self._render_thread.error.connect(lambda e: self._show_error("Render Error", e))
            self._render_thread.start()

            self.render_panel.btn_render.setEnabled(False)
            self.render_panel.btn_cancel.setEnabled(True)
            self.status_bar.showMessage("Rendering...")
        except Exception as e:
            self._show_error("Render Error", str(e))

    def _on_render_done(self, output_path):
        try:
            self.render_panel.btn_render.setEnabled(True)
            self.render_panel.btn_cancel.setEnabled(False)
            self.status_bar.showMessage(f"Render complete: {output_path}")
            logger.info(f"Render complete: {output_path}")
            QMessageBox.information(self, "Render Complete", f"Video saved to:\n{output_path}")
        except Exception as e:
            logger.error(f"Render done handler error: {e}")

    def _cancel_render(self):
        try:
            if self._render_thread:
                self._render_thread.cancel()
                self.render_panel.btn_render.setEnabled(True)
                self.render_panel.btn_cancel.setEnabled(False)
                self.status_bar.showMessage("Render cancelled")
        except Exception as e:
            logger.error(f"Cancel render error: {e}")

    def _start_preview(self):
        self.status_bar.showMessage("Preview not available in this version. Use full render.")

    def _start_batch(self):
        try:
            batch_settings = self.batch_panel.get_settings()
            if not batch_settings["audio_folder"]:
                self._show_error("Error", "Please select a music folder")
                return

            render_settings = self.render_panel.get_settings()
            spectrum_settings = self.spectrum_panel.get_settings()
            karaoke_settings = self.karaoke_panel.get_settings()
            lyrics_settings = self.lyrics_panel.get_settings()

            merged = {**render_settings}
            merged["spectrum_style"] = spectrum_settings.get("style", "Bar Spectrum")
            merged["karaoke_mode"] = karaoke_settings.get("mode", "Karaoke Word Highlight")
            merged["whisper_model"] = lyrics_settings.get("model", "Auto Best Model")
            merged["device"] = lyrics_settings.get("device", "auto")
            merged["compute_type"] = lyrics_settings.get("compute_type", "auto")

            from app.render.batch_folder_renderer import BatchFolderRenderer, BatchRenderThread
            batch = BatchFolderRenderer()
            batch.audio_folder = batch_settings["audio_folder"]
            batch.background_folder = batch_settings.get("bg_folder", "")
            batch.output_folder = batch_settings.get("output_folder", DIRS["output"])
            batch.bg_mode = batch_settings.get("bg_mode", "Random Background")
            batch.auto_lyrics = batch_settings.get("auto_lyrics", True)
            batch.auto_sync = batch_settings.get("auto_sync", True)
            batch.use_metadata = batch_settings.get("use_metadata", True)

            jobs = batch.prepare_jobs()
            for job in jobs:
                self.batch_panel.update_job_status(job["index"], "Queued")

            self._batch_thread = BatchRenderThread(batch, merged)
            self._batch_thread.progress.connect(self.batch_panel.update_progress)
            self._batch_thread.job_started.connect(
                lambda idx, name: self.batch_panel.update_job_status(idx, "Rendering...")
            )
            self._batch_thread.job_finished.connect(
                lambda idx, name, path: self.batch_panel.update_job_status(idx, "Done")
            )
            self._batch_thread.job_error.connect(
                lambda idx, name, err: self.batch_panel.update_job_status(idx, f"Failed: {err[:50]}")
            )
            self._batch_thread.all_finished.connect(self._on_batch_done)
            self._batch_thread.error.connect(lambda e: self._show_error("Batch Error", e))
            self._batch_thread.start()

            self.batch_panel.btn_start.setEnabled(False)
            self.batch_panel.btn_cancel.setEnabled(True)
            self.status_bar.showMessage("Batch rendering...")
        except Exception as e:
            self._show_error("Batch Error", str(e))

    def _on_batch_done(self, report_path):
        try:
            self.batch_panel.btn_start.setEnabled(True)
            self.batch_panel.btn_cancel.setEnabled(False)
            self.status_bar.showMessage(f"Batch complete! Report: {report_path}")
            logger.info(f"Batch render complete: {report_path}")
            QMessageBox.information(self, "Batch Complete", f"Report saved to:\n{report_path}")
        except Exception as e:
            logger.error(f"Batch done handler error: {e}")

    def _cancel_batch(self):
        try:
            if self._batch_thread:
                self._batch_thread.cancel()
                self.batch_panel.btn_start.setEnabled(True)
                self.batch_panel.btn_cancel.setEnabled(False)
                self.status_bar.showMessage("Batch cancelled")
        except Exception as e:
            logger.error(f"Cancel batch error: {e}")

    def _clear_whisper_cache(self):
        try:
            from app.lyrics.whisper_engine import WhisperEngine
            WhisperEngine.clear_model_cache()
            self.status_bar.showMessage("Model cache cleared")
        except Exception as e:
            self._show_error("Cache Error", str(e))

    def _export_lrc(self):
        try:
            if not self.lyrics_data:
                return
            path, _ = QFileDialog.getSaveFileName(self, "Export LRC", "", "LRC Files (*.lrc)")
            if path:
                self.karaoke_engine.export_lrc(path)
                self.status_bar.showMessage(f"LRC exported: {path}")
        except Exception as e:
            self._show_error("Export Error", str(e))

    def _export_srt(self):
        try:
            if not self.lyrics_data:
                return
            path, _ = QFileDialog.getSaveFileName(self, "Export SRT", "", "SRT Files (*.srt)")
            if path:
                self.karaoke_engine.export_srt(path)
                self.status_bar.showMessage(f"SRT exported: {path}")
        except Exception as e:
            self._show_error("Export Error", str(e))

    def _new_project(self):
        self.project_manager.new_project()
        self.status_bar.showMessage("New project created")

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", DIRS["projects"], "Project Files (*.json)"
        )
        if path:
            try:
                self.project_manager.load_project(path)
                self.status_bar.showMessage(f"Project loaded: {path}")
            except Exception as e:
                self._show_error("Load Error", str(e))

    def _save_project(self):
        try:
            path = self.project_manager.save_project()
            self.status_bar.showMessage(f"Project saved: {path}")
        except Exception as e:
            self._show_error("Save Error", str(e))

    def _save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", DIRS["projects"], "Project Files (*.json)"
        )
        if path:
            try:
                self.project_manager.save_project(path)
                self.status_bar.showMessage(f"Project saved: {path}")
            except Exception as e:
                self._show_error("Save Error", str(e))

    def _export_template(self):
        try:
            path, _ = QFileDialog.getSaveFileName(
                self, "Export Template", DIRS["presets"], "Template Files (*.json)"
            )
            if path:
                self.project_manager.export_template(path)
                self.status_bar.showMessage(f"Template exported: {path}")
        except Exception as e:
            self._show_error("Export Error", str(e))

    def _import_template(self):
        try:
            path, _ = QFileDialog.getOpenFileName(
                self, "Import Template", DIRS["presets"], "Template Files (*.json)"
            )
            if path:
                self.project_manager.import_template(path)
                self.status_bar.showMessage(f"Template imported: {path}")
        except Exception as e:
            self._show_error("Import Error", str(e))

    def _autosave(self):
        try:
            self.project_manager.autosave()
        except Exception as e:
            logger.warning(f"Autosave failed: {e}")

    def _show_about(self):
        QMessageBox.about(
            self, "About",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "Professional music video creator with audio spectrum\n"
            "visualization and karaoke-style synchronized lyrics.\n\n"
            "Features:\n"
            "- Multiple spectrum visualization styles\n"
            "- 20 karaoke display modes\n"
            "- AI-powered lyrics generation (Whisper/WhisperX)\n"
            "- Logo/watermark overlay\n"
            "- CTA animation support\n"
            "- Batch folder rendering\n"
            "- Low spec mode for older hardware"
        )

    def _show_error(self, title, message):
        logger.error(f"{title}: {message}")
        QMessageBox.critical(self, title, message)
        self.status_bar.showMessage(f"Error: {message[:100]}")

    def closeEvent(self, event):
        try:
            self.project_manager.autosave()
        except Exception as e:
            logger.warning(f"Autosave on close failed: {e}")
        try:
            from app.utils.helpers import clean_temp_files
            clean_temp_files(DIRS["temp"])
        except Exception as e:
            logger.warning(f"Temp cleanup failed: {e}")
        event.accept()
