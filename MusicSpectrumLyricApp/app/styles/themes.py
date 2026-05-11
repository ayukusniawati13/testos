"""Dark mode theme stylesheet for the application."""

DARK_THEME = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #2d2d4a;
    background-color: #1a1a2e;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #16213e;
    color: #8888aa;
    padding: 10px 24px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
    font-weight: 500;
}

QTabBar::tab:selected {
    color: #00d4ff;
    border-bottom: 2px solid #00d4ff;
    background-color: #1a1a2e;
}

QTabBar::tab:hover {
    color: #ffffff;
    background-color: #202040;
}

QPushButton {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #1a5276;
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #1a5276;
    border-color: #00d4ff;
}

QPushButton:pressed {
    background-color: #0a2647;
}

QPushButton#renderBtn {
    background-color: #00875a;
    border-color: #00a86b;
    font-size: 14px;
    font-weight: 600;
    padding: 10px 30px;
}

QPushButton#renderBtn:hover {
    background-color: #00a86b;
}

QPushButton#stopBtn {
    background-color: #c0392b;
    border-color: #e74c3c;
}

QPushButton#stopBtn:hover {
    background-color: #e74c3c;
}

QGroupBox {
    border: 1px solid #2d2d4a;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 20px;
    font-weight: 600;
    color: #00d4ff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
}

QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #16213e;
    border: 1px solid #2d2d4a;
    border-radius: 4px;
    padding: 6px 10px;
    color: #e0e0e0;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #00d4ff;
}

QComboBox {
    background-color: #16213e;
    border: 1px solid #2d2d4a;
    border-radius: 4px;
    padding: 6px 10px;
    color: #e0e0e0;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #00d4ff;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox QAbstractItemView {
    background-color: #16213e;
    border: 1px solid #2d2d4a;
    color: #e0e0e0;
    selection-background-color: #0f3460;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #2d2d4a;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #00d4ff;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00d4ff, stop:1 #e040fb);
    border-radius: 3px;
}

QProgressBar {
    background-color: #16213e;
    border: 1px solid #2d2d4a;
    border-radius: 4px;
    text-align: center;
    color: #e0e0e0;
    min-height: 22px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #00d4ff, stop:1 #e040fb);
    border-radius: 3px;
}

QTextEdit, QPlainTextEdit {
    background-color: #0d1117;
    border: 1px solid #2d2d4a;
    border-radius: 4px;
    color: #8b949e;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
}

QTableWidget {
    background-color: #16213e;
    border: 1px solid #2d2d4a;
    border-radius: 4px;
    gridline-color: #2d2d4a;
    color: #e0e0e0;
}

QTableWidget::item {
    padding: 6px;
}

QTableWidget::item:selected {
    background-color: #0f3460;
}

QHeaderView::section {
    background-color: #1a1a2e;
    color: #00d4ff;
    border: 1px solid #2d2d4a;
    padding: 8px;
    font-weight: 600;
}

QLabel {
    color: #c0c0d0;
}

QLabel#titleLabel {
    font-size: 22px;
    font-weight: 700;
    color: #00d4ff;
}

QLabel#statusLabel {
    font-size: 12px;
    color: #8888aa;
}

QLabel#ffmpegOk {
    color: #00e676;
    font-weight: 600;
}

QLabel#ffmpegError {
    color: #ff5252;
    font-weight: 600;
}

QScrollBar:vertical {
    background: #1a1a2e;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: #2d2d4a;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #00d4ff;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QCheckBox {
    color: #c0c0d0;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #2d2d4a;
    border-radius: 4px;
    background-color: #16213e;
}

QCheckBox::indicator:checked {
    background-color: #00d4ff;
    border-color: #00d4ff;
}

QRadioButton {
    color: #c0c0d0;
    spacing: 8px;
}

QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #2d2d4a;
    border-radius: 8px;
    background-color: #16213e;
}

QRadioButton::indicator:checked {
    background-color: #00d4ff;
    border-color: #00d4ff;
}
"""
