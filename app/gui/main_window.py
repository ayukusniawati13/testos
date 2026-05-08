"""Main application window: sidebar + stacked workspace + log dock."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.core.batch_processor import (
    BatchEntry,
    BatchProcessor,
    JobStatus,
    SUPPORTED_MATCH_STRATEGIES,
    match_backgrounds,
)
from app.core.ffmpeg_manager import FFmpegManager
from app.core.lyric_engine import LyricStyle
from app.core.project_manager import ProjectManager
from app.core.render_engine import (
    AnimationOverlaySpec,
    BackgroundSpec,
    LogoSpec,
    RenderEngine,
    RenderJob,
    RenderResult,
    RenderSettings,
)
from app.gui.dialogs import FFmpegDialog, PresetDialog, SettingsDialog
from app.gui.widgets import (
    AnimationPanel,
    AudioPanel,
    BackgroundPanel,
    BatchPanel,
    LogPanel,
    LogoPanel,
    LyricPanel,
    PreviewPanel,
    RenderPanel,
    Sidebar,
    SpectrumPanel,
)
from app.utils import file_utils, validators
from app.utils.config import AppConfig
from app.utils.logger import get_logger

logger = get_logger("main_window")


# --------------------------------------------------------------- workers


class _SingleRenderWorker(QObject):
    progress = Signal(float, str)
    log = Signal(str)
    finished = Signal(object)  # RenderResult

    def __init__(self, engine: RenderEngine, job: RenderJob) -> None:
        super().__init__()
        self.engine = engine
        self.job = job

    def run(self) -> None:
        result = self.engine.render(
            self.job,
            progress=self._on_progress,
            log_cb=self._on_log,
        )
        self.finished.emit(result)

    def _on_progress(self, pct: float, msg: str) -> None:
        self.progress.emit(pct, msg)

    def _on_log(self, msg: str) -> None:
        self.log.emit(msg)


# --------------------------------------------------------------- main window


class MainWindow(QMainWindow):
    """Top-level window orchestrating all panels."""

    PAGE_SINGLE = 0
    PAGE_BATCH = 1
    PAGE_PRESETS = 2
    PAGE_SETTINGS = 3
    PAGE_LOGS = 4

    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Spectrum Lyric Video Maker")
        self.resize(1400, 880)

        self.ffmpeg_manager = FFmpegManager(config)
        self.render_engine = RenderEngine(self.ffmpeg_manager)
        self.batch_processor = BatchProcessor(self.ffmpeg_manager)
        self.project_manager = ProjectManager(
            Path(config.get("presets_dir", str(file_utils.project_root() / "presets")))
        )

        # --- Build pages -----------------------------------------------------
        self.audio_panel = AudioPanel()
        self.lyric_panel = LyricPanel()
        self.spectrum_panel = SpectrumPanel()
        self.background_panel = BackgroundPanel()
        self.logo_panel = LogoPanel()
        self.animation_panel = AnimationPanel()
        self.render_panel = RenderPanel(default_output_dir=str(config.get("output_dir", "")))
        self.preview = PreviewPanel()
        self.batch_panel = BatchPanel()

        self.audio_panel.audio_changed.connect(self.lyric_panel.set_audio_path)
        for w in (
            self.spectrum_panel, self.background_panel, self.logo_panel,
            self.animation_panel, self.lyric_panel,
        ):
            if hasattr(w, "settings_changed"):
                w.settings_changed.connect(self._refresh_preview)
            elif hasattr(w, "track_changed"):
                w.track_changed.connect(lambda *_: self._refresh_preview())

        # --- Single project page --------------------------------------------
        single_page = self._build_single_project_page()

        # --- Batch page ------------------------------------------------------
        batch_page = self._build_batch_page()

        # --- Presets / Settings / Logs --------------------------------------
        presets_page = self._build_presets_page()
        settings_page = self._build_settings_page()
        log_page = self._build_log_page()

        self.stack = QStackedWidget()
        self.stack.addWidget(single_page)
        self.stack.addWidget(batch_page)
        self.stack.addWidget(presets_page)
        self.stack.addWidget(settings_page)
        self.stack.addWidget(log_page)

        self.sidebar = Sidebar([
            ("Single Project", "single"),
            ("Batch Mode", "batch"),
            ("Presets", "presets"),
            ("Settings", "settings"),
            ("Logs", "logs"),
        ])
        self.sidebar.page_changed.connect(self.stack.setCurrentIndex)

        # --- Central layout --------------------------------------------------
        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_layout.addWidget(self.sidebar)
        central_layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        # --- Toolbar / actions ----------------------------------------------
        self._build_actions()

        # --- Status bar ------------------------------------------------------
        self.status = QStatusBar()
        self.ffmpeg_status_label = QLabel("FFmpeg: checking...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setMaximumWidth(280)
        self.progress_bar.setVisible(False)
        self.status.addWidget(self.ffmpeg_status_label, 1)
        self.status.addPermanentWidget(self.progress_bar)
        self.setStatusBar(self.status)

        # Floating log dock (toggleable via the Logs page button as well).
        self.log_dock = QDockWidget("Logs", self)
        self.log_dock.setObjectName("LogsDock")
        self.log_dock.setWidget(self.log_panel)
        self.log_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetMovable
        )
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)
        self.log_dock.hide()

        # Wire batch UI to processor.
        self.batch_panel.build_queue.connect(self._on_batch_build)
        self.batch_panel.start_clicked.connect(self._on_batch_start)
        self.batch_panel.pause_clicked.connect(self.batch_processor.pause)
        self.batch_panel.resume_clicked.connect(self.batch_processor.resume)
        self.batch_panel.cancel_clicked.connect(self.batch_processor.cancel)
        self.batch_panel.clear_clicked.connect(self._on_batch_clear)
        self.batch_processor.on_status = self._on_batch_status
        self.batch_processor.on_progress = self._on_batch_progress
        self.batch_processor.on_log = lambda msg: self.log_panel.append_plain(msg)

        # Background workers.
        self._single_thread: Optional[QThread] = None
        self._single_worker: Optional[_SingleRenderWorker] = None

        # Initial state.
        self._refresh_ffmpeg_status()
        self._refresh_preview()

    # ------------------------------------------------------------ pages

    def _build_single_project_page(self) -> QWidget:
        """Two columns: scrollable settings + preview / actions."""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Left column (scroll area with all panels).
        left = QWidget()
        left_v = QVBoxLayout(left)
        left_v.setContentsMargins(0, 0, 0, 0)
        for panel in (
            self.audio_panel,
            self.lyric_panel,
            self.spectrum_panel,
            self.background_panel,
            self.logo_panel,
            self.animation_panel,
            self.render_panel,
        ):
            left_v.addWidget(panel)
        left_v.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(left)

        # Right column (preview + render button + small log).
        right = QWidget()
        right_v = QVBoxLayout(right)
        right_v.setContentsMargins(0, 0, 0, 0)
        right_v.addWidget(self.preview, 1)
        action_row = QHBoxLayout()
        self.btn_preview = QPushButton("Refresh Preview")
        self.btn_render = QPushButton("Render Video")
        self.btn_render.setObjectName("primary")
        self.btn_cancel_render = QPushButton("Cancel")
        self.btn_cancel_render.setEnabled(False)
        action_row.addWidget(self.btn_preview)
        action_row.addWidget(self.btn_render)
        action_row.addWidget(self.btn_cancel_render)
        action_row.addStretch(1)
        right_v.addLayout(action_row)

        self.log_panel = LogPanel()
        right_v.addWidget(self.log_panel, 1)

        self.btn_preview.clicked.connect(self._refresh_preview)
        self.btn_render.clicked.connect(self._on_single_render)
        self.btn_cancel_render.clicked.connect(self._on_cancel_single_render)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(scroll)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 5)
        layout.addWidget(splitter)
        return page

    def _build_batch_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.addWidget(self.batch_panel, 1)
        return page

    def _build_presets_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(20, 20, 20, 20)
        intro = QLabel(
            "Save and load full render presets (spectrum + lyrics + render settings)."
        )
        intro.setStyleSheet("color: #9aa0b3; font-size: 13px;")
        outer.addWidget(intro)
        actions = QHBoxLayout()
        self.btn_open_preset_dialog = QPushButton("Open preset manager")
        self.btn_open_preset_dialog.setObjectName("primary")
        actions.addWidget(self.btn_open_preset_dialog)
        actions.addStretch(1)
        outer.addLayout(actions)
        outer.addStretch(1)
        self.btn_open_preset_dialog.clicked.connect(self._open_preset_dialog)
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.addWidget(QLabel("App settings (paths, FFmpeg, log level)."))
        actions = QHBoxLayout()
        self.btn_open_ffmpeg = QPushButton("Open FFmpeg dialog")
        self.btn_open_settings = QPushButton("Edit settings...")
        actions.addWidget(self.btn_open_ffmpeg)
        actions.addWidget(self.btn_open_settings)
        actions.addStretch(1)
        outer.addLayout(actions)
        outer.addStretch(1)
        self.btn_open_ffmpeg.clicked.connect(self._open_ffmpeg_dialog)
        self.btn_open_settings.clicked.connect(self._open_settings_dialog)
        return page

    def _build_log_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.addWidget(QLabel("Application logs (mirrored to logs/app.log)."))
        outer.addWidget(self._build_log_view(), 1)
        return page

    def _build_log_view(self) -> QWidget:
        # Re-use the same LogPanel via a second instance so users see logs on
        # the dedicated page even when the dock is hidden.
        page_log = LogPanel()
        return page_log

    # ------------------------------------------------------------ actions

    def _build_actions(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setIconSize(toolbar.iconSize())
        self.addToolBar(toolbar)

        act_open = QAction("Open audio", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(lambda: self.audio_panel._on_browse())  # noqa: SLF001
        toolbar.addAction(act_open)

        act_render = QAction("Render", self)
        act_render.setShortcut(QKeySequence("Ctrl+R"))
        act_render.triggered.connect(self._on_single_render)
        toolbar.addAction(act_render)

        toolbar.addSeparator()

        act_ffmpeg = QAction("FFmpeg", self)
        act_ffmpeg.triggered.connect(self._open_ffmpeg_dialog)
        toolbar.addAction(act_ffmpeg)

        act_settings = QAction("Settings", self)
        act_settings.triggered.connect(self._open_settings_dialog)
        toolbar.addAction(act_settings)

        act_presets = QAction("Presets", self)
        act_presets.triggered.connect(self._open_preset_dialog)
        toolbar.addAction(act_presets)

        toolbar.addSeparator()

        act_toggle_log = QAction("Toggle log panel", self)
        act_toggle_log.setShortcut(QKeySequence("Ctrl+L"))
        act_toggle_log.triggered.connect(lambda: self.log_dock.setVisible(not self.log_dock.isVisible()))
        toolbar.addAction(act_toggle_log)

    # ------------------------------------------------------------ helpers

    def _refresh_ffmpeg_status(self) -> None:
        status = self.ffmpeg_manager.status(refresh=True)
        if status.installed:
            self.ffmpeg_status_label.setText(
                f"FFmpeg: installed  ·  {status.path}"
            )
            self.ffmpeg_status_label.setStyleSheet("color: #62d4a4;")
        else:
            self.ffmpeg_status_label.setText("FFmpeg: not found — open Settings → FFmpeg")
            self.ffmpeg_status_label.setStyleSheet("color: #ff7676;")

    def _refresh_preview(self) -> None:
        try:
            spec_cfg = self.spectrum_panel.to_config()
            background = self.background_panel.to_background()
            resolution = self.background_panel.to_resolution()
            lyric_style = self.lyric_panel.to_style()
            self.preview.render_preview(
                size=resolution,
                spectrum_config=spec_cfg,
                background=background,
                lyric_style=lyric_style,
                lyric_track=self.lyric_panel.get_track(),
                logo=self.logo_panel.to_spec(),
                animation=self.animation_panel.to_spec(),
            )
        except Exception as exc:  # pragma: no cover - tolerant
            logger.exception("Preview render failed: %s", exc)

    def _gather_job(self) -> Optional[RenderJob]:
        audio = self.audio_panel.get_path()
        if not audio:
            QMessageBox.information(self, "Audio missing", "Please load an audio file first.")
            return None
        try:
            audio_path = validators.ensure_audio(audio)
        except validators.ValidationError as exc:
            QMessageBox.critical(self, "Invalid audio", str(exc))
            return None

        resolution = self.background_panel.to_resolution()
        settings = self.render_panel.to_settings(resolution=resolution)
        output_dir = Path(self.render_panel.get_output_dir() or self.config.get("output_dir", "output"))
        file_utils.ensure_dir(output_dir)
        target = output_dir / f"{audio_path.stem}.mp4"
        target = file_utils.unique_path(target)

        return RenderJob(
            audio_path=audio_path,
            output_path=target,
            settings=settings,
            spectrum_config=self.spectrum_panel.to_config(),
            lyric_style=self.lyric_panel.to_style(),
            lyric_track=self.lyric_panel.get_track(),
            background=self.background_panel.to_background(),
            logo=self.logo_panel.to_spec(),
            animation=self.animation_panel.to_spec(),
            transcribe_if_missing=self.lyric_panel.to_style().enabled and self.lyric_panel.get_track().is_empty(),
            whisper_model=self.lyric_panel.get_model(),
            language=self.lyric_panel.get_language(),
        )

    # ------------------------------------------------------------ single render

    def _on_single_render(self) -> None:
        if self._single_thread is not None and self._single_thread.isRunning():
            return
        if not self.ffmpeg_manager.status().installed:
            self._open_ffmpeg_dialog()
            return
        job = self._gather_job()
        if job is None:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.btn_render.setEnabled(False)
        self.btn_cancel_render.setEnabled(True)

        worker = _SingleRenderWorker(self.render_engine, job)
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._on_single_progress)
        worker.log.connect(self.log_panel.append_plain)
        worker.finished.connect(self._on_single_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._single_thread = thread
        self._single_worker = worker
        thread.start()

    def _on_single_progress(self, pct: float, msg: str) -> None:
        self.progress_bar.setValue(int(pct * 100))
        self.status.showMessage(msg, 5000)

    def _on_single_finished(self, result: RenderResult) -> None:
        self.btn_render.setEnabled(True)
        self.btn_cancel_render.setEnabled(False)
        self.progress_bar.setVisible(False)
        self._single_thread = None
        self._single_worker = None
        if result.success and result.output_path:
            QMessageBox.information(
                self, "Render complete",
                f"Saved to:\n{result.output_path}",
            )
        else:
            QMessageBox.critical(
                self, "Render failed", result.error or "Unknown failure",
            )

    def _on_cancel_single_render(self) -> None:
        self.render_engine.cancel()

    # ------------------------------------------------------------ batch

    def _on_batch_build(self, audio_folder: str, bg_folder: str, strategy: str, shared_bg: str) -> None:
        if not audio_folder or not Path(audio_folder).is_dir():
            QMessageBox.information(self, "Folder required", "Select a music folder first.")
            return
        audios = file_utils.list_audio_files(audio_folder)
        if not audios:
            QMessageBox.information(self, "No audio", "The chosen folder contains no audio files.")
            return
        backgrounds = file_utils.list_background_files(bg_folder) if bg_folder else []
        shared_path = Path(shared_bg) if shared_bg else None
        mapping = match_backgrounds(audios, backgrounds, strategy, shared_background=shared_path)

        self.batch_processor.clear()
        output_dir = Path(self.render_panel.get_output_dir() or self.config.get("output_dir", "output"))
        file_utils.ensure_dir(output_dir)

        spec_cfg = self.spectrum_panel.to_config()
        lyric_style = self.lyric_panel.to_style()
        render_settings = self.render_panel.to_settings(resolution=self.background_panel.to_resolution())
        base_bg = self.background_panel.to_background()

        for audio in audios:
            chosen_bg = mapping.get(audio)
            bg = BackgroundSpec(
                type="image" if chosen_bg and chosen_bg.suffix.lower() in file_utils.IMAGE_EXTS
                else "video" if chosen_bg and chosen_bg.suffix.lower() in file_utils.VIDEO_EXTS
                else base_bg.type,
                color=base_bg.color,
                gradient=list(base_bg.gradient),
                path=str(chosen_bg) if chosen_bg else base_bg.path,
                fit_mode=base_bg.fit_mode,
            )
            target = file_utils.unique_path(output_dir / f"{audio.stem}.mp4")
            job = RenderJob(
                audio_path=audio,
                output_path=target,
                settings=render_settings,
                spectrum_config=spec_cfg,
                lyric_style=lyric_style,
                background=bg,
                logo=self.logo_panel.to_spec(),
                animation=self.animation_panel.to_spec(),
                transcribe_if_missing=lyric_style.enabled,
                whisper_model=self.lyric_panel.get_model(),
                language=self.lyric_panel.get_language(),
            )
            self.batch_processor.add(job)

        self.batch_panel.set_table_entries(self.batch_processor.entries())
        self.status.showMessage(f"Built queue: {len(audios)} job(s)", 5000)

    def _on_batch_start(self) -> None:
        if not self.ffmpeg_manager.status().installed:
            self._open_ffmpeg_dialog()
            return
        self.batch_processor.start()

    def _on_batch_clear(self) -> None:
        self.batch_processor.cancel()
        self.batch_processor.clear()

    def _on_batch_status(self, idx: int, entry: BatchEntry) -> None:
        self.batch_panel.update_entry(idx, entry)

    def _on_batch_progress(self, idx: int, pct: float, message: str) -> None:
        self.batch_panel.update_progress(idx, pct, message)

    # ------------------------------------------------------------ dialogs

    def _open_ffmpeg_dialog(self) -> None:
        dlg = FFmpegDialog(self.ffmpeg_manager, parent=self)
        dlg.exec()
        self._refresh_ffmpeg_status()

    def _open_settings_dialog(self) -> None:
        dlg = SettingsDialog(self.config, parent=self)
        if dlg.exec():
            self._refresh_ffmpeg_status()

    def _open_preset_dialog(self) -> None:
        payload = {
            "spectrum": self.spectrum_panel.to_config().__dict__,
            "lyrics": {
                "enabled": self.lyric_panel.enabled.isChecked(),
                "display_mode": self.lyric_panel.display_mode.currentText(),
                "font_family": self.lyric_panel.font_family.currentText(),
                "font_size": int(self.lyric_panel.font_size.value()),
                "y_position": float(self.lyric_panel.y_position.value()),
                "fade_seconds": float(self.lyric_panel.fade_seconds.value()),
                "model": self.lyric_panel.get_model(),
                "language": self.lyric_panel.get_language(),
            },
            "render": {
                "fps": int(self.render_panel.fps.currentText()),
                "codec": self.render_panel.codec.currentText(),
                "preset": self.render_panel.preset.currentText(),
                "crf": int(self.render_panel.crf.value()),
                "video_bitrate": self.render_panel.bitrate.text(),
                "audio_bitrate": self.render_panel.audio_bitrate.text(),
            },
            "background": self.background_panel.to_background().__dict__,
            "logo": self.logo_panel.to_spec().__dict__,
            "animation": self.animation_panel.to_spec().__dict__,
        }
        dlg = PresetDialog(self.project_manager, payload, parent=self)
        if dlg.exec() and dlg.selected_payload is not None:
            self._apply_preset(dlg.selected_payload)

    def _apply_preset(self, payload: dict) -> None:
        try:
            if isinstance(payload.get("spectrum"), dict):
                self.spectrum_panel.load_dict(payload["spectrum"])
            if isinstance(payload.get("lyrics"), dict):
                self.lyric_panel.load_dict(payload["lyrics"])
            if isinstance(payload.get("render"), dict):
                self.render_panel.load_dict(payload["render"])
            if isinstance(payload.get("background"), dict):
                self.background_panel.load_dict(payload["background"])
            if isinstance(payload.get("logo"), dict):
                self.logo_panel.load_dict(payload["logo"])
            if isinstance(payload.get("animation"), dict):
                self.animation_panel.load_dict(payload["animation"])
        except Exception as exc:  # pragma: no cover - tolerant
            logger.exception("Failed to apply preset: %s", exc)
        self._refresh_preview()

    # ------------------------------------------------------------ qt

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API
        self.batch_processor.cancel()
        self.render_engine.cancel()
        super().closeEvent(event)
