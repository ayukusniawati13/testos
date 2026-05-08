"""Render configuration controls (codec, fps, bitrate, output path)."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.core.render_engine import RenderSettings


class RenderPanel(QGroupBox):
    settings_changed = Signal()

    def __init__(self, default_output_dir: str, parent: QWidget | None = None) -> None:
        super().__init__("7. Render", parent)
        outer = QVBoxLayout(self)

        form = QFormLayout()
        self.fps = QComboBox(); self.fps.addItems(["24", "25", "30", "50", "60"]); self.fps.setCurrentText("30")
        self.codec = QComboBox(); self.codec.addItems(["h264", "h265"]); self.codec.setCurrentText("h264")
        self.preset = QComboBox(); self.preset.addItems(["ultrafast", "fast", "medium", "slow", "veryslow"]); self.preset.setCurrentText("medium")
        self.crf = QSpinBox(); self.crf.setRange(0, 51); self.crf.setValue(20)
        self.bitrate = QLineEdit(); self.bitrate.setPlaceholderText("e.g. 8M (overrides CRF)")
        self.audio_bitrate = QLineEdit("192k")

        self.output_dir = QLineEdit(default_output_dir)
        browse = QPushButton("Browse")
        browse.clicked.connect(self._on_browse_dir)
        out_row = QHBoxLayout()
        out_row.addWidget(self.output_dir, 1)
        out_row.addWidget(browse)
        out_row_w = QWidget(); out_row_w.setLayout(out_row)

        form.addRow("FPS", self.fps)
        form.addRow("Codec", self.codec)
        form.addRow("Preset", self.preset)
        form.addRow("CRF", self.crf)
        form.addRow("Video bitrate", self.bitrate)
        form.addRow("Audio bitrate", self.audio_bitrate)
        form.addRow("Output folder", out_row_w)
        outer.addLayout(form)

        for w in (self.fps, self.codec, self.preset, self.crf, self.bitrate, self.audio_bitrate):
            if hasattr(w, "currentTextChanged"):
                w.currentTextChanged.connect(lambda *_: self.settings_changed.emit())
            elif hasattr(w, "valueChanged"):
                w.valueChanged.connect(lambda *_: self.settings_changed.emit())
            elif hasattr(w, "textChanged"):
                w.textChanged.connect(lambda *_: self.settings_changed.emit())

    def to_settings(self, resolution=(1920, 1080)) -> RenderSettings:
        return RenderSettings(
            resolution=tuple(resolution),
            fps=int(self.fps.currentText()),
            codec=self.codec.currentText(),
            preset=self.preset.currentText(),
            crf=int(self.crf.value()),
            video_bitrate=self.bitrate.text().strip(),
            audio_bitrate=self.audio_bitrate.text().strip() or "192k",
        )

    def get_output_dir(self) -> str:
        return self.output_dir.text().strip()

    def load_dict(self, data: dict) -> None:
        if not data:
            return
        if "fps" in data:
            self.fps.setCurrentText(str(int(data["fps"])))
        if data.get("codec"):
            self.codec.setCurrentText(str(data["codec"]))
        if data.get("preset"):
            self.preset.setCurrentText(str(data["preset"]))
        if "crf" in data:
            self.crf.setValue(int(data["crf"]))
        if "video_bitrate" in data:
            self.bitrate.setText(str(data["video_bitrate"]))
        if "audio_bitrate" in data:
            self.audio_bitrate.setText(str(data["audio_bitrate"]))

    def _on_browse_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select output folder", self.output_dir.text())
        if path:
            self.output_dir.setText(path)
