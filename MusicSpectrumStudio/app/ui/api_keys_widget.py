"""Multi-API-key manager widget for Groq."""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from ..config import ApiKeyEntry
from ..core.groq_client import GroqClient

logger = logging.getLogger(__name__)


class _TestKeyWorker(QThread):
    finished = Signal(int, bool, str)

    def __init__(self, row: int, key: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.row = row
        self.key = key

    def run(self) -> None:  # noqa: D401
        client = GroqClient()
        ok, msg = client.test_key(self.key)
        self.finished.emit(self.row, ok, msg)


class ApiKeysWidget(QGroupBox):
    keysChanged = Signal()

    def __init__(self, get_keys: Callable[[], list[ApiKeyEntry]], set_keys: Callable[[list[ApiKeyEntry]], None]):
        super().__init__("Groq API Keys (rotasi otomatis bila limit)")
        self._get_keys = get_keys
        self._set_keys = set_keys
        self._workers: list[_TestKeyWorker] = []
        self._build()
        self.refresh_from_storage()

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setSpacing(8)

        hint = QLabel(
            "Tambahkan beberapa API key Groq. Aplikasi akan memakai key pertama dan "
            "pindah otomatis ke key berikutnya bila terkena rate-limit / kuota."
        )
        hint.setProperty("role", "muted")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Aktif", "Label", "API Key", "Status / Hasil", ""])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        outer.addWidget(self.table)

        button_row = QHBoxLayout()
        add_btn = QPushButton("+ Tambah API Key")
        add_btn.clicked.connect(self._add_blank_row)
        test_all_btn = QPushButton("Tes Semua")
        test_all_btn.setProperty("secondary", True)
        test_all_btn.clicked.connect(self._test_all)
        button_row.addWidget(add_btn)
        button_row.addWidget(test_all_btn)
        button_row.addStretch()
        outer.addLayout(button_row)

    # ---- model <-> table ---------------------------------------------------
    def refresh_from_storage(self) -> None:
        keys = self._get_keys()
        if not keys:
            keys = [ApiKeyEntry()]
        self.table.setRowCount(0)
        for entry in keys:
            self._append_row(entry)

    def _append_row(self, entry: ApiKeyEntry | None = None) -> int:
        entry = entry or ApiKeyEntry()
        row = self.table.rowCount()
        self.table.insertRow(row)

        check = QCheckBox()
        check.setChecked(entry.enabled)
        check.stateChanged.connect(self._on_changed)
        check_holder = QWidget()
        h = QHBoxLayout(check_holder)
        h.setContentsMargins(8, 0, 8, 0)
        h.addWidget(check)
        h.addStretch()
        self.table.setCellWidget(row, 0, check_holder)
        check_holder.setProperty("checkbox", check)

        label = QLineEdit(entry.label)
        label.setPlaceholderText("Nama key (opsional)")
        label.textChanged.connect(self._on_changed)
        self.table.setCellWidget(row, 1, label)

        key_edit = QLineEdit(entry.key)
        key_edit.setPlaceholderText("gsk_...")
        key_edit.setEchoMode(QLineEdit.Password)
        key_edit.textChanged.connect(self._on_changed)
        self.table.setCellWidget(row, 2, key_edit)

        status_label = QLabel("Belum diuji")
        status_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        status_label.setProperty("role", "muted")
        self.table.setCellWidget(row, 3, status_label)

        btn_widget = QWidget()
        bh = QHBoxLayout(btn_widget)
        bh.setContentsMargins(0, 0, 0, 0)
        test_btn = QPushButton("Tes")
        test_btn.setProperty("secondary", True)
        test_btn.clicked.connect(lambda _, r=row: self._test_row(r))
        remove_btn = QPushButton("Hapus")
        remove_btn.setProperty("danger", True)
        remove_btn.clicked.connect(lambda _, r=row: self._remove_row(r))
        bh.addWidget(test_btn)
        bh.addWidget(remove_btn)
        self.table.setCellWidget(row, 4, btn_widget)
        return row

    def _row_entry(self, row: int) -> ApiKeyEntry:
        check_widget = self.table.cellWidget(row, 0)
        check = check_widget.property("checkbox") if check_widget else None
        label_edit = self.table.cellWidget(row, 1)
        key_edit = self.table.cellWidget(row, 2)
        return ApiKeyEntry(
            enabled=check.isChecked() if check else True,
            label=label_edit.text() if label_edit else "",
            key=key_edit.text() if key_edit else "",
        )

    def entries(self) -> list[ApiKeyEntry]:
        rows = [self._row_entry(r) for r in range(self.table.rowCount())]
        return [r for r in rows if r.key]

    def _add_blank_row(self) -> None:
        self._append_row()
        self._on_changed()

    def _remove_row(self, row: int) -> None:
        self.table.removeRow(row)
        self._on_changed()

    def _on_changed(self) -> None:
        self._set_keys(self.entries())
        self.keysChanged.emit()

    # ---- testing -----------------------------------------------------------
    def _test_row(self, row: int) -> None:
        if row >= self.table.rowCount():
            return
        entry = self._row_entry(row)
        if not entry.key:
            self._set_status(row, False, "API key kosong")
            return
        self._set_status(row, None, "Menguji...")
        worker = _TestKeyWorker(row, entry.key, self)
        worker.finished.connect(self._on_test_done)
        worker.start()
        self._workers.append(worker)

    def _test_all(self) -> None:
        for r in range(self.table.rowCount()):
            self._test_row(r)

    def _on_test_done(self, row: int, ok: bool, msg: str) -> None:
        self._set_status(row, ok, msg)
        # Drop finished workers
        self._workers = [w for w in self._workers if w.isRunning()]

    def _set_status(self, row: int, ok: bool | None, message: str) -> None:
        widget = self.table.cellWidget(row, 3)
        if not isinstance(widget, QLabel):
            return
        widget.setText(message)
        if ok is True:
            widget.setProperty("role", "badge_ok")
        elif ok is False:
            widget.setProperty("role", "badge_bad")
        else:
            widget.setProperty("role", "muted")
        widget.style().unpolish(widget)
        widget.style().polish(widget)
