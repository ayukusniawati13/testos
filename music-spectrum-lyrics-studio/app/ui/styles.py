"""
Application dark theme stylesheet.
"""

DARK_THEME = """
QMainWindow {
    background-color: #1a1a2e;
    color: #e0e0e0;
}

QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #333366;
    background-color: #16213e;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #1a1a2e;
    color: #8888aa;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    border: 1px solid #333366;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #16213e;
    color: #00d4ff;
    border-bottom: 2px solid #00d4ff;
}

QTabBar::tab:hover {
    background-color: #1f2b47;
    color: #ffffff;
}

QPushButton {
    background-color: #0f3460;
    color: #ffffff;
    border: 1px solid #1a5276;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: bold;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #1a5276;
    border-color: #00d4ff;
}

QPushButton:pressed {
    background-color: #0a2647;
}

QPushButton:disabled {
    background-color: #2a2a3e;
    color: #555577;
    border-color: #333355;
}

QPushButton#primaryButton {
    background-color: #e94560;
    border-color: #e94560;
}

QPushButton#primaryButton:hover {
    background-color: #ff5a7a;
}

QPushButton#successButton {
    background-color: #00b894;
    border-color: #00b894;
}

QPushButton#successButton:hover {
    background-color: #00d4aa;
}

QComboBox {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #333366;
    padding: 6px 10px;
    border-radius: 4px;
    min-height: 20px;
}

QComboBox:hover {
    border-color: #00d4ff;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #333366;
    selection-background-color: #0f3460;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #333366;
    padding: 6px 10px;
    border-radius: 4px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #00d4ff;
}

QSpinBox, QDoubleSpinBox {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #333366;
    padding: 4px 8px;
    border-radius: 4px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #00d4ff;
}

QSlider::groove:horizontal {
    height: 6px;
    background-color: #333366;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #00d4ff;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::sub-page:horizontal {
    background-color: #0f3460;
    border-radius: 3px;
}

QProgressBar {
    background-color: #16213e;
    border: 1px solid #333366;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
    min-height: 20px;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #e94560, stop:1 #00d4ff);
    border-radius: 3px;
}

QGroupBox {
    border: 1px solid #333366;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: bold;
    color: #00d4ff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

QCheckBox {
    color: #e0e0e0;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #333366;
    border-radius: 4px;
    background-color: #16213e;
}

QCheckBox::indicator:checked {
    background-color: #00d4ff;
    border-color: #00d4ff;
}

QLabel {
    color: #c0c0d0;
}

QLabel#headerLabel {
    font-size: 18px;
    font-weight: bold;
    color: #00d4ff;
}

QLabel#statusLabel {
    color: #888899;
    font-size: 12px;
}

QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 10px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #333366;
    min-height: 30px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4444aa;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #1a1a2e;
    height: 10px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #333366;
    min-width: 30px;
    border-radius: 5px;
}

QListWidget, QTreeWidget, QTableWidget {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #333366;
    border-radius: 4px;
    alternate-background-color: #1a2540;
}

QListWidget::item:selected, QTreeWidget::item:selected {
    background-color: #0f3460;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #1a1a2e;
    color: #8888aa;
    border: 1px solid #333366;
    padding: 6px;
    font-weight: bold;
}

QSplitter::handle {
    background-color: #333366;
    width: 2px;
}

QMenuBar {
    background-color: #1a1a2e;
    color: #e0e0e0;
    border-bottom: 1px solid #333366;
}

QMenuBar::item:selected {
    background-color: #0f3460;
}

QMenu {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #333366;
}

QMenu::item:selected {
    background-color: #0f3460;
}

QStatusBar {
    background-color: #0f0f1e;
    color: #888899;
    border-top: 1px solid #333366;
}

QToolTip {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #00d4ff;
    padding: 4px;
    border-radius: 4px;
}
"""
