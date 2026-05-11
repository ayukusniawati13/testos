"""Settings panel for video, spectrum, lyric, and logo configuration."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QLineEdit,
    QPushButton, QSlider, QColorDialog, QFileDialog, QScrollArea,
    QFormLayout, QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from app.core.spectrum_engine import SpectrumStyle, SpectrumConfig
from app.core.lyric_renderer import LyricConfig
from app.core.video_renderer import VideoConfig, LogoConfig
from app.styles.spectrum_styles import SPECTRUM_PRESETS


class ColorButton(QPushButton):
    color_changed = Signal(tuple)

    def __init__(self, color: tuple = (255, 255, 255), parent=None):
        super().__init__(parent)
        self._color = color
        self._update_style()
        self.clicked.connect(self._pick_color)
        self.setFixedSize(40, 28)

    def _update_style(self) -> None:
        r, g, b = self._color
        self.setStyleSheet(
            f"background-color: rgb({r},{g},{b}); border: 1px solid #555; "
            f"border-radius: 4px; min-height: 0; padding: 0;"
        )

    def _pick_color(self) -> None:
        c = QColorDialog.getColor(QColor(*self._color), self, "Pick Color")
        if c.isValid():
            self._color = (c.red(), c.green(), c.blue())
            self._update_style()
            self.color_changed.emit(self._color)

    @property
    def color(self) -> tuple:
        return self._color

    @color.setter
    def color(self, val: tuple) -> None:
        self._color = val
        self._update_style()


class SettingsPanel(QWidget):
    settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)

        layout.addWidget(self._create_video_group())
        layout.addWidget(self._create_spectrum_group())
        layout.addWidget(self._create_lyric_group())
        layout.addWidget(self._create_logo_group())
        layout.addStretch()

        scroll.setWidget(content)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

    def _create_video_group(self) -> QGroupBox:
        group = QGroupBox("Video Settings")
        form = QFormLayout()
        form.setSpacing(8)

        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1920x1080 (Full HD)",
            "1080x1920 (Vertical/TikTok)",
            "1280x720 (HD)",
        ])
        form.addRow("Resolution:", self.resolution_combo)

        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["30", "60"])
        form.addRow("FPS:", self.fps_combo)

        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["4M", "6M", "8M", "10M", "12M", "15M"])
        self.bitrate_combo.setCurrentIndex(2)
        form.addRow("Bitrate:", self.bitrate_combo)

        group.setLayout(form)
        return group

    def _create_spectrum_group(self) -> QGroupBox:
        group = QGroupBox("Spectrum / Visualizer")
        form = QFormLayout()
        form.setSpacing(8)

        self.spectrum_style_combo = QComboBox()
        self.spectrum_style_combo.addItems(SpectrumStyle.ALL)
        self.spectrum_style_combo.currentTextChanged.connect(self._on_style_changed)
        form.addRow("Style:", self.spectrum_style_combo)

        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(10, 300)
        self.sensitivity_slider.setValue(120)
        form.addRow("Sensitivity:", self.sensitivity_slider)

        self.spec_height_slider = QSlider(Qt.Orientation.Horizontal)
        self.spec_height_slider.setRange(10, 80)
        self.spec_height_slider.setValue(30)
        form.addRow("Height:", self.spec_height_slider)

        self.spec_position = QComboBox()
        self.spec_position.addItems(["bottom", "center", "top"])
        form.addRow("Position:", self.spec_position)

        self.spec_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.spec_opacity_slider.setRange(10, 100)
        self.spec_opacity_slider.setValue(85)
        form.addRow("Opacity:", self.spec_opacity_slider)

        self.spec_glow_slider = QSlider(Qt.Orientation.Horizontal)
        self.spec_glow_slider.setRange(0, 100)
        self.spec_glow_slider.setValue(50)
        form.addRow("Glow:", self.spec_glow_slider)

        self.spec_blur_slider = QSlider(Qt.Orientation.Horizontal)
        self.spec_blur_slider.setRange(0, 100)
        self.spec_blur_slider.setValue(20)
        form.addRow("Blur:", self.spec_blur_slider)

        self.spec_color1 = ColorButton((0, 200, 255))
        form.addRow("Color 1:", self.spec_color1)

        self.spec_color2 = ColorButton((255, 0, 200))
        form.addRow("Color 2:", self.spec_color2)

        self.spec_gradient_check = QCheckBox("Use Gradient")
        self.spec_gradient_check.setChecked(True)
        form.addRow("", self.spec_gradient_check)

        self.spec_smoothing_slider = QSlider(Qt.Orientation.Horizontal)
        self.spec_smoothing_slider.setRange(0, 90)
        self.spec_smoothing_slider.setValue(30)
        form.addRow("Smoothing:", self.spec_smoothing_slider)

        group.setLayout(form)
        return group

    def _create_lyric_group(self) -> QGroupBox:
        group = QGroupBox("Lyric Settings")
        form = QFormLayout()
        form.setSpacing(8)

        self.font_family = QComboBox()
        self.font_family.setEditable(True)
        self.font_family.addItems([
            "Arial", "Segoe UI", "Helvetica", "Verdana", "Tahoma",
            "Georgia", "Times New Roman", "Impact",
            "DejaVu Sans", "Liberation Sans",
        ])
        form.addRow("Font:", self.font_family)

        self.font_size = QSpinBox()
        self.font_size.setRange(16, 120)
        self.font_size.setValue(48)
        form.addRow("Size:", self.font_size)

        self.lyric_color = ColorButton((255, 255, 255))
        form.addRow("Color:", self.lyric_color)

        self.shadow_color = ColorButton((0, 0, 0))
        form.addRow("Shadow Color:", self.shadow_color)

        self.shadow_offset = QSpinBox()
        self.shadow_offset.setRange(0, 20)
        self.shadow_offset.setValue(3)
        form.addRow("Shadow Offset:", self.shadow_offset)

        self.stroke_color = ColorButton((0, 0, 0))
        form.addRow("Stroke Color:", self.stroke_color)

        self.stroke_width = QSpinBox()
        self.stroke_width.setRange(0, 10)
        self.stroke_width.setValue(2)
        form.addRow("Stroke Width:", self.stroke_width)

        self.lyric_glow_slider = QSlider(Qt.Orientation.Horizontal)
        self.lyric_glow_slider.setRange(0, 100)
        self.lyric_glow_slider.setValue(50)
        form.addRow("Glow:", self.lyric_glow_slider)

        self.lyric_glow_color = ColorButton((100, 150, 255))
        form.addRow("Glow Color:", self.lyric_glow_color)

        self.lyric_position = QComboBox()
        self.lyric_position.addItems(["bottom", "center", "top"])
        form.addRow("Position:", self.lyric_position)

        self.lyric_alignment = QComboBox()
        self.lyric_alignment.addItems(["center", "left", "right"])
        form.addRow("Alignment:", self.lyric_alignment)

        self.show_next_line = QCheckBox("Show Next Line")
        self.show_next_line.setChecked(True)
        form.addRow("", self.show_next_line)

        self.fade_duration = QDoubleSpinBox()
        self.fade_duration.setRange(0.1, 2.0)
        self.fade_duration.setValue(0.5)
        self.fade_duration.setSingleStep(0.1)
        form.addRow("Fade Duration:", self.fade_duration)

        group.setLayout(form)
        return group

    def _create_logo_group(self) -> QGroupBox:
        group = QGroupBox("Logo")
        form = QFormLayout()
        form.setSpacing(8)

        self.logo_enabled = QCheckBox("Enable Logo")
        form.addRow("", self.logo_enabled)

        row = QHBoxLayout()
        self.logo_path = QLineEdit()
        self.logo_path.setPlaceholderText("Select logo file...")
        self.logo_path.setReadOnly(True)
        btn = QPushButton("Browse")
        btn.clicked.connect(self._browse_logo)
        row.addWidget(self.logo_path)
        row.addWidget(btn)
        form.addRow("File:", row)

        self.logo_position = QComboBox()
        self.logo_position.addItems([
            "top-left", "top-right", "bottom-left", "bottom-right", "center"
        ])
        self.logo_position.setCurrentIndex(1)
        form.addRow("Position:", self.logo_position)

        self.logo_size = QSpinBox()
        self.logo_size.setRange(20, 500)
        self.logo_size.setValue(100)
        form.addRow("Size:", self.logo_size)

        self.logo_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.logo_opacity_slider.setRange(10, 100)
        self.logo_opacity_slider.setValue(80)
        form.addRow("Opacity:", self.logo_opacity_slider)

        self.logo_margin = QSpinBox()
        self.logo_margin.setRange(0, 100)
        self.logo_margin.setValue(20)
        form.addRow("Margin:", self.logo_margin)

        group.setLayout(form)
        return group

    def _browse_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo",
            "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            self.logo_path.setText(path)

    def _on_style_changed(self, style_name: str) -> None:
        preset = SPECTRUM_PRESETS.get(style_name)
        if preset:
            self.sensitivity_slider.setValue(int(preset.sensitivity * 100))
            self.spec_height_slider.setValue(int(preset.height_ratio * 100))
            self.spec_opacity_slider.setValue(int(preset.opacity * 100))
            self.spec_glow_slider.setValue(int(preset.glow * 100))
            self.spec_blur_slider.setValue(int(preset.blur * 10))
            self.spec_color1.color = preset.color1
            self.spec_color2.color = preset.color2
            self.spec_gradient_check.setChecked(preset.use_gradient)
            self.spec_smoothing_slider.setValue(int(preset.smoothing * 100))
            idx = self.spec_position.findText(preset.position)
            if idx >= 0:
                self.spec_position.setCurrentIndex(idx)

    def get_video_config(self) -> VideoConfig:
        cfg = VideoConfig()
        res_text = self.resolution_combo.currentText()
        if "1920x1080" in res_text:
            cfg.width, cfg.height = 1920, 1080
        elif "1080x1920" in res_text:
            cfg.width, cfg.height = 1080, 1920
        elif "1280x720" in res_text:
            cfg.width, cfg.height = 1280, 720
        cfg.fps = int(self.fps_combo.currentText())
        cfg.bitrate = self.bitrate_combo.currentText()
        return cfg

    def get_spectrum_config(self) -> SpectrumConfig:
        cfg = SpectrumConfig()
        cfg.style = self.spectrum_style_combo.currentText()
        cfg.sensitivity = self.sensitivity_slider.value() / 100.0
        cfg.height_ratio = self.spec_height_slider.value() / 100.0
        cfg.position = self.spec_position.currentText()
        cfg.opacity = self.spec_opacity_slider.value() / 100.0
        cfg.glow = self.spec_glow_slider.value() / 100.0
        cfg.blur = self.spec_blur_slider.value() / 10.0
        cfg.color1 = self.spec_color1.color
        cfg.color2 = self.spec_color2.color
        cfg.use_gradient = self.spec_gradient_check.isChecked()
        cfg.smoothing = self.spec_smoothing_slider.value() / 100.0
        return cfg

    def get_lyric_config(self) -> LyricConfig:
        cfg = LyricConfig()
        cfg.font_family = self.font_family.currentText()
        cfg.font_size = self.font_size.value()
        cfg.color = self.lyric_color.color
        cfg.shadow_color = self.shadow_color.color
        cfg.shadow_offset = self.shadow_offset.value()
        cfg.stroke_color = self.stroke_color.color
        cfg.stroke_width = self.stroke_width.value()
        cfg.glow = self.lyric_glow_slider.value() / 100.0
        cfg.glow_color = self.lyric_glow_color.color
        cfg.position = self.lyric_position.currentText()
        cfg.alignment = self.lyric_alignment.currentText()
        cfg.show_next_line = self.show_next_line.isChecked()
        cfg.fade_duration = self.fade_duration.value()
        return cfg

    def get_logo_config(self) -> LogoConfig:
        cfg = LogoConfig()
        cfg.enabled = self.logo_enabled.isChecked()
        cfg.path = self.logo_path.text()
        cfg.position = self.logo_position.currentText()
        cfg.size = self.logo_size.value()
        cfg.opacity = self.logo_opacity_slider.value() / 100.0
        cfg.margin = self.logo_margin.value()
        return cfg
