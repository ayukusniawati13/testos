"""Main window orchestrating all sub-panels."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .. import APP_NAME, __version__
from ..config import ApiKeyEntry, AppConfig, load_api_keys, save_api_keys
from ..core.batch import build_batch
from ..core.groq_client import GroqClient
from ..core.transcribe import TranscriptionResult
from ..utils.paths import safe_stem
from ..workers.render_worker import RenderJob, RenderWorker
from ..workers.transcribe_worker import TranscribeWorker
from .api_keys_widget import ApiKeysWidget
from .ffmpeg_widget import FfmpegStatusBar
from .preview_widget import PreviewWidget
from .settings_widgets import (
    AudioPanel,
    BackgroundPanel,
    BatchPanel,
    EffectsPanel,
    LogoPanel,
    LyricsPanel,
    RenderPanel,
    SpectrumPanel,
    TranscribePanel,
)

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{__version__}")
        self.resize(1500, 920)

        self.config = AppConfig.load()
        self._api_keys: list[ApiKeyEntry] = load_api_keys()
        self.groq_client = GroqClient()
        self._refresh_groq_keys()

        self.transcription: TranscriptionResult | None = None
        self._render_worker: RenderWorker | None = None
        self._transcribe_worker: TranscribeWorker | None = None

        self._build_ui()
        self._wire_signals()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.setInterval(450)
        self._refresh_timer.timeout.connect(self._refresh_preview)

        # initial preview
        QTimer.singleShot(150, self._refresh_preview)

    # ----- UI ---------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QSplitter(Qt.Horizontal)
        root.setHandleWidth(8)

        # ---- LEFT panel (scrollable settings) ----
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)

        header = QLabel(APP_NAME)
        header.setProperty("role", "title")
        left_layout.addWidget(header)

        self.ffmpeg_bar = FfmpegStatusBar()
        left_layout.addWidget(self.ffmpeg_bar)

        self.api_keys_widget = ApiKeysWidget(self._get_api_keys, self._set_api_keys)
        left_layout.addWidget(self.api_keys_widget)

        self.tabs = QTabWidget()
        left_layout.addWidget(self.tabs, stretch=1)

        # tab: Music & Lyrics
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        tab1_layout.setSpacing(10)
        self.audio_panel = AudioPanel(self.config)
        self.transcribe_panel = TranscribePanel(self.config.transcribe)
        tab1_layout.addWidget(self.audio_panel)
        tab1_layout.addWidget(self.transcribe_panel)
        tab1_layout.addWidget(self._wrap_lyric_log())
        tab1_layout.addStretch()
        self.tabs.addTab(self._scrollable(tab1), "Musik & Lirik")

        # tab: Visualizer
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        tab2_layout.setSpacing(10)
        self.spectrum_panel = SpectrumPanel(self.config.spectrum)
        self.effects_panel = EffectsPanel(self.config.effects)
        tab2_layout.addWidget(self.spectrum_panel)
        tab2_layout.addWidget(self.effects_panel)
        tab2_layout.addStretch()
        self.tabs.addTab(self._scrollable(tab2), "Spectrum & Efek")

        # tab: Style / overlay
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        tab3_layout.setSpacing(10)
        self.lyrics_panel = LyricsPanel(self.config.lyrics)
        self.logo_panel = LogoPanel(self.config.logo)
        tab3_layout.addWidget(self.lyrics_panel)
        tab3_layout.addWidget(self.logo_panel)
        tab3_layout.addStretch()
        self.tabs.addTab(self._scrollable(tab3), "Lirik & Logo")

        # tab: Background
        tab4 = QWidget()
        tab4_layout = QVBoxLayout(tab4)
        self.background_panel = BackgroundPanel(self.config.background)
        tab4_layout.addWidget(self.background_panel)
        tab4_layout.addStretch()
        self.tabs.addTab(self._scrollable(tab4), "Background")

        # tab: Batch
        tab5 = QWidget()
        tab5_layout = QVBoxLayout(tab5)
        self.batch_panel = BatchPanel(self.config.batch)
        tab5_layout.addWidget(self.batch_panel)
        tab5_layout.addStretch()
        self.tabs.addTab(self._scrollable(tab5), "Batch")

        # ---- RIGHT panel (preview + render) ----
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)

        preview_title = QLabel("Preview")
        preview_title.setProperty("role", "title")
        right_layout.addWidget(preview_title)

        self.preview = PreviewWidget()
        right_layout.addWidget(self.preview, stretch=1)

        self.render_panel = RenderPanel(self.config.render)
        right_layout.addWidget(self.render_panel)

        action_row = QHBoxLayout()
        self.render_btn = QPushButton("Render Video")
        self.render_btn.setProperty("success", True)
        self.render_btn.clicked.connect(self._on_render)
        self.cancel_btn = QPushButton("Batal")
        self.cancel_btn.setProperty("danger", True)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_render)
        action_row.addWidget(self.render_btn, stretch=1)
        action_row.addWidget(self.cancel_btn)
        right_layout.addLayout(action_row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        right_layout.addWidget(self.progress)

        root.addWidget(left)
        root.addWidget(right)
        root.setSizes([760, 740])

        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Siap")

    @staticmethod
    def _scrollable(widget: QWidget) -> QScrollArea:
        area = QScrollArea()
        area.setWidget(widget)
        area.setWidgetResizable(True)
        area.setFrameShape(QScrollArea.NoFrame)
        return area

    def _wrap_lyric_log(self) -> QWidget:
        from PySide6.QtWidgets import QGroupBox

        box = QGroupBox("Hasil Lirik")
        layout = QVBoxLayout(box)
        self.lyric_log = QTextEdit()
        self.lyric_log.setReadOnly(True)
        self.lyric_log.setPlaceholderText(
            "Tekan tombol Generate Lirik untuk transkripsi otomatis dengan Groq Whisper.\n"
            "Hasil + timestamp akan muncul di sini."
        )
        layout.addWidget(self.lyric_log)

        actions = QHBoxLayout()
        save_srt = QPushButton("Export SRT")
        save_srt.setProperty("secondary", True)
        save_srt.clicked.connect(self._export_srt)
        save_lrc = QPushButton("Export LRC")
        save_lrc.setProperty("secondary", True)
        save_lrc.clicked.connect(self._export_lrc)
        actions.addWidget(save_srt)
        actions.addWidget(save_lrc)
        actions.addStretch()
        layout.addLayout(actions)
        return box

    # ----- signal wiring ----------------------------------------------------
    def _wire_signals(self) -> None:
        self.preview.requestRefresh.connect(self._schedule_preview)
        self.audio_panel.audioChanged.connect(self._on_audio_changed)
        self.audio_panel.generateLyricsRequested.connect(self._generate_lyrics)
        self.api_keys_widget.keysChanged.connect(self._on_keys_changed)

        for panel in (
            self.transcribe_panel,
            self.spectrum_panel,
            self.effects_panel,
            self.lyrics_panel,
            self.logo_panel,
            self.background_panel,
            self.batch_panel,
            self.render_panel,
        ):
            panel.changed.connect(self._schedule_preview)

    # ----- API key plumbing -------------------------------------------------
    def _get_api_keys(self) -> list[ApiKeyEntry]:
        return list(self._api_keys)

    def _set_api_keys(self, keys: list[ApiKeyEntry]) -> None:
        self._api_keys = keys
        save_api_keys(keys)
        self._refresh_groq_keys()

    def _on_keys_changed(self) -> None:
        self._refresh_groq_keys()

    def _refresh_groq_keys(self) -> None:
        active = [(k.label, k.key) for k in self._api_keys if k.enabled and k.key]
        self.groq_client.set_keys(active)

    # ----- transcription ----------------------------------------------------
    def _on_audio_changed(self, _path: str) -> None:
        self.transcription = None
        self.lyric_log.clear()
        self._schedule_preview()

    def _generate_lyrics(self) -> None:
        if not self.config.audio_file or not os.path.exists(self.config.audio_file):
            QMessageBox.warning(self, "Audio belum dipilih", "Silakan pilih file musik terlebih dahulu.")
            return
        if not self.groq_client.has_keys():
            QMessageBox.warning(
                self,
                "API key Groq belum ada",
                "Tambahkan minimal satu Groq API key di panel atas untuk transkripsi.",
            )
            return
        if self._transcribe_worker and self._transcribe_worker.isRunning():
            return
        self.lyric_log.clear()
        self.statusBar().showMessage("Transkripsi sedang berjalan...")
        self._transcribe_worker = TranscribeWorker(
            self.groq_client,
            self.config.audio_file,
            model=self.config.transcribe.model,
            language=self.config.transcribe.language,
            ai_correct=self.config.transcribe.ai_correct,
            correct_model=self.config.transcribe.correct_model,
        )
        self._transcribe_worker.progressed.connect(self._append_log)
        self._transcribe_worker.failed.connect(self._on_transcribe_fail)
        self._transcribe_worker.finished_with_result.connect(self._on_transcribe_done)
        self._transcribe_worker.start()

    def _append_log(self, text: str) -> None:
        self.lyric_log.append(text)
        self.statusBar().showMessage(text)

    def _on_transcribe_fail(self, msg: str) -> None:
        self.statusBar().showMessage("Transkripsi gagal")
        QMessageBox.critical(self, "Transkripsi gagal", msg)

    def _on_transcribe_done(self, result: object) -> None:
        if not isinstance(result, TranscriptionResult):
            return
        self.transcription = result
        self.lyric_log.append("\n--- Lirik & timestamp ---")
        for line in result.lines:
            self.lyric_log.append(f"[{line.start:7.2f} → {line.end:7.2f}]  {line.text}")
        self.statusBar().showMessage(f"Transkripsi selesai: {len(result.lines)} baris")
        self._schedule_preview()

    # ----- preview ----------------------------------------------------------
    def _schedule_preview(self) -> None:
        self._refresh_timer.start()

    def _refresh_preview(self) -> None:
        self.preview.update_preview(self.config, self.config.audio_file or None, self.transcription)

    # ----- export -----------------------------------------------------------
    def _export_srt(self) -> None:
        if not self.transcription or not self.transcription.lines:
            QMessageBox.information(self, "Belum ada lirik", "Generate lirik terlebih dahulu.")
            return
        default = self._default_output_basename(".srt")
        path, _ = QFileDialog.getSaveFileName(self, "Simpan SRT", default, "SRT (*.srt)")
        if not path:
            return
        from ..utils.timecode import format_srt
        with open(path, "w", encoding="utf-8") as f:
            for i, line in enumerate(self.transcription.lines, 1):
                f.write(f"{i}\n{format_srt(line.start)} --> {format_srt(line.end)}\n{line.text}\n\n")
        QMessageBox.information(self, "Tersimpan", f"SRT disimpan ke {path}")

    def _export_lrc(self) -> None:
        if not self.transcription or not self.transcription.lines:
            QMessageBox.information(self, "Belum ada lirik", "Generate lirik terlebih dahulu.")
            return
        default = self._default_output_basename(".lrc")
        path, _ = QFileDialog.getSaveFileName(self, "Simpan LRC", default, "LRC (*.lrc)")
        if not path:
            return
        from ..utils.timecode import format_lrc
        with open(path, "w", encoding="utf-8") as f:
            for line in self.transcription.lines:
                f.write(f"{format_lrc(line.start)} {line.text}\n")
        QMessageBox.information(self, "Tersimpan", f"LRC disimpan ke {path}")

    def _default_output_basename(self, ext: str) -> str:
        base = safe_stem(self.config.audio_file) if self.config.audio_file else "lyrics"
        folder = self.config.output_dir or (
            os.path.dirname(self.config.audio_file) if self.config.audio_file else str(Path.home())
        )
        return os.path.join(folder, base + ext)

    # ----- render ----------------------------------------------------------
    def _on_render(self) -> None:
        if self._render_worker and self._render_worker.isRunning():
            return
        if not self.ffmpeg_bar.badge.text().lower().startswith("terinstall"):
            self.ffmpeg_bar.refresh()
            if not self.ffmpeg_bar.badge.text().lower().startswith("terinstall"):
                QMessageBox.warning(
                    self,
                    "FFmpeg belum tersedia",
                    "FFmpeg dibutuhkan untuk merender video. Klik tombol Install FFmpeg dulu.",
                )
                return
        jobs = self._collect_jobs()
        if not jobs:
            QMessageBox.information(self, "Tidak ada job", "Tidak ada audio yang bisa dirender.")
            return
        self.config.save()
        self.progress.setValue(0)
        self.render_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self._render_worker = RenderWorker(jobs, parent=self)
        self._render_worker.progressed.connect(self._on_render_progress)
        self._render_worker.finished_one.connect(self._on_render_one_done)
        self._render_worker.failed.connect(self._on_render_fail)
        self._render_worker.all_done.connect(self._on_render_all_done)
        self._render_worker.start()

    def _collect_jobs(self) -> list[RenderJob]:
        jobs: list[RenderJob] = []
        if self.config.batch.enabled and self.config.batch.music_folder:
            batch_jobs = build_batch(
                self.config.batch.music_folder,
                self.config.batch.background_folder,
                self.config.batch.background_match,
                multi_background=self.config.background.enabled_multi,
            )
            for bj in batch_jobs:
                job_cfg = AppConfig.from_dict(self.config.to_dict())
                if bj.background_files:
                    job_cfg.background.files = bj.background_files
                output_path = self._output_path(bj.audio_path)
                jobs.append(
                    RenderJob(
                        cfg=job_cfg,
                        audio_path=bj.audio_path,
                        output_path=output_path,
                        transcription=None,  # generated per-track inside batch
                    )
                )
        else:
            if not self.config.audio_file or not os.path.exists(self.config.audio_file):
                return []
            jobs.append(
                RenderJob(
                    cfg=AppConfig.from_dict(self.config.to_dict()),
                    audio_path=self.config.audio_file,
                    output_path=self._output_path(self.config.audio_file),
                    transcription=self.transcription,
                )
            )
        return jobs

    def _output_path(self, audio_path: str) -> str:
        folder = self.config.output_dir or os.path.dirname(audio_path)
        return os.path.join(folder, safe_stem(audio_path) + ".mp4")

    def _on_render_progress(self, fraction: float, message: str) -> None:
        self.progress.setValue(int(fraction * 100))
        self.statusBar().showMessage(message)

    def _on_render_one_done(self, path: str) -> None:
        self.statusBar().showMessage(f"Selesai: {path}")

    def _on_render_fail(self, msg: str) -> None:
        QMessageBox.warning(self, "Render gagal", msg)

    def _on_render_all_done(self) -> None:
        self.render_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress.setValue(100)
        self.statusBar().showMessage("Semua render selesai")

    def _cancel_render(self) -> None:
        if self._render_worker:
            self._render_worker.cancel()
            self.statusBar().showMessage("Membatalkan...")

    # ----- close ------------------------------------------------------------
    def closeEvent(self, event) -> None:  # noqa: D401
        try:
            self.config.save()
        except Exception:
            pass
        super().closeEvent(event)
