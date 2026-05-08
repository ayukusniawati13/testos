"""
General settings panel.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QCheckBox, QFileDialog, QGridLayout, QSpinBox
)
from PyQt6.QtCore import pyqtSignal
from app.core.config import QUALITY_MODES, DIRS, load_settings, save_settings


class SettingsPanel(QWidget):
    """Panel for general application settings."""
    settings_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_current()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # General
        gen_group = QGroupBox("General")
        gen_layout = QGridLayout()

        gen_layout.addWidget(QLabel("Default Quality:"), 0, 0)
        self.combo_quality = QComboBox()
        self.combo_quality.addItems(list(QUALITY_MODES.keys()))
        gen_layout.addWidget(self.combo_quality, 0, 1)

        gen_layout.addWidget(QLabel("Theme:"), 1, 0)
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Dark Mode"])
        gen_layout.addWidget(self.combo_theme, 1, 1)

        self.chk_autosave = QCheckBox("Autosave Projects")
        self.chk_autosave.setChecked(True)
        gen_layout.addWidget(self.chk_autosave, 2, 0, 1, 2)

        gen_layout.addWidget(QLabel("Autosave Interval (s):"), 3, 0)
        self.spin_autosave = QSpinBox()
        self.spin_autosave.setRange(10, 600)
        self.spin_autosave.setValue(60)
        gen_layout.addWidget(self.spin_autosave, 3, 1)

        gen_group.setLayout(gen_layout)
        layout.addWidget(gen_group)

        # Paths
        path_group = QGroupBox("Default Paths")
        path_layout = QGridLayout()

        path_layout.addWidget(QLabel("Output:"), 0, 0)
        self.lbl_output = QLabel(DIRS["output"])
        path_layout.addWidget(self.lbl_output, 0, 1)
        btn_output = QPushButton("Change")
        btn_output.clicked.connect(self._change_output)
        path_layout.addWidget(btn_output, 0, 2)

        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        # Temp cleanup
        temp_group = QGroupBox("Temporary Files")
        temp_layout = QVBoxLayout()

        self.btn_clean_temp = QPushButton("Clean Temp Files")
        self.btn_clean_temp.clicked.connect(self._clean_temp)
        temp_layout.addWidget(self.btn_clean_temp)

        self.btn_clean_cache = QPushButton("Clean Cache Files")
        self.btn_clean_cache.clicked.connect(self._clean_cache)
        temp_layout.addWidget(self.btn_clean_cache)

        self.lbl_temp_info = QLabel("")
        temp_layout.addWidget(self.lbl_temp_info)

        temp_group.setLayout(temp_layout)
        layout.addWidget(temp_group)

        # Save
        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setObjectName("successButton")
        self.btn_save.clicked.connect(self._save)
        layout.addWidget(self.btn_save)

        layout.addStretch()

    def _load_current(self):
        try:
            settings = load_settings()
            self.combo_quality.setCurrentText(settings.get("quality_mode", "Balanced"))
            self.chk_autosave.setChecked(settings.get("autosave", True))
        except Exception:
            pass

    def _change_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.lbl_output.setText(folder)

    def _clean_temp(self):
        try:
            from app.utils.helpers import clean_temp_files
            clean_temp_files(DIRS["temp"])
            self.lbl_temp_info.setText("Temp files cleaned")
        except Exception as e:
            self.lbl_temp_info.setText(f"Error: {e}")

    def _clean_cache(self):
        try:
            from app.utils.helpers import clean_temp_files
            clean_temp_files(DIRS["cache"])
            self.lbl_temp_info.setText("Cache files cleaned")
        except Exception as e:
            self.lbl_temp_info.setText(f"Error: {e}")

    def _save(self):
        try:
            settings = load_settings()
            settings["quality_mode"] = self.combo_quality.currentText()
            settings["autosave"] = self.chk_autosave.isChecked()
            settings["output_dir"] = self.lbl_output.text()
            save_settings(settings)
            self.settings_saved.emit()
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Save Error", str(e))

    def get_settings(self):
        return {
            "quality_mode": self.combo_quality.currentText(),
            "autosave": self.chk_autosave.isChecked(),
            "autosave_interval": self.spin_autosave.value(),
            "output_dir": self.lbl_output.text(),
        }
