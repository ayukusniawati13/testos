"""Preset selector / saver dialog."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.core.project_manager import ProjectManager


class PresetDialog(QDialog):
    """Lets the user pick / save / delete a preset.

    The dialog returns the chosen preset payload through :attr:`selected_payload`.
    """

    def __init__(self, manager: ProjectManager, current_payload: dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Presets")
        self.setMinimumSize(420, 360)
        self.manager = manager
        self.current_payload = current_payload
        self.selected_payload: Optional[dict] = None

        outer = QVBoxLayout(self)
        outer.addWidget(QLabel("Saved presets"))
        self.list = QListWidget()
        outer.addWidget(self.list, 1)

        actions = QHBoxLayout()
        self.btn_save = QPushButton("Save current as...")
        self.btn_load = QPushButton("Load")
        self.btn_load.setObjectName("primary")
        self.btn_delete = QPushButton("Delete")
        self.btn_close = QPushButton("Close")
        actions.addWidget(self.btn_save)
        actions.addWidget(self.btn_load)
        actions.addWidget(self.btn_delete)
        actions.addStretch(1)
        actions.addWidget(self.btn_close)
        outer.addLayout(actions)

        self.btn_save.clicked.connect(self._on_save)
        self.btn_load.clicked.connect(self._on_load)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_close.clicked.connect(self.reject)
        self.list.itemDoubleClicked.connect(lambda *_: self._on_load())

        self._refresh()

    def _refresh(self) -> None:
        self.list.clear()
        for path in self.manager.list_presets():
            item = QListWidgetItem(path.stem)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.list.addItem(item)

    def _selected_path(self) -> Optional[Path]:
        item = self.list.currentItem()
        if item is None:
            return None
        return Path(str(item.data(Qt.ItemDataRole.UserRole)))

    def _on_save(self) -> None:
        name, ok = QInputDialog.getText(self, "Save preset", "Name:")
        if not ok or not name.strip():
            return
        try:
            self.manager.save_preset(name.strip(), self.current_payload)
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return
        self._refresh()

    def _on_load(self) -> None:
        path = self._selected_path()
        if path is None:
            return
        try:
            self.selected_payload = self.manager.load_preset(path)
        except Exception as exc:
            QMessageBox.critical(self, "Load failed", str(exc))
            return
        self.accept()

    def _on_delete(self) -> None:
        path = self._selected_path()
        if path is None:
            return
        confirm = QMessageBox.question(
            self, "Delete preset", f"Delete '{path.stem}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            self.manager.delete_preset(path)
        except Exception as exc:
            QMessageBox.critical(self, "Delete failed", str(exc))
            return
        self._refresh()
