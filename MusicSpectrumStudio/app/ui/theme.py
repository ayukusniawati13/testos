"""Dark theme stylesheet for the application."""

DARK_THEME = """
* { font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; }

QMainWindow, QDialog, QWidget {
    background-color: #11141B;
    color: #E6E8EE;
}

QGroupBox {
    background-color: #161A23;
    border: 1px solid #232A38;
    border-radius: 10px;
    margin-top: 14px;
    padding: 12px 12px 10px 12px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #8AB6FF;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
    background-color: #0F131B;
    border: 1px solid #2A3245;
    border-radius: 6px;
    padding: 6px 8px;
    color: #E6E8EE;
    selection-background-color: #5E64FF;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus,
QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #5E64FF;
}

QComboBox QAbstractItemView {
    background-color: #161A23;
    border: 1px solid #2A3245;
    selection-background-color: #5E64FF;
    color: #E6E8EE;
}

QPushButton {
    background-color: #5E64FF;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover { background-color: #7079FF; }
QPushButton:pressed { background-color: #4D52E5; }
QPushButton:disabled { background-color: #2A3245; color: #6C7689; }

QPushButton[secondary="true"] {
    background-color: #1E2433;
    color: #C5CCE0;
    border: 1px solid #2A3245;
}
QPushButton[secondary="true"]:hover { background-color: #2A3245; }

QPushButton[danger="true"] { background-color: #E54B6A; }
QPushButton[danger="true"]:hover { background-color: #FF6280; }

QPushButton[success="true"] { background-color: #2BB47C; }
QPushButton[success="true"]:hover { background-color: #36C68B; }

QTabWidget::pane { border: none; }
QTabBar::tab {
    background: #161A23;
    color: #98A1B6;
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}
QTabBar::tab:selected { background: #1E2433; color: #FFFFFF; }
QTabBar::tab:hover { background: #232A38; }

QCheckBox::indicator, QRadioButton::indicator {
    width: 18px; height: 18px;
    border-radius: 4px;
    border: 1px solid #3A4358;
    background: #0F131B;
}
QCheckBox::indicator:checked {
    background: #5E64FF;
    border-color: #5E64FF;
}
QRadioButton::indicator { border-radius: 9px; }
QRadioButton::indicator:checked {
    background: #5E64FF;
    border-color: #5E64FF;
}

QSlider::groove:horizontal {
    border: none; height: 4px; background: #2A3245; border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #5E64FF; width: 16px; height: 16px;
    margin: -7px 0; border-radius: 8px;
}

QProgressBar {
    background-color: #0F131B;
    color: white;
    border-radius: 6px;
    border: 1px solid #2A3245;
    text-align: center;
    height: 18px;
}
QProgressBar::chunk { background-color: #5E64FF; border-radius: 6px; }

QListWidget, QTreeWidget {
    background: #0F131B; border: 1px solid #2A3245; border-radius: 8px;
    alternate-background-color: #131826;
}
QListWidget::item, QTreeWidget::item { padding: 4px 6px; }
QListWidget::item:selected, QTreeWidget::item:selected { background: #5E64FF; }

QScrollBar:vertical, QScrollBar:horizontal {
    background: transparent; width: 10px; height: 10px; margin: 2px;
}
QScrollBar::handle { background: #2A3245; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:hover { background: #3A4358; }
QScrollBar::add-line, QScrollBar::sub-line { background: transparent; height: 0; width: 0; }

QStatusBar { background: #0F131B; color: #98A1B6; }
QLabel[role="title"] { font-size: 18px; font-weight: 700; color: #FFFFFF; }
QLabel[role="muted"] { color: #98A1B6; }
QLabel[role="badge_ok"] { color: #2BB47C; font-weight: 700; }
QLabel[role="badge_bad"] { color: #E54B6A; font-weight: 700; }
QLabel[role="badge_warn"] { color: #FFC857; font-weight: 700; }
QFrame[role="divider"] { background: #232A38; border: none; max-height: 1px; }
"""
