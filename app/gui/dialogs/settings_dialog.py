"""Application settings dialog (paths, FFmpeg, log level)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.utils.config import AppConfig


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(480)
        self.config = config

        outer = QVBoxLayout(self)
        form = QFormLayout()

        self.ffmpeg_path = self._path_row(self.config.get("ffmpeg_path", ""), file_mode=True)
        self.output_dir = self._path_row(self.config.get("output_dir", ""), file_mode=False)
        self.temp_dir = self._path_row(self.config.get("temp_dir", ""), file_mode=False)
        self.presets_dir = self._path_row(self.config.get("presets_dir", ""), file_mode=False)
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level.setCurrentText(str(self.config.get("log_level", "INFO")))

        form.addRow("FFmpeg path", self.ffmpeg_path)
        form.addRow("Output folder", self.output_dir)
        form.addRow("Temp folder", self.temp_dir)
        form.addRow("Presets folder", self.presets_dir)
        form.addRow("Log level", self.log_level)
        outer.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def _path_row(self, initial: str, file_mode: bool) -> QWidget:
        edit = QLineEdit(initial)
        button = QPushButton("Browse")

        def pick() -> None:
            if file_mode:
                path, _ = QFileDialog.getOpenFileName(self, "Select FFmpeg binary", edit.text())
            else:
                path = QFileDialog.getExistingDirectory(self, "Select folder", edit.text())
            if path:
                edit.setText(path)

        button.clicked.connect(pick)
        wrapper = QWidget()
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edit, 1)
        layout.addWidget(button)
        wrapper.line_edit = edit  # type: ignore[attr-defined]
        return wrapper

    def _on_ok(self) -> None:
        self.config.set("ffmpeg_path", self.ffmpeg_path.line_edit.text().strip())  # type: ignore[attr-defined]
        self.config.set("output_dir", self.output_dir.line_edit.text().strip())  # type: ignore[attr-defined]
        self.config.set("temp_dir", self.temp_dir.line_edit.text().strip())  # type: ignore[attr-defined]
        self.config.set("presets_dir", self.presets_dir.line_edit.text().strip())  # type: ignore[attr-defined]
        self.config.set("log_level", self.log_level.currentText())
        try:
            self.config.save()
        except Exception:  # pragma: no cover - tolerant
            pass
        self.accept()
