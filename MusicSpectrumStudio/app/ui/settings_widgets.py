"""Settings tab widgets: audio, background, spectrum, lyrics, effects, logo, batch, render."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

from ..config import (
    AppConfig,
    BackgroundConfig,
    BatchConfig,
    EffectsConfig,
    LogoConfig,
    LyricsConfig,
    RenderConfig,
    SpectrumConfig,
    TranscribeConfig,
)
from ..constants import (
    AUDIO_EXTENSIONS,
    GROQ_TRANSCRIBE_MODELS,
    IMAGE_EXTENSIONS,
    RESOLUTIONS,
    VIDEO_EXTENSIONS,
)
from ..core.fonts import list_fonts
from ..render.lyrics_styles import LYRIC_STYLES
from ..render.spectrum_styles import style_names
from .widgets import ColorButton, Row

logger = logging.getLogger(__name__)


def _form() -> QFormLayout:
    form = QFormLayout()
    form.setLabelAlignment(Qt.AlignRight)
    form.setHorizontalSpacing(12)
    form.setVerticalSpacing(8)
    return form


class AudioPanel(QGroupBox):
    audioChanged = Signal(str)
    generateLyricsRequested = Signal()

    def __init__(self, cfg: AppConfig):
        super().__init__("Sumber Audio")
        self.cfg = cfg
        outer = QVBoxLayout(self)
        outer.setSpacing(8)
        self.audio_edit = QLineEdit(cfg.audio_file)
        self.audio_edit.setPlaceholderText("Pilih file musik (mp3, wav, flac, m4a, ...)")
        browse = QPushButton("Pilih...")
        browse.setProperty("secondary", True)
        browse.clicked.connect(self._browse_audio)
        outer.addWidget(QLabel("File musik"))
        outer.addWidget(Row(self.audio_edit, browse))

        self.output_edit = QLineEdit(cfg.output_dir)
        self.output_edit.setPlaceholderText("Folder output (kosong = di samping file musik)")
        out_browse = QPushButton("Pilih...")
        out_browse.setProperty("secondary", True)
        out_browse.clicked.connect(self._browse_output)
        outer.addWidget(QLabel("Folder output"))
        outer.addWidget(Row(self.output_edit, out_browse))

        gen = QPushButton("Generate Lirik (Groq Whisper)")
        gen.setProperty("success", True)
        gen.clicked.connect(lambda: self.generateLyricsRequested.emit())
        outer.addWidget(gen)

        self.audio_edit.textChanged.connect(self._on_audio_changed)
        self.output_edit.textChanged.connect(self._on_output_changed)

    def _browse_audio(self) -> None:
        filters = " ".join(f"*{ext}" for ext in sorted(AUDIO_EXTENSIONS))
        path, _ = QFileDialog.getOpenFileName(self, "Pilih file musik", "", f"Audio ({filters})")
        if path:
            self.audio_edit.setText(path)

    def _browse_output(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Pilih folder output")
        if path:
            self.output_edit.setText(path)

    def _on_audio_changed(self, text: str) -> None:
        self.cfg.audio_file = text
        self.audioChanged.emit(text)

    def _on_output_changed(self, text: str) -> None:
        self.cfg.output_dir = text


class TranscribePanel(QGroupBox):
    changed = Signal()

    def __init__(self, cfg: TranscribeConfig):
        super().__init__("Transkripsi (Groq Whisper)")
        self.cfg = cfg
        form = _form()
        self.model_combo = QComboBox()
        self.model_combo.addItems(GROQ_TRANSCRIBE_MODELS)
        if cfg.model in GROQ_TRANSCRIBE_MODELS:
            self.model_combo.setCurrentText(cfg.model)
        form.addRow("Model whisper", self.model_combo)

        self.language_edit = QLineEdit(cfg.language)
        self.language_edit.setPlaceholderText("Kode bahasa (kosong = otomatis, mis: id, en)")
        form.addRow("Bahasa", self.language_edit)

        self.ai_correct = QCheckBox("Perbaiki kata dengan AI (chat LLM)")
        self.ai_correct.setChecked(cfg.ai_correct)
        form.addRow("AI Correction", self.ai_correct)

        self.correct_model = QLineEdit(cfg.correct_model)
        self.correct_model.setPlaceholderText("contoh: llama-3.3-70b-versatile")
        form.addRow("Model perbaikan", self.correct_model)

        self.setLayout(form)
        self.model_combo.currentTextChanged.connect(self._sync)
        self.language_edit.textChanged.connect(self._sync)
        self.ai_correct.toggled.connect(self._sync)
        self.correct_model.textChanged.connect(self._sync)

    def _sync(self) -> None:
        self.cfg.model = self.model_combo.currentText()
        self.cfg.language = self.language_edit.text().strip()
        self.cfg.ai_correct = self.ai_correct.isChecked()
        self.cfg.correct_model = self.correct_model.text().strip() or "llama-3.3-70b-versatile"
        self.changed.emit()


class BackgroundPanel(QGroupBox):
    changed = Signal()

    def __init__(self, cfg: BackgroundConfig):
        super().__init__("Background")
        self.cfg = cfg
        outer = QVBoxLayout(self)
        outer.setSpacing(8)

        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(110)
        for p in cfg.files:
            self.list_widget.addItem(p)
        outer.addWidget(self.list_widget)

        btns = QHBoxLayout()
        add = QPushButton("+ Tambah file")
        add.clicked.connect(self._add_files)
        rem = QPushButton("Hapus")
        rem.setProperty("danger", True)
        rem.clicked.connect(self._remove_selected)
        btns.addWidget(add)
        btns.addWidget(rem)
        btns.addStretch()
        outer.addLayout(btns)

        form = _form()
        self.multi_check = QCheckBox("Gunakan banyak background (crossfade smooth)")
        self.multi_check.setChecked(cfg.enabled_multi)
        form.addRow("", self.multi_check)
        self.cycle = QDoubleSpinBox()
        self.cycle.setRange(1.0, 60.0)
        self.cycle.setValue(cfg.cycle_seconds)
        self.cycle.setSuffix(" s")
        form.addRow("Tahan per background", self.cycle)
        self.fade = QDoubleSpinBox()
        self.fade.setRange(0.1, 10.0)
        self.fade.setValue(cfg.crossfade_seconds)
        self.fade.setSuffix(" s")
        form.addRow("Durasi crossfade", self.fade)
        self.fit = QComboBox()
        self.fit.addItems(["cover", "contain"])
        self.fit.setCurrentText(cfg.fit_mode)
        form.addRow("Cara pas", self.fit)
        self.blur = QSpinBox()
        self.blur.setRange(0, 99)
        self.blur.setValue(cfg.blur)
        form.addRow("Blur", self.blur)
        self.darken = QDoubleSpinBox()
        self.darken.setRange(0.0, 1.0)
        self.darken.setSingleStep(0.05)
        self.darken.setValue(cfg.darken)
        form.addRow("Darken (0-1)", self.darken)
        self.color_btn = ColorButton(cfg.color)
        form.addRow("Warna fallback", self.color_btn)

        outer.addLayout(form)

        # signals
        self.multi_check.toggled.connect(self._sync)
        self.cycle.valueChanged.connect(self._sync)
        self.fade.valueChanged.connect(self._sync)
        self.fit.currentTextChanged.connect(self._sync)
        self.blur.valueChanged.connect(self._sync)
        self.darken.valueChanged.connect(self._sync)
        self.color_btn.colorChanged.connect(self._sync)

    def _add_files(self) -> None:
        filters = " ".join(f"*{ext}" for ext in sorted(IMAGE_EXTENSIONS | VIDEO_EXTENSIONS))
        paths, _ = QFileDialog.getOpenFileNames(self, "Pilih background", "", f"Media ({filters})")
        for p in paths:
            QListWidgetItem(p, self.list_widget)
        self._sync()

    def _remove_selected(self) -> None:
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))
        self._sync()

    def _sync(self) -> None:
        self.cfg.files = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        self.cfg.enabled_multi = self.multi_check.isChecked()
        self.cfg.cycle_seconds = self.cycle.value()
        self.cfg.crossfade_seconds = self.fade.value()
        self.cfg.fit_mode = self.fit.currentText()
        self.cfg.blur = self.blur.value()
        self.cfg.darken = self.darken.value()
        self.cfg.color = self.color_btn.color()
        self.changed.emit()


class SpectrumPanel(QGroupBox):
    changed = Signal()

    def __init__(self, cfg: SpectrumConfig):
        super().__init__("Spectrum / Visualizer")
        self.cfg = cfg
        form = _form()

        self.style_combo = QComboBox()
        self.style_combo.addItems(style_names())
        if cfg.style in style_names():
            self.style_combo.setCurrentText(cfg.style)
        form.addRow("Gaya", self.style_combo)

        self.color_a = ColorButton(cfg.color_a)
        self.color_b = ColorButton(cfg.color_b)
        color_row = Row(QLabel("A"), self.color_a, QLabel("B"), self.color_b)
        form.addRow("Warna", color_row)

        self.position = QComboBox()
        self.position.addItems(["bottom", "center", "top"])
        self.position.setCurrentText(cfg.position)
        form.addRow("Posisi", self.position)

        self.height = QDoubleSpinBox()
        self.height.setRange(10.0, 80.0)
        self.height.setSingleStep(1.0)
        self.height.setValue(cfg.height_pct)
        self.height.setSuffix(" %")
        form.addRow("Tinggi area", self.height)

        self.sensitivity = QDoubleSpinBox()
        self.sensitivity.setRange(0.1, 5.0)
        self.sensitivity.setSingleStep(0.1)
        self.sensitivity.setValue(cfg.sensitivity)
        form.addRow("Sensitivity", self.sensitivity)

        self.smoothing = QDoubleSpinBox()
        self.smoothing.setRange(0.0, 0.95)
        self.smoothing.setSingleStep(0.05)
        self.smoothing.setValue(cfg.smoothing)
        form.addRow("Smoothing", self.smoothing)

        self.bar_count = QSpinBox()
        self.bar_count.setRange(16, 256)
        self.bar_count.setValue(cfg.bar_count)
        form.addRow("Jumlah band", self.bar_count)

        self.setLayout(form)

        self.style_combo.currentTextChanged.connect(self._sync)
        self.color_a.colorChanged.connect(self._sync)
        self.color_b.colorChanged.connect(self._sync)
        self.position.currentTextChanged.connect(self._sync)
        self.height.valueChanged.connect(self._sync)
        self.sensitivity.valueChanged.connect(self._sync)
        self.smoothing.valueChanged.connect(self._sync)
        self.bar_count.valueChanged.connect(self._sync)

    def _sync(self) -> None:
        self.cfg.style = self.style_combo.currentText()
        self.cfg.color_a = self.color_a.color()
        self.cfg.color_b = self.color_b.color()
        self.cfg.position = self.position.currentText()
        self.cfg.height_pct = self.height.value()
        self.cfg.sensitivity = self.sensitivity.value()
        self.cfg.smoothing = self.smoothing.value()
        self.cfg.bar_count = self.bar_count.value()
        self.changed.emit()


class LyricsPanel(QGroupBox):
    changed = Signal()

    def __init__(self, cfg: LyricsConfig):
        super().__init__("Lirik")
        self.cfg = cfg
        form = _form()

        self.enabled = QCheckBox("Tampilkan lirik di video")
        self.enabled.setChecked(cfg.enabled)
        form.addRow("", self.enabled)

        self.style_combo = QComboBox()
        self.style_combo.addItems(LYRIC_STYLES)
        if cfg.style in LYRIC_STYLES:
            self.style_combo.setCurrentText(cfg.style)
        form.addRow("Gaya lirik", self.style_combo)

        self.font_combo = QComboBox()
        self.font_combo.addItems([f for f, _ in list_fonts()])
        if cfg.font_family:
            idx = self.font_combo.findText(cfg.font_family)
            if idx >= 0:
                self.font_combo.setCurrentIndex(idx)
        form.addRow("Font", self.font_combo)

        self.font_size = QSpinBox()
        self.font_size.setRange(16, 200)
        self.font_size.setValue(cfg.font_size)
        form.addRow("Ukuran", self.font_size)

        self.primary = ColorButton(cfg.primary_color)
        self.accent = ColorButton(cfg.accent_color)
        self.outline = ColorButton(cfg.outline_color)
        form.addRow("Warna utama", self.primary)
        form.addRow("Warna aksen", self.accent)
        form.addRow("Outline", self.outline)

        self.outline_w = QSpinBox()
        self.outline_w.setRange(0, 20)
        self.outline_w.setValue(cfg.outline_width)
        form.addRow("Tebal outline", self.outline_w)

        self.fade = QSpinBox()
        self.fade.setRange(0, 5000)
        self.fade.setSingleStep(50)
        self.fade.setSuffix(" ms")
        self.fade.setValue(cfg.fade_ms)
        form.addRow("Fade in/out", self.fade)

        self.position = QComboBox()
        self.position.addItems(["bottom", "center", "top"])
        self.position.setCurrentText(cfg.position)
        form.addRow("Posisi", self.position)

        self.max_lines = QSpinBox()
        self.max_lines.setRange(1, 4)
        self.max_lines.setValue(cfg.max_lines)
        form.addRow("Maks baris simultan", self.max_lines)

        self.gap_s = QDoubleSpinBox()
        self.gap_s.setRange(0.0, 10.0)
        self.gap_s.setSingleStep(0.1)
        self.gap_s.setValue(cfg.line_gap_seconds)
        self.gap_s.setSuffix(" s")
        form.addRow("Jeda antar baris (hide)", self.gap_s)

        self.margin = QDoubleSpinBox()
        self.margin.setRange(0.0, 30.0)
        self.margin.setSingleStep(0.5)
        self.margin.setValue(cfg.margin_pct)
        self.margin.setSuffix(" %")
        form.addRow("Margin (%)", self.margin)

        self.setLayout(form)

        for w in (
            self.enabled, self.style_combo, self.font_combo, self.font_size,
            self.outline_w, self.fade, self.position, self.max_lines, self.gap_s, self.margin,
            self.primary, self.accent, self.outline,
        ):
            sig = getattr(w, "valueChanged", None) or getattr(w, "currentTextChanged", None) or \
                getattr(w, "toggled", None) or getattr(w, "colorChanged", None)
            if sig is not None:
                sig.connect(self._sync)

    def _sync(self) -> None:
        self.cfg.enabled = self.enabled.isChecked()
        self.cfg.style = self.style_combo.currentText()
        self.cfg.font_family = self.font_combo.currentText()
        self.cfg.font_size = self.font_size.value()
        self.cfg.primary_color = self.primary.color()
        self.cfg.accent_color = self.accent.color()
        self.cfg.outline_color = self.outline.color()
        self.cfg.outline_width = self.outline_w.value()
        self.cfg.fade_ms = self.fade.value()
        self.cfg.position = self.position.currentText()
        self.cfg.max_lines = self.max_lines.value()
        self.cfg.line_gap_seconds = self.gap_s.value()
        self.cfg.margin_pct = self.margin.value()
        self.changed.emit()


class EffectsPanel(QGroupBox):
    changed = Signal()

    def __init__(self, cfg: EffectsConfig):
        super().__init__("Efek Video")
        self.cfg = cfg
        form = _form()
        self.sparkle = QCheckBox("Kelap-kelip (sparkle)")
        self.sparkle.setChecked(cfg.sparkle)
        form.addRow("", self.sparkle)
        self.sparkle_intensity = self._slider(0, 100, int(cfg.sparkle_intensity * 100))
        form.addRow("Intensitas sparkle", self.sparkle_intensity)

        self.glow = QCheckBox("Glow / Bloom")
        self.glow.setChecked(cfg.glow)
        form.addRow("", self.glow)
        self.glow_strength = self._slider(0, 100, int(cfg.glow_strength * 100))
        form.addRow("Kekuatan glow", self.glow_strength)

        self.vignette = QCheckBox("Vignette")
        self.vignette.setChecked(cfg.vignette)
        form.addRow("", self.vignette)
        self.vignette_strength = self._slider(0, 100, int(cfg.vignette_strength * 100))
        form.addRow("Kekuatan vignette", self.vignette_strength)

        self.grain = QCheckBox("Grain (noise)")
        self.grain.setChecked(cfg.grain)
        form.addRow("", self.grain)

        self.beat_flash = QCheckBox("Beat flash (kilat saat beat)")
        self.beat_flash.setChecked(cfg.beat_flash)
        form.addRow("", self.beat_flash)

        self.light_leaks = QCheckBox("Light leaks (gradient bergerak)")
        self.light_leaks.setChecked(cfg.light_leaks)
        form.addRow("", self.light_leaks)

        self.setLayout(form)
        for w in (
            self.sparkle, self.glow, self.vignette, self.grain, self.beat_flash,
            self.light_leaks, self.sparkle_intensity, self.glow_strength, self.vignette_strength,
        ):
            sig = getattr(w, "valueChanged", None) or getattr(w, "toggled", None)
            if sig:
                sig.connect(self._sync)

    @staticmethod
    def _slider(lo: int, hi: int, value: int) -> QSlider:
        s = QSlider(Qt.Horizontal)
        s.setRange(lo, hi)
        s.setValue(value)
        return s

    def _sync(self) -> None:
        self.cfg.sparkle = self.sparkle.isChecked()
        self.cfg.sparkle_intensity = self.sparkle_intensity.value() / 100.0
        self.cfg.glow = self.glow.isChecked()
        self.cfg.glow_strength = self.glow_strength.value() / 100.0
        self.cfg.vignette = self.vignette.isChecked()
        self.cfg.vignette_strength = self.vignette_strength.value() / 100.0
        self.cfg.grain = self.grain.isChecked()
        self.cfg.beat_flash = self.beat_flash.isChecked()
        self.cfg.light_leaks = self.light_leaks.isChecked()
        self.changed.emit()


class LogoPanel(QGroupBox):
    changed = Signal()

    def __init__(self, cfg: LogoConfig):
        super().__init__("Logo")
        self.cfg = cfg
        outer = QVBoxLayout(self)
        self.enabled = QCheckBox("Tampilkan logo")
        self.enabled.setChecked(cfg.enabled)
        outer.addWidget(self.enabled)

        self.path = QLineEdit(cfg.path)
        self.path.setPlaceholderText("Pilih file gambar logo (PNG transparan disarankan)")
        browse = QPushButton("Pilih...")
        browse.setProperty("secondary", True)
        browse.clicked.connect(self._browse)
        outer.addWidget(Row(self.path, browse))

        form = _form()
        self.circular = QCheckBox("Buat logo bulat")
        self.circular.setChecked(cfg.circular)
        form.addRow("", self.circular)
        self.size = QDoubleSpinBox()
        self.size.setRange(2.0, 50.0)
        self.size.setValue(cfg.size_pct)
        self.size.setSuffix(" %")
        form.addRow("Ukuran (% lebar)", self.size)
        self.x = QDoubleSpinBox()
        self.x.setRange(0.0, 80.0)
        self.x.setValue(cfg.x_pct)
        self.x.setSuffix(" %")
        form.addRow("Margin X", self.x)
        self.y = QDoubleSpinBox()
        self.y.setRange(0.0, 80.0)
        self.y.setValue(cfg.y_pct)
        self.y.setSuffix(" %")
        form.addRow("Margin Y", self.y)
        self.anchor = QComboBox()
        self.anchor.addItems(["top_left", "top_right", "bottom_left", "bottom_right", "center"])
        self.anchor.setCurrentText(cfg.anchor)
        form.addRow("Anchor", self.anchor)
        self.opacity = QDoubleSpinBox()
        self.opacity.setRange(0.0, 1.0)
        self.opacity.setSingleStep(0.05)
        self.opacity.setValue(cfg.opacity)
        form.addRow("Opacity", self.opacity)
        outer.addLayout(form)

        for w in (
            self.enabled, self.path, self.circular, self.size, self.x, self.y,
            self.anchor, self.opacity,
        ):
            sig = getattr(w, "valueChanged", None) or getattr(w, "textChanged", None) or \
                getattr(w, "currentTextChanged", None) or getattr(w, "toggled", None)
            if sig:
                sig.connect(self._sync)

    def _browse(self) -> None:
        filters = " ".join(f"*{ext}" for ext in sorted(IMAGE_EXTENSIONS))
        path, _ = QFileDialog.getOpenFileName(self, "Pilih logo", "", f"Gambar ({filters})")
        if path:
            self.path.setText(path)

    def _sync(self) -> None:
        self.cfg.enabled = self.enabled.isChecked()
        self.cfg.path = self.path.text()
        self.cfg.circular = self.circular.isChecked()
        self.cfg.size_pct = self.size.value()
        self.cfg.x_pct = self.x.value()
        self.cfg.y_pct = self.y.value()
        self.cfg.anchor = self.anchor.currentText()
        self.cfg.opacity = self.opacity.value()
        self.changed.emit()


class BatchPanel(QGroupBox):
    changed = Signal()

    def __init__(self, cfg: BatchConfig):
        super().__init__("Batch Render")
        self.cfg = cfg
        outer = QVBoxLayout(self)
        self.enabled = QCheckBox("Aktifkan mode batch (render banyak musik sekaligus)")
        self.enabled.setChecked(cfg.enabled)
        outer.addWidget(self.enabled)

        self.music_edit = QLineEdit(cfg.music_folder)
        self.music_edit.setPlaceholderText("Folder berisi banyak file musik")
        music_btn = QPushButton("Pilih...")
        music_btn.setProperty("secondary", True)
        music_btn.clicked.connect(lambda: self._browse(self.music_edit))
        outer.addWidget(QLabel("Folder musik"))
        outer.addWidget(Row(self.music_edit, music_btn))

        self.bg_edit = QLineEdit(cfg.background_folder)
        self.bg_edit.setPlaceholderText("Folder berisi gambar/video background")
        bg_btn = QPushButton("Pilih...")
        bg_btn.setProperty("secondary", True)
        bg_btn.clicked.connect(lambda: self._browse(self.bg_edit))
        outer.addWidget(QLabel("Folder background"))
        outer.addWidget(Row(self.bg_edit, bg_btn))

        self.match = QComboBox()
        self.match.addItems(["order", "name", "random"])
        self.match.setCurrentText(cfg.background_match)
        outer.addWidget(QLabel("Cara mencocokkan background"))
        outer.addWidget(self.match)

        outer.addStretch()

        self.enabled.toggled.connect(self._sync)
        self.music_edit.textChanged.connect(self._sync)
        self.bg_edit.textChanged.connect(self._sync)
        self.match.currentTextChanged.connect(self._sync)

    def _browse(self, target: QLineEdit) -> None:
        path = QFileDialog.getExistingDirectory(self, "Pilih folder")
        if path:
            target.setText(path)

    def _sync(self) -> None:
        self.cfg.enabled = self.enabled.isChecked()
        self.cfg.music_folder = self.music_edit.text()
        self.cfg.background_folder = self.bg_edit.text()
        self.cfg.background_match = self.match.currentText()
        self.changed.emit()


class RenderPanel(QGroupBox):
    changed = Signal()

    def __init__(self, cfg: RenderConfig):
        super().__init__("Render")
        self.cfg = cfg
        form = _form()
        self.resolution_combo = QComboBox()
        for w, h, label in RESOLUTIONS:
            self.resolution_combo.addItem(label, (w, h))
        # pre-select matching item
        for i in range(self.resolution_combo.count()):
            w, h = self.resolution_combo.itemData(i)
            if (w, h) == (cfg.width, cfg.height):
                self.resolution_combo.setCurrentIndex(i)
                break
        form.addRow("Resolusi", self.resolution_combo)

        self.fps = QSpinBox()
        self.fps.setRange(15, 60)
        self.fps.setValue(cfg.fps)
        form.addRow("FPS", self.fps)

        self.crf = QSpinBox()
        self.crf.setRange(14, 32)
        self.crf.setValue(cfg.crf)
        form.addRow("CRF (semakin kecil semakin tajam)", self.crf)

        self.preset = QComboBox()
        for p in ("ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower"):
            self.preset.addItem(p)
        self.preset.setCurrentText(cfg.preset)
        form.addRow("Preset H.264", self.preset)

        self.audio_bitrate = QLineEdit(cfg.audio_bitrate)
        form.addRow("Bitrate audio", self.audio_bitrate)

        self.setLayout(form)

        self.resolution_combo.currentIndexChanged.connect(self._sync)
        self.fps.valueChanged.connect(self._sync)
        self.crf.valueChanged.connect(self._sync)
        self.preset.currentTextChanged.connect(self._sync)
        self.audio_bitrate.textChanged.connect(self._sync)

    def _sync(self) -> None:
        data = self.resolution_combo.currentData()
        if data:
            self.cfg.width, self.cfg.height = data
        self.cfg.fps = self.fps.value()
        self.cfg.crf = self.crf.value()
        self.cfg.preset = self.preset.currentText()
        self.cfg.audio_bitrate = self.audio_bitrate.text() or "192k"
        self.changed.emit()
