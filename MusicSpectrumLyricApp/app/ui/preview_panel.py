"""Preview panel for visualizing spectrum and lyrics before rendering."""

import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap

from app.core.spectrum_engine import SpectrumEngine, SpectrumConfig
from app.core.lyric_renderer import LyricRenderer, LyricConfig
from app.core.lrc_parser import LyricLine
from PIL import Image


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._time = 0.0
        self._playing = False
        self._duration = 60.0
        self._lyrics: list[LyricLine] = []
        self._spectrum_engine: SpectrumEngine | None = None
        self._lyric_renderer: LyricRenderer | None = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._width = 640
        self._height = 360

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(320, 180)
        self.image_label.setStyleSheet(
            "background-color: #0d0d1a; border: 1px solid #2d2d4a; border-radius: 4px;"
        )
        layout.addWidget(self.image_label)

        controls = QHBoxLayout()
        self.play_btn = QPushButton("Play Preview")
        self.play_btn.clicked.connect(self._toggle_play)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._stop)
        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setStyleSheet("color: #8888aa;")
        controls.addWidget(self.play_btn)
        controls.addWidget(self.stop_btn)
        controls.addStretch()
        controls.addWidget(self.time_label)
        layout.addLayout(controls)

    def set_config(self, spectrum_config: SpectrumConfig,
                   lyric_config: LyricConfig) -> None:
        self._spectrum_engine = SpectrumEngine(spectrum_config)
        self._lyric_renderer = LyricRenderer(lyric_config)

    def set_lyrics(self, lyrics: list[LyricLine]) -> None:
        self._lyrics = lyrics

    def set_duration(self, dur: float) -> None:
        self._duration = dur

    def _toggle_play(self) -> None:
        if self._playing:
            self._playing = False
            self._timer.stop()
            self.play_btn.setText("Play Preview")
        else:
            self._playing = True
            self._timer.start(33)
            self.play_btn.setText("Pause")

    def _stop(self) -> None:
        self._playing = False
        self._timer.stop()
        self._time = 0.0
        self.play_btn.setText("Play Preview")
        self._render_frame()

    def _tick(self) -> None:
        self._time += 0.033
        if self._time > self._duration:
            self._time = 0.0
        self._render_frame()

    def _render_frame(self) -> None:
        w, h = self._width, self._height
        frame = Image.new("RGBA", (w, h), (13, 13, 26, 255))

        if self._spectrum_engine:
            n_bands = 64
            rng = np.random.RandomState(int(self._time * 10))
            bands = np.abs(np.sin(np.linspace(0, 6, n_bands) + self._time * 3))
            bands *= 0.3 + 0.7 * rng.random(n_bands)
            bands = np.clip(bands, 0, 1)
            beat = float(0.3 + 0.3 * abs(np.sin(self._time * 2)))
            spec_layer = self._spectrum_engine.render(w, h, bands, beat)
            frame = Image.alpha_composite(frame, spec_layer)

        if self._lyric_renderer and self._lyrics:
            lyric_layer = self._lyric_renderer.render(w, h, self._lyrics, self._time)
            frame = Image.alpha_composite(frame, lyric_layer)

        rgb = frame.convert("RGB")
        data = rgb.tobytes()
        qimg = QImage(data, w, h, w * 3, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

        mins = int(self._time) // 60
        secs = int(self._time) % 60
        total_m = int(self._duration) // 60
        total_s = int(self._duration) % 60
        self.time_label.setText(f"{mins}:{secs:02d} / {total_m}:{total_s:02d}")
