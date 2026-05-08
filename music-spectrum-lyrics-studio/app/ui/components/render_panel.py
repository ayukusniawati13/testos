"""
Render settings and output panel.
"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QSpinBox, QCheckBox, QFileDialog,
    QGridLayout, QProgressBar
)
from PyQt6.QtCore import pyqtSignal
from app.core.config import (
    ASPECT_RATIOS, RESOLUTIONS, PLATFORM_PRESETS, QUALITY_MODES, DIRS
)


class RenderPanel(QWidget):
    """Panel for render settings and controls."""
    render_requested = pyqtSignal()
    preview_requested = pyqtSignal()
    cancel_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Quality mode
        quality_group = QGroupBox("Quality Mode")
        quality_layout = QVBoxLayout()
        self.combo_quality = QComboBox()
        self.combo_quality.addItems(list(QUALITY_MODES.keys()))
        self.combo_quality.setCurrentText("Balanced")
        quality_layout.addWidget(self.combo_quality)

        info_labels = {
            "Low Spec": "Preview 480p, Render 720p, 24fps, ultrafast",
            "Balanced": "Preview 720p, Render 1080p, 30fps, medium",
            "High Quality": "Preview 1080p, Render 1080p, 60fps, slow",
        }
        self.lbl_quality_info = QLabel(info_labels.get("Balanced", ""))
        self.lbl_quality_info.setObjectName("statusLabel")
        quality_layout.addWidget(self.lbl_quality_info)
        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)

        # Resolution
        res_group = QGroupBox("Resolution & Aspect Ratio")
        res_layout = QGridLayout()

        res_layout.addWidget(QLabel("Aspect Ratio:"), 0, 0)
        self.combo_aspect = QComboBox()
        self.combo_aspect.addItems(list(ASPECT_RATIOS.keys()))
        res_layout.addWidget(self.combo_aspect, 0, 1)

        res_layout.addWidget(QLabel("Resolution:"), 1, 0)
        self.combo_resolution = QComboBox()
        self.combo_resolution.addItems(list(RESOLUTIONS.keys()))
        self.combo_resolution.setCurrentText("1080p Full HD")
        res_layout.addWidget(self.combo_resolution, 1, 1)

        res_layout.addWidget(QLabel("Platform Preset:"), 2, 0)
        self.combo_platform = QComboBox()
        self.combo_platform.addItems(["Custom"] + list(PLATFORM_PRESETS.keys()))
        res_layout.addWidget(self.combo_platform, 2, 1)

        res_layout.addWidget(QLabel("Width:"), 3, 0)
        self.spin_width = QSpinBox()
        self.spin_width.setRange(320, 7680)
        self.spin_width.setValue(1920)
        res_layout.addWidget(self.spin_width, 3, 1)

        res_layout.addWidget(QLabel("Height:"), 4, 0)
        self.spin_height = QSpinBox()
        self.spin_height.setRange(240, 4320)
        self.spin_height.setValue(1080)
        res_layout.addWidget(self.spin_height, 4, 1)

        res_layout.addWidget(QLabel("FPS:"), 5, 0)
        self.spin_fps = QSpinBox()
        self.spin_fps.setRange(15, 120)
        self.spin_fps.setValue(30)
        res_layout.addWidget(self.spin_fps, 5, 1)

        self.chk_maintain_ratio = QCheckBox("Maintain Aspect Ratio")
        self.chk_maintain_ratio.setChecked(True)
        res_layout.addWidget(self.chk_maintain_ratio, 6, 0, 1, 2)

        res_group.setLayout(res_layout)
        layout.addWidget(res_group)

        # Estimates
        est_group = QGroupBox("Estimates")
        est_layout = QGridLayout()

        est_layout.addWidget(QLabel("Est. Render Time:"), 0, 0)
        self.lbl_est_time = QLabel("-")
        est_layout.addWidget(self.lbl_est_time, 0, 1)

        est_layout.addWidget(QLabel("Est. Output Size:"), 1, 0)
        self.lbl_est_size = QLabel("-")
        est_layout.addWidget(self.lbl_est_size, 1, 1)

        est_group.setLayout(est_layout)
        layout.addWidget(est_group)

        # Output
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout()

        out_path_layout = QHBoxLayout()
        self.lbl_output = QLabel(DIRS["output"])
        self.lbl_output.setObjectName("statusLabel")
        out_path_layout.addWidget(self.lbl_output)
        self.btn_output_dir = QPushButton("Change")
        self.btn_output_dir.clicked.connect(self._select_output_dir)
        out_path_layout.addWidget(self.btn_output_dir)
        output_layout.addLayout(out_path_layout)

        self.chk_thumbnail = QCheckBox("Export Thumbnail (PNG)")
        output_layout.addWidget(self.chk_thumbnail)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        # Render progress
        progress_group = QGroupBox("Render Progress")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.lbl_progress = QLabel("Ready")
        progress_layout.addWidget(self.lbl_progress)

        btn_layout = QHBoxLayout()
        self.btn_preview = QPushButton("Preview (10-20s)")
        self.btn_preview.clicked.connect(self.preview_requested.emit)
        btn_layout.addWidget(self.btn_preview)

        self.btn_render = QPushButton("Start Render")
        self.btn_render.setObjectName("primaryButton")
        self.btn_render.clicked.connect(self.render_requested.emit)
        btn_layout.addWidget(self.btn_render)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.cancel_requested.emit)
        self.btn_cancel.setEnabled(False)
        btn_layout.addWidget(self.btn_cancel)
        progress_layout.addLayout(btn_layout)

        self.btn_open_output = QPushButton("Open Output Folder")
        self.btn_open_output.clicked.connect(self._open_output)
        progress_layout.addWidget(self.btn_open_output)

        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)

        layout.addStretch()

    def _connect_signals(self):
        self.combo_quality.currentTextChanged.connect(self._on_quality_changed)
        self.combo_platform.currentTextChanged.connect(self._on_platform_changed)
        self.combo_aspect.currentTextChanged.connect(self._on_aspect_changed)

    def _on_quality_changed(self, mode):
        info = QUALITY_MODES.get(mode, {})
        self.lbl_quality_info.setText(
            f"Preview {info.get('preview_resolution', '?')}p, "
            f"Render {info.get('render_resolution', '?')}p, "
            f"{info.get('fps', '?')}fps, {info.get('ffmpeg_preset', '?')}"
        )

    def _on_platform_changed(self, platform):
        preset = PLATFORM_PRESETS.get(platform)
        if preset:
            self.spin_width.setValue(preset["width"])
            self.spin_height.setValue(preset["height"])
            self.spin_fps.setValue(preset["fps"])

    def _on_aspect_changed(self, ratio_name):
        ratio = ASPECT_RATIOS.get(ratio_name)
        if ratio:
            w, h = ratio
            current_h = self.spin_height.value()
            self.spin_width.setValue(int(current_h * w / h))

    def _select_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.lbl_output.setText(folder)

    def _open_output(self):
        import subprocess
        import sys
        path = self.lbl_output.text()
        if os.path.isdir(path):
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])

    def update_progress(self, pct, msg):
        self.progress_bar.setValue(pct)
        self.lbl_progress.setText(msg)

    def update_estimates(self, duration):
        from app.utils.helpers import estimate_output_size, estimate_render_time
        w = self.spin_width.value()
        h = self.spin_height.value()
        fps = self.spin_fps.value()
        quality = self.combo_quality.currentText()
        preset = QUALITY_MODES.get(quality, {}).get("ffmpeg_preset", "medium")

        size_mb = estimate_output_size(duration, w, h, fps)
        render_time = estimate_render_time(duration, w, h, fps, preset)

        self.lbl_est_size.setText(f"~{size_mb:.0f} MB")
        from app.utils.helpers import format_time
        self.lbl_est_time.setText(f"~{format_time(render_time)}")

    def get_settings(self):
        quality = self.combo_quality.currentText()
        quality_settings = QUALITY_MODES.get(quality, {})
        return {
            "width": self.spin_width.value(),
            "height": self.spin_height.value(),
            "fps": self.spin_fps.value(),
            "quality_mode": quality,
            "ffmpeg_preset": quality_settings.get("ffmpeg_preset", "medium"),
            "aspect_ratio": self.combo_aspect.currentText(),
            "resolution": self.combo_resolution.currentText(),
            "output_dir": self.lbl_output.text(),
            "export_thumbnail": self.chk_thumbnail.isChecked(),
            "glow_enabled": quality_settings.get("glow_enabled", True),
            "reflection_enabled": quality_settings.get("reflection_enabled", True),
            "particle_enabled": quality_settings.get("particle_enabled", True),
        }
