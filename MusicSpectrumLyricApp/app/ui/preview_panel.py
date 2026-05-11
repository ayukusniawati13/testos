"""Preview panel for visualizing spectrum and lyrics before rendering."""

import os
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QSlider,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap

from app.core.spectrum_engine import SpectrumEngine, SpectrumConfig
from app.core.lyric_renderer import LyricRenderer, LyricConfig
from app.core.lrc_parser import LyricLine
from app.core.audio_analyzer import AudioAnalyzer
from PIL import Image


class PreviewPanel(QWidget):
    time_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._time = 0.0
        self._playing = False
        self._duration = 60.0
        self._lyrics: list[LyricLine] = []
        self._spectrum_engine: SpectrumEngine | None = None
        self._lyric_renderer: LyricRenderer | None = None
        self._audio_analyzer: AudioAnalyzer | None = None
        self._background: Image.Image | None = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._width = 640
        self._height = 360
        self._seeking = False

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(480, 270)
        self.image_label.setStyleSheet(
            "background-color: #0d0d1a; border: 1px solid #2d2d4a; border-radius: 6px;"
        )
        layout.addWidget(self.image_label, 1)

        self.timeline = QSlider(Qt.Orientation.Horizontal)
        self.timeline.setRange(0, 10000)
        self.timeline.setValue(0)
        self.timeline.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px; background: #1a1a2e;
                border: 1px solid #2d2d4a; border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00d4ff; width: 14px; height: 14px;
                margin: -4px 0; border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4ff, stop:1 #e040fb);
                border-radius: 4px;
            }
        """)
        self.timeline.sliderPressed.connect(self._on_seek_start)
        self.timeline.sliderReleased.connect(self._on_seek_end)
        self.timeline.valueChanged.connect(self._on_timeline_changed)
        layout.addWidget(self.timeline)

        controls = QHBoxLayout()
        controls.setSpacing(8)

        self.play_btn = QPushButton("Play")
        self.play_btn.setFixedWidth(80)
        self.play_btn.clicked.connect(self._toggle_play)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFixedWidth(60)
        self.stop_btn.clicked.connect(self._stop)

        self.time_label = QLabel("0:00.0 / 0:00.0")
        self.time_label.setStyleSheet("color: #8888aa; font-family: monospace; font-size: 13px;")

        self.lyric_label = QLabel("")
        self.lyric_label.setStyleSheet(
            "color: #00d4ff; font-size: 12px; font-style: italic;"
        )
        self.lyric_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        controls.addWidget(self.play_btn)
        controls.addWidget(self.stop_btn)
        controls.addWidget(self.time_label)
        controls.addStretch()
        controls.addWidget(self.lyric_label)
        layout.addLayout(controls)

        self.info_label = QLabel("Load music and lyrics, then click Update Preview")
        self.info_label.setStyleSheet("color: #555570; font-size: 11px;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)

    def set_config(self, spectrum_config: SpectrumConfig,
                   lyric_config: LyricConfig) -> None:
        self._spectrum_engine = SpectrumEngine(spectrum_config)
        self._lyric_renderer = LyricRenderer(lyric_config)

    def set_lyrics(self, lyrics: list[LyricLine]) -> None:
        self._lyrics = lyrics
        if lyrics:
            self.info_label.setText(f"{len(lyrics)} lyric lines loaded")

    def set_duration(self, dur: float) -> None:
        self._duration = max(1.0, dur)

    def load_audio(self, filepath: str) -> None:
        if not filepath or not os.path.isfile(filepath):
            self._audio_analyzer = None
            return
        try:
            self._audio_analyzer = AudioAnalyzer(filepath)
            self._audio_analyzer.load()
            self._audio_analyzer.analyze()
            self._duration = self._audio_analyzer.duration
            self.info_label.setText(
                f"Audio loaded: {self._duration:.1f}s | "
                f"Click Play to preview"
            )
        except Exception as e:
            self._audio_analyzer = None
            self.info_label.setText(f"Audio load error: {e}")

    def load_background(self, filepath: str) -> None:
        if not filepath or not os.path.isfile(filepath):
            self._background = None
            return
        try:
            ext = filepath.lower().rsplit(".", 1)[-1]
            if ext in ("jpg", "jpeg", "png", "webp", "bmp"):
                img = Image.open(filepath).convert("RGBA")
                img = img.resize((self._width, self._height), Image.LANCZOS)
                self._background = img
                self.info_label.setText("Background loaded")
        except Exception:
            self._background = None

    def _on_seek_start(self) -> None:
        self._seeking = True

    def _on_seek_end(self) -> None:
        self._seeking = False
        val = self.timeline.value()
        self._time = (val / 10000.0) * self._duration
        self._render_frame()

    def _on_timeline_changed(self, val: int) -> None:
        if self._seeking:
            self._time = (val / 10000.0) * self._duration
            self._update_time_display()

    def _toggle_play(self) -> None:
        if self._playing:
            self._playing = False
            self._timer.stop()
            self.play_btn.setText("Play")
        else:
            self._playing = True
            self._timer.start(33)
            self.play_btn.setText("Pause")

    def _stop(self) -> None:
        self._playing = False
        self._timer.stop()
        self._time = 0.0
        self.play_btn.setText("Play")
        self.timeline.setValue(0)
        self._render_frame()

    def _tick(self) -> None:
        self._time += 0.033
        if self._time >= self._duration:
            self._time = 0.0
        if not self._seeking:
            pos = int((self._time / self._duration) * 10000)
            self.timeline.blockSignals(True)
            self.timeline.setValue(pos)
            self.timeline.blockSignals(False)
        self._render_frame()

    def _render_frame(self) -> None:
        w, h = self._width, self._height

        if self._background:
            frame = self._background.copy()
        else:
            frame = Image.new("RGBA", (w, h), (13, 13, 26, 255))

        if self._spectrum_engine:
            if self._audio_analyzer:
                bands = self._audio_analyzer.get_spectrum_at_time(self._time, n_bands=64)
                beat = self._audio_analyzer.get_beat_strength_at_time(self._time)
            else:
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
        self._update_time_display()
        self._update_lyric_display()

    def _update_time_display(self) -> None:
        t = self._time
        d = self._duration
        self.time_label.setText(
            f"{int(t)//60}:{int(t)%60:02d}.{int((t%1)*10)} / "
            f"{int(d)//60}:{int(d)%60:02d}.{int((d%1)*10)}"
        )

    def _update_lyric_display(self) -> None:
        if not self._lyrics:
            self.lyric_label.setText("")
            return
        if self._lyric_renderer:
            active, _, _ = self._lyric_renderer.get_active_lyric(
                self._lyrics, self._time)
            if active:
                text = active.text
                if len(text) > 50:
                    text = text[:47] + "..."
                self.lyric_label.setText(text)
            else:
                self.lyric_label.setText("(instrumental)")
        else:
            self.lyric_label.setText("")
