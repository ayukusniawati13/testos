"""Audio input widget: drag-and-drop, browse, metadata display."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.audio_analyzer import AudioMetadata, probe_audio_metadata
from app.utils import file_utils, validators
from app.utils.logger import get_logger

logger = get_logger("audio_panel")


class AudioPanel(QGroupBox):
    audio_changed = Signal(str)  # emits the absolute audio path

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("1. Audio", parent)
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)

        self.path_field = QLineEdit()
        self.path_field.setReadOnly(True)
        self.path_field.setPlaceholderText("Drop an audio file here or click Browse")
        browse = QPushButton("Browse")
        browse.clicked.connect(self._on_browse)
        clear = QPushButton("Clear")
        clear.clicked.connect(self._clear)

        path_row = QHBoxLayout()
        path_row.addWidget(self.path_field, 1)
        path_row.addWidget(browse)
        path_row.addWidget(clear)
        layout.addLayout(path_row)

        meta_box = QGroupBox("Metadata")
        meta_form = QFormLayout(meta_box)
        self.lbl_title = QLabel("—")
        self.lbl_artist = QLabel("—")
        self.lbl_duration = QLabel("—")
        self.lbl_sr = QLabel("—")
        self.lbl_bitrate = QLabel("—")
        meta_form.addRow("Title", self.lbl_title)
        meta_form.addRow("Artist", self.lbl_artist)
        meta_form.addRow("Duration", self.lbl_duration)
        meta_form.addRow("Sample rate", self.lbl_sr)
        meta_form.addRow("Bitrate", self.lbl_bitrate)
        layout.addWidget(meta_box)

    # --------------------------------------------------------------- public

    def set_audio(self, path: str | Path) -> Optional[AudioMetadata]:
        try:
            p = validators.ensure_audio(path)
        except validators.ValidationError as exc:
            logger.warning("Audio validation failed: %s", exc)
            return None

        self.path_field.setText(str(p))
        try:
            meta = probe_audio_metadata(p)
        except Exception as exc:  # pragma: no cover - tolerant
            logger.warning("Could not probe %s: %s", p, exc)
            meta = AudioMetadata(path=p, duration=0.0, sample_rate=0, channels=0)
        self._populate_metadata(meta)
        self.audio_changed.emit(str(p))
        return meta

    def get_path(self) -> Optional[str]:
        return self.path_field.text() or None

    # --------------------------------------------------------------- internals

    def _populate_metadata(self, meta: AudioMetadata) -> None:
        self.lbl_title.setText(meta.title or meta.path.stem)
        self.lbl_artist.setText(meta.artist or "—")
        if meta.duration > 0:
            mins = int(meta.duration // 60)
            secs = meta.duration - mins * 60
            self.lbl_duration.setText(f"{mins:02d}:{secs:05.2f}")
        else:
            self.lbl_duration.setText("—")
        self.lbl_sr.setText(f"{meta.sample_rate} Hz" if meta.sample_rate else "—")
        if meta.bitrate:
            self.lbl_bitrate.setText(f"{int(meta.bitrate / 1000)} kbps")
        else:
            self.lbl_bitrate.setText("—")

    def _on_browse(self) -> None:
        filt = "Audio files (*.mp3 *.wav *.flac *.m4a *.ogg *.aac);;All files (*.*)"
        path, _ = QFileDialog.getOpenFileName(self, "Select audio file", "", filt)
        if path:
            self.set_audio(path)

    def _clear(self) -> None:
        self.path_field.clear()
        for label in (self.lbl_title, self.lbl_artist, self.lbl_duration, self.lbl_sr, self.lbl_bitrate):
            label.setText("—")
        self.audio_changed.emit("")

    # --------------------------------------------------------------- DnD

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802 - Qt API
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if Path(url.toLocalFile()).suffix.lower() in file_utils.AUDIO_EXTS:
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802 - Qt API
        for url in event.mimeData().urls():
            local = url.toLocalFile()
            if local and Path(local).suffix.lower() in file_utils.AUDIO_EXTS:
                self.set_audio(local)
                event.acceptProposedAction()
                return
        event.ignore()
