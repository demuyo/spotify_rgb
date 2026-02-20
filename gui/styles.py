# gui/styles.py
"""
Tema escuro para a GUI do Spotify RGB Sync.
Inspirado no visual do Spotify (escuro com verde).
"""

DARK_THEME = """
QMainWindow {
    background-color: #121212;
}

QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #333;
    background-color: #1a1a1a;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #252525;
    color: #888;
    padding: 8px 18px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 80px;
}

QTabBar::tab:selected {
    background-color: #1a1a1a;
    color: #1db954;
    border-bottom: 2px solid #1db954;
}

QTabBar::tab:hover {
    background-color: #2a2a2a;
    color: #ccc;
}

QGroupBox {
    border: 1px solid #333;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: #1db954;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

QLabel {
    color: #ccc;
    background: transparent;
}

QLabel[class="header"] {
    color: #1db954;
    font-size: 15px;
    font-weight: bold;
}

QLabel[class="description"] {
    color: #777;
    font-size: 11px;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #333;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #1db954;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QSlider::handle:horizontal:hover {
    background: #1ed760;
}

QSlider::sub-page:horizontal {
    background: #1db954;
    border-radius: 3px;
}

QSpinBox, QDoubleSpinBox {
    background-color: #252525;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e0e0e0;
    min-width: 80px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #1db954;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #333;
    border: none;
    width: 20px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #1db954;
}

QComboBox {
    background-color: #252525;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 5px 10px;
    color: #e0e0e0;
    min-width: 120px;
}

QComboBox:focus {
    border-color: #1db954;
}

QComboBox::drop-down {
    border: none;
    width: 25px;
}

QComboBox QAbstractItemView {
    background-color: #252525;
    border: 1px solid #444;
    color: #e0e0e0;
    selection-background-color: #1db954;
}

QCheckBox {
    spacing: 8px;
    color: #ccc;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 3px;
    border: 2px solid #555;
    background-color: #252525;
}

QCheckBox::indicator:checked {
    background-color: #1db954;
    border-color: #1db954;
}

QCheckBox::indicator:hover {
    border-color: #1db954;
}

QPushButton {
    background-color: #252525;
    color: #e0e0e0;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 8px 20px;
    font-weight: bold;
    min-width: 90px;
}

QPushButton:hover {
    background-color: #333;
    border-color: #1db954;
}

QPushButton:pressed {
    background-color: #1db954;
    color: #000;
}

QPushButton[class="primary"] {
    background-color: #1db954;
    color: #000;
    border: none;
}

QPushButton[class="primary"]:hover {
    background-color: #1ed760;
}

QPushButton[class="danger"] {
    background-color: #e74c3c;
    color: #fff;
    border: none;
}

QPushButton[class="danger"]:hover {
    background-color: #ff6b6b;
}

QLineEdit {
    background-color: #252525;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 6px 10px;
    color: #e0e0e0;
}

QLineEdit:focus {
    border-color: #1db954;
}

QProgressBar {
    background-color: #252525;
    border: 1px solid #333;
    border-radius: 4px;
    height: 8px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background-color: #1db954;
    border-radius: 3px;
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background-color: #1a1a1a;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #444;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #1db954;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QStatusBar {
    background-color: #0a0a0a;
    color: #888;
    border-top: 1px solid #333;
    font-size: 11px;
}

QMenu {
    background-color: #252525;
    border: 1px solid #444;
    border-radius: 4px;
    padding: 4px;
}

QMenu::item {
    padding: 6px 30px;
    border-radius: 3px;
}

QMenu::item:selected {
    background-color: #1db954;
    color: #000;
}

QToolTip {
    background-color: #333;
    color: #e0e0e0;
    border: 1px solid #555;
    border-radius: 4px;
    padding: 6px;
    font-size: 12px;
}
"""