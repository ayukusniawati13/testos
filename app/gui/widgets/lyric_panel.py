"""Lyric controls: import / edit / export, transcription, display style."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.lyric_engine import (
    LyricEngine,
    LyricLine,
    LyricStyle,
    LyricTrack,
    SUPPORTED_DISPLAY_MODES,
    parse_txt,
)
from app.utils.logger import get_logger

logger = get_logger("lyric_panel")


class _TranscribeWorker(QObject):
    finished = Signal(object, str)  # LyricTrack | None, error message

    def __init__(self, audio_path: str, model: str, language: str, style: LyricStyle) -> None:
        super().__init__()
        self.audio_path = audio_path
        self.model = model
        self.language = language
        self.style = style

    def run(self) -> None:
        try:
            engine = LyricEngine(self.style, model=self.model, language=self.language)
            track = engine.transcribe(self.audio_path)
            self.finished.emit(track, "")
        except Exception as exc:  # pragma: no cover - dependent on heavy deps
            logger.exception("Transcription failed")
            self.finished.emit(None, str(exc))


class LyricPanel(QGroupBox):
    track_changed = Signal(object)  # emits LyricTrack

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("2. Lyrics", parent)
        outer = QVBoxLayout(self)

        # Style settings
        style_form = QFormLayout()
        self.enabled = QCheckBox("Enable lyrics overlay"); self.enabled.setChecked(True)
        self.display_mode = QComboBox(); self.display_mode.addItems(SUPPORTED_DISPLAY_MODES); self.display_mode.setCurrentText("highlight")
        self.font_family = QComboBox(); self.font_family.setEditable(True)
        self.font_family.addItems(["Inter", "Arial", "DejaVu Sans", "Roboto"])
        self.font_size = QSpinBox(); self.font_size.setRange(10, 200); self.font_size.setValue(56)
        self.y_position = QDoubleSpinBox(); self.y_position.setRange(0, 1); self.y_position.setSingleStep(0.05); self.y_position.setValue(0.7)
        self.fade_seconds = QDoubleSpinBox(); self.fade_seconds.setRange(0, 2); self.fade_seconds.setSingleStep(0.05); self.fade_seconds.setValue(0.25)
        self.model = QComboBox(); self.model.addItems(["tiny", "base", "small", "medium", "large-v2"])
        self.model.setCurrentText("base")
        self.language = QComboBox(); self.language.setEditable(True)
        self.language.addItems(["auto", "id", "en", "ja", "ko", "es", "fr", "de"])
        style_form.addRow(self.enabled)
        style_form.addRow("Display mode", self.display_mode)
        style_form.addRow("Font family", self.font_family)
        style_form.addRow("Font size", self.font_size)
        style_form.addRow("Y position", self.y_position)
        style_form.addRow("Fade (s)", self.fade_seconds)
        style_form.addRow("Whisper model", self.model)
        style_form.addRow("Language", self.language)
        outer.addLayout(style_form)

        # IO buttons
        io_row = QHBoxLayout()
        self.btn_transcribe = QPushButton("Auto Transcribe")
        self.btn_import = QPushButton("Import...")
        self.btn_export = QPushButton("Export...")
        io_row.addWidget(self.btn_transcribe)
        io_row.addWidget(self.btn_import)
        io_row.addWidget(self.btn_export)
        io_row.addStretch(1)
        outer.addLayout(io_row)

        # Editor
        outer.addWidget(QLabel("Edit transcript (one line per cue)"))
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText("Lyrics will appear here after auto-transcription, or paste them manually.")
        self.editor.setMinimumHeight(160)
        outer.addWidget(self.editor, 1)

        self.status = QLabel("")
        self.status.setStyleSheet("color: #9aa0b3;")
        outer.addWidget(self.status)

        self._track: LyricTrack = LyricTrack()
        self._audio_path: Optional[str] = None
        self._thread: Optional[QThread] = None
        self._worker: Optional[_TranscribeWorker] = None

        self.btn_transcribe.clicked.connect(self._on_transcribe)
        self.btn_import.clicked.connect(self._on_import)
        self.btn_export.clicked.connect(self._on_export)
        self.editor.textChanged.connect(self._sync_text_to_track)

    # ---------------------------------------------------------- public API

    def set_audio_path(self, path: str) -> None:
        self._audio_path = path or None
        self.btn_transcribe.setEnabled(bool(path))

    def to_style(self) -> LyricStyle:
        return LyricStyle(
            enabled=self.enabled.isChecked(),
            display_mode=self.display_mode.currentText(),
            font_family=self.font_family.currentText(),
            font_size=int(self.font_size.value()),
            y_position=float(self.y_position.value()),
            fade_seconds=float(self.fade_seconds.value()),
        )

    def get_track(self) -> LyricTrack:
        return self._track

    def get_model(self) -> str:
        return self.model.currentText()

    def get_language(self) -> str:
        return self.language.currentText()

    def load_track(self, track: LyricTrack) -> None:
        self._track = track
        self.editor.blockSignals(True)
        self.editor.setPlainText(track.to_plain_text())
        self.editor.blockSignals(False)
        self.track_changed.emit(track)

    def load_dict(self, data: dict) -> None:
        if not data:
            return
        self.enabled.setChecked(bool(data.get("enabled", True)))
        if data.get("display_mode") in SUPPORTED_DISPLAY_MODES:
            self.display_mode.setCurrentText(data["display_mode"])
        if "font_family" in data:
            self.font_family.setEditText(str(data["font_family"]))
        if "font_size" in data:
            self.font_size.setValue(int(data["font_size"]))
        if "y_position" in data:
            self.y_position.setValue(float(data["y_position"]))
        if "fade_seconds" in data:
            self.fade_seconds.setValue(float(data["fade_seconds"]))
        if "model" in data:
            self.model.setCurrentText(str(data["model"]))
        if "language" in data:
            self.language.setEditText(str(data["language"]))

    # ---------------------------------------------------------- handlers

    def _on_transcribe(self) -> None:
        if not self._audio_path:
            QMessageBox.information(self, "Audio missing", "Load an audio file first.")
            return
        if self._thread is not None and self._thread.isRunning():
            return
        self.status.setText("Transcribing... (first run downloads the Whisper model)")
        self.btn_transcribe.setEnabled(False)

        worker = _TranscribeWorker(
            audio_path=self._audio_path,
            model=self.model.currentText(),
            language=self.language.currentText(),
            style=self.to_style(),
        )
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_transcribe_done)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._worker = worker
        self._thread = thread
        thread.start()

    def _on_transcribe_done(self, track, error_message: str) -> None:
        self.btn_transcribe.setEnabled(True)
        self._thread = None
        self._worker = None
        if track is None:
            self.status.setText(f"Transcription failed: {error_message}")
            QMessageBox.critical(self, "Transcription failed", error_message)
            return
        self.status.setText(f"Transcribed {len(track.lines)} line(s).")
        self.load_track(track)

    def _on_import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import lyrics", "",
            "Lyric files (*.srt *.lrc *.txt);;All files (*.*)",
        )
        if not path:
            return
        try:
            engine = LyricEngine(self.to_style())
            track = engine.load(path)
            self.load_track(track)
            self.status.setText(f"Imported {len(track.lines)} line(s) from {Path(path).name}")
        except Exception as exc:
            QMessageBox.critical(self, "Import failed", str(exc))

    def _on_export(self) -> None:
        if self._track.is_empty():
            QMessageBox.information(self, "No lyrics", "There are no lyrics to export.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export lyrics", "",
            "SRT (*.srt);;LRC (*.lrc);;Plain text (*.txt)",
        )
        if not path:
            return
        try:
            engine = LyricEngine(self.to_style())
            engine.set_track(self._track)
            engine.save(path)
            self.status.setText(f"Saved {Path(path).name}")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", str(exc))

    def _sync_text_to_track(self) -> None:
        # When the user edits the textbox we keep the existing timing for
        # lines whose count matches; otherwise we rebuild the track as
        # equally-spaced lines (4 s each) using parse_txt.
        text = self.editor.toPlainText()
        rows = [r.strip() for r in text.splitlines() if r.strip()]
        if self._track.lines and len(self._track.lines) == len(rows):
            new_lines = []
            for line, body in zip(self._track.lines, rows):
                new_lines.append(LyricLine(text=body, start=line.start, end=line.end, words=line.words))
            self._track = LyricTrack(lines=new_lines, language=self._track.language, source=self._track.source)
        else:
            self._track = parse_txt(text)
        self.track_changed.emit(self._track)
