# gui/widgets.py
"""
Widgets customizados reutilizáveis para a GUI.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QGroupBox, QPushButton, QColorDialog, QFrame,
    QSizePolicy, QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen


class LabeledSlider(QWidget):
    """Slider com label, valor e range configurável."""
    valueChanged = pyqtSignal(float)

    def __init__(
        self,
        label: str,
        min_val: float = 0.0,
        max_val: float = 1.0,
        step: float = 0.01,
        value: float = 0.5,
        suffix: str = "",
        description: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._min = min_val
        self._max = max_val
        self._step = step
        self._suffix = suffix
        self._multiplier = int(1.0 / step) if step < 1 else 1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(2)

        # Header row
        header = QHBoxLayout()
        self._label = QLabel(label)
        self._label.setStyleSheet("font-weight: bold; color: #ccc;")
        header.addWidget(self._label)
        header.addStretch()
        self._value_label = QLabel()
        self._value_label.setStyleSheet("color: #1db954; font-weight: bold;")
        header.addWidget(self._value_label)
        layout.addLayout(header)

        if description:
            desc = QLabel(description)
            desc.setStyleSheet("color: #666; font-size: 11px;")
            desc.setWordWrap(True)
            layout.addWidget(desc)

        # Slider row
        slider_row = QHBoxLayout()
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setMinimum(int(min_val * self._multiplier))
        self._slider.setMaximum(int(max_val * self._multiplier))
        self._slider.setSingleStep(1)
        self._slider.setValue(int(value * self._multiplier))
        self._slider.valueChanged.connect(self._on_slider_change)
        slider_row.addWidget(self._slider)

        self._spinbox = QDoubleSpinBox()
        self._spinbox.setRange(min_val, max_val)
        self._spinbox.setSingleStep(step)
        self._spinbox.setDecimals(len(str(step).split('.')[-1]) if '.' in str(step) else 0)
        self._spinbox.setValue(value)
        self._spinbox.setFixedWidth(85)
        self._spinbox.valueChanged.connect(self._on_spinbox_change)
        slider_row.addWidget(self._spinbox)

        layout.addLayout(slider_row)

        self._update_label(value)
        self._updating = False

    def _on_slider_change(self, raw):
        if self._updating:
            return
        self._updating = True
        val = raw / self._multiplier
        self._spinbox.setValue(val)
        self._update_label(val)
        self.valueChanged.emit(val)
        self._updating = False

    def _on_spinbox_change(self, val):
        if self._updating:
            return
        self._updating = True
        self._slider.setValue(int(val * self._multiplier))
        self._update_label(val)
        self.valueChanged.emit(val)
        self._updating = False

    def _update_label(self, val):
        if self._step >= 1:
            text = f"{int(val)}{self._suffix}"
        else:
            decimals = len(str(self._step).split('.')[-1]) if '.' in str(self._step) else 2
            text = f"{val:.{decimals}f}{self._suffix}"
        self._value_label.setText(text)

    def value(self) -> float:
        return self._spinbox.value()

    def setValue(self, val: float):
        self._updating = True
        self._spinbox.setValue(val)
        self._slider.setValue(int(val * self._multiplier))
        self._update_label(val)
        self._updating = False


class LabeledIntSlider(QWidget):
    """Slider para valores inteiros."""
    valueChanged = pyqtSignal(int)

    def __init__(
        self,
        label: str,
        min_val: int = 0,
        max_val: int = 100,
        value: int = 50,
        suffix: str = "",
        description: str = "",
        parent=None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(2)

        header = QHBoxLayout()
        self._label = QLabel(label)
        self._label.setStyleSheet("font-weight: bold; color: #ccc;")
        header.addWidget(self._label)
        header.addStretch()
        self._value_label = QLabel(f"{value}{suffix}")
        self._value_label.setStyleSheet("color: #1db954; font-weight: bold;")
        header.addWidget(self._value_label)
        layout.addLayout(header)

        if description:
            desc = QLabel(description)
            desc.setStyleSheet("color: #666; font-size: 11px;")
            desc.setWordWrap(True)
            layout.addWidget(desc)

        slider_row = QHBoxLayout()
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(min_val, max_val)
        self._slider.setValue(value)
        slider_row.addWidget(self._slider)

        self._spinbox = QSpinBox()
        self._spinbox.setRange(min_val, max_val)
        self._spinbox.setValue(value)
        self._spinbox.setFixedWidth(75)
        slider_row.addWidget(self._spinbox)

        layout.addLayout(slider_row)

        self._suffix = suffix
        self._updating = False
        self._slider.valueChanged.connect(self._on_slider)
        self._spinbox.valueChanged.connect(self._on_spinbox)

    def _on_slider(self, v):
        if self._updating:
            return
        self._updating = True
        self._spinbox.setValue(v)
        self._value_label.setText(f"{v}{self._suffix}")
        self.valueChanged.emit(v)
        self._updating = False

    def _on_spinbox(self, v):
        if self._updating:
            return
        self._updating = True
        self._slider.setValue(v)
        self._value_label.setText(f"{v}{self._suffix}")
        self.valueChanged.emit(v)
        self._updating = False

    def value(self) -> int:
        return self._spinbox.value()

    def setValue(self, val: int):
        self._updating = True
        self._spinbox.setValue(val)
        self._slider.setValue(val)
        self._value_label.setText(f"{val}{self._suffix}")
        self._updating = False


class LabeledCombo(QWidget):
    """ComboBox com label."""
    currentTextChanged = pyqtSignal(str)

    def __init__(
        self,
        label: str,
        options: list,
        current: str = "",
        description: str = "",
        parent=None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(2)

        self._label = QLabel(label)
        self._label.setStyleSheet("font-weight: bold; color: #ccc;")
        layout.addWidget(self._label)

        if description:
            desc = QLabel(description)
            desc.setStyleSheet("color: #666; font-size: 11px;")
            desc.setWordWrap(True)
            layout.addWidget(desc)

        self._combo = QComboBox()
        self._combo.addItems(options)
        if current and current in options:
            self._combo.setCurrentText(current)
        self._combo.currentTextChanged.connect(self.currentTextChanged.emit)
        layout.addWidget(self._combo)

    def currentText(self) -> str:
        return self._combo.currentText()

    def setCurrentText(self, text: str):
        self._combo.setCurrentText(text)


class LabeledCheck(QWidget):
    """Checkbox com label e descrição."""
    toggled = pyqtSignal(bool)

    def __init__(
        self,
        label: str,
        checked: bool = False,
        description: str = "",
        parent=None,
    ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(2)

        self._check = QCheckBox(label)
        self._check.setChecked(checked)
        self._check.setStyleSheet("font-weight: bold;")
        self._check.toggled.connect(self.toggled.emit)
        layout.addWidget(self._check)

        if description:
            desc = QLabel(description)
            desc.setStyleSheet("color: #666; font-size: 11px; margin-left: 26px;")
            desc.setWordWrap(True)
            layout.addWidget(desc)

    def isChecked(self) -> bool:
        return self._check.isChecked()

    def setChecked(self, val: bool):
        self._check.setChecked(val)


class ColorPickerButton(QWidget):
    """Botão que abre color picker e mostra preview da cor."""
    colorChanged = pyqtSignal(tuple)

    def __init__(self, label: str, color: tuple = (100, 0, 200), parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        self._label = QLabel(label)
        self._label.setStyleSheet("font-weight: bold; color: #ccc;")
        layout.addWidget(self._label)

        layout.addStretch()

        self._preview = QFrame()
        self._preview.setFixedSize(40, 24)
        self._preview.setFrameStyle(QFrame.Shape.Box)
        layout.addWidget(self._preview)

        self._btn = QPushButton("Escolher")
        self._btn.setFixedWidth(80)
        self._btn.clicked.connect(self._pick_color)
        layout.addWidget(self._btn)

        self._color = color
        self._update_preview()

    def _pick_color(self):
        qcolor = QColor(*self._color)
        result = QColorDialog.getColor(qcolor, self, "Escolher Cor")
        if result.isValid():
            self._color = (result.red(), result.green(), result.blue())
            self._update_preview()
            self.colorChanged.emit(self._color)

    def _update_preview(self):
        r, g, b = self._color
        self._preview.setStyleSheet(
            f"background-color: rgb({r},{g},{b}); "
            f"border: 2px solid #555; border-radius: 3px;"
        )

    def color(self) -> tuple:
        return self._color

    def setColor(self, color: tuple):
        self._color = color
        self._update_preview()


class BrightnessMapEditor(QWidget):
    """Editor visual para BRIGHTNESS_MAP com preview da curva."""
    mapChanged = pyqtSignal(list)

    def __init__(self, brightness_map: list, parent=None):
        super().__init__(parent)

        self._map = list(brightness_map)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Mapeamento de Intensidade → Brilho")
        header.setStyleSheet("font-weight: bold; color: #1db954; font-size: 14px;")
        layout.addWidget(header)

        desc = QLabel(
            "Define como a intensidade do áudio se traduz em brilho dos LEDs.\n"
            "Coluna esquerda = intensidade do áudio | Coluna direita = brilho do LED"
        )
        desc.setStyleSheet("color: #666; font-size: 11px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Curve preview
        self._curve_widget = CurvePreview(self._map)
        self._curve_widget.setFixedHeight(150)
        layout.addWidget(self._curve_widget)

        # Sliders for each point
        self._sliders_layout = QVBoxLayout()
        self._point_sliders = []

        for i, (inp, out) in enumerate(self._map):
            row = QHBoxLayout()

            lbl_in = QLabel(f"Input {inp:.2f}")
            lbl_in.setFixedWidth(80)
            lbl_in.setStyleSheet("color: #888;")
            row.addWidget(lbl_in)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 1000)
            slider.setValue(int(out * 1000))
            slider.valueChanged.connect(lambda v, idx=i: self._on_point_change(idx, v / 1000.0))
            row.addWidget(slider)

            lbl_out = QLabel(f"{out:.3f}")
            lbl_out.setFixedWidth(50)
            lbl_out.setStyleSheet("color: #1db954; font-weight: bold;")
            row.addWidget(lbl_out)

            self._sliders_layout.addLayout(row)
            self._point_sliders.append((slider, lbl_out, inp))

        layout.addLayout(self._sliders_layout)

        # Preset buttons
        presets = QHBoxLayout()
        for name, preset_map in [
            ("Linear", [(0, 0), (0.25, 0.25), (0.5, 0.5), (0.75, 0.75), (1, 1)]),
            ("Suave", [(0, 0.001), (0.15, 0.02), (0.3, 0.08), (0.5, 0.25), (0.7, 0.5), (0.85, 0.75), (1, 1)]),
            ("Agressivo", [(0, 0), (0.2, 0.01), (0.4, 0.03), (0.6, 0.15), (0.8, 0.5), (0.9, 0.8), (1, 1)]),
            ("Alto Contraste", [(0, 0), (0.3, 0.01), (0.5, 0.05), (0.7, 0.3), (0.85, 0.7), (1, 1)]),
        ]:
            btn = QPushButton(name)
            btn.setFixedWidth(100)
            btn.clicked.connect(lambda _, m=preset_map: self._apply_preset(m))
            presets.addWidget(btn)
        presets.addStretch()
        layout.addLayout(presets)

    def _on_point_change(self, idx, val):
        self._map[idx] = (self._map[idx][0], val)
        self._point_sliders[idx][1].setText(f"{val:.3f}")
        self._curve_widget.set_map(self._map)
        self.mapChanged.emit(self._map)

    def _apply_preset(self, preset):
        self._map = list(preset)

        # Rebuild sliders
        for slider, lbl, _ in self._point_sliders:
            slider.setParent(None)
            lbl.setParent(None)

        self._point_sliders.clear()

        # Remove all items from sliders layout
        while self._sliders_layout.count():
            item = self._sliders_layout.takeAt(0)
            if item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().setParent(None)

        for i, (inp, out) in enumerate(self._map):
            row = QHBoxLayout()

            lbl_in = QLabel(f"Input {inp:.2f}")
            lbl_in.setFixedWidth(80)
            lbl_in.setStyleSheet("color: #888;")
            row.addWidget(lbl_in)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 1000)
            slider.setValue(int(out * 1000))
            slider.valueChanged.connect(lambda v, idx=i: self._on_point_change(idx, v / 1000.0))
            row.addWidget(slider)

            lbl_out = QLabel(f"{out:.3f}")
            lbl_out.setFixedWidth(50)
            lbl_out.setStyleSheet("color: #1db954; font-weight: bold;")
            row.addWidget(lbl_out)

            self._sliders_layout.addLayout(row)
            self._point_sliders.append((slider, lbl_out, inp))

        self._curve_widget.set_map(self._map)
        self.mapChanged.emit(self._map)

    def get_map(self) -> list:
        return list(self._map)

    def set_map(self, m: list):
        self._apply_preset(m)


class CurvePreview(QWidget):
    """Desenha a curva do brightness map."""

    def __init__(self, brightness_map, parent=None):
        super().__init__(parent)
        self._map = list(brightness_map)
        self.setMinimumHeight(100)

    def set_map(self, m):
        self._map = list(m)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 20

        # Background
        painter.fillRect(0, 0, w, h, QBrush(QColor(25, 25, 25)))

        # Grid
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        for i in range(5):
            x = margin + (w - 2 * margin) * i / 4
            y = margin + (h - 2 * margin) * i / 4
            painter.drawLine(int(x), margin, int(x), h - margin)
            painter.drawLine(margin, int(y), w - margin, int(y))

        # Axes
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawRect(margin, margin, w - 2 * margin, h - 2 * margin)

        # Labels
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(margin, h - 4, "0")
        painter.drawText(w - margin - 10, h - 4, "1")
        painter.drawText(2, margin + 10, "1")
        painter.drawText(2, h - margin, "0")

        if len(self._map) < 2:
            painter.end()
            return

        # Linear interpolation curve (dense)
        painter.setPen(QPen(QColor(30, 185, 84), 2))
        points = []
        for px in range(w - 2 * margin + 1):
            inp = px / (w - 2 * margin)
            # Interpolate from map
            out = self._interpolate(inp)
            sx = margin + px
            sy = h - margin - out * (h - 2 * margin)
            points.append((int(sx), int(sy)))

        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1])

        # Points
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setBrush(QBrush(QColor(30, 185, 84)))
        for inp, out in self._map:
            sx = margin + inp * (w - 2 * margin)
            sy = h - margin - out * (h - 2 * margin)
            painter.drawEllipse(int(sx) - 4, int(sy) - 4, 8, 8)

        painter.end()

    def _interpolate(self, x):
        if x <= self._map[0][0]:
            return self._map[0][1]
        if x >= self._map[-1][0]:
            return self._map[-1][1]
        for i in range(len(self._map) - 1):
            x0, y0 = self._map[i]
            x1, y1 = self._map[i + 1]
            if x0 <= x <= x1:
                t = (x - x0) / (x1 - x0) if x1 != x0 else 0
                return y0 + t * (y1 - y0)
        return self._map[-1][1]


class StatusIndicator(QWidget):
    """Indicador de status (bolinha colorida + texto)."""

    def __init__(self, label: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._dot = QFrame()
        self._dot.setFixedSize(12, 12)
        self._dot.setStyleSheet(
            "background-color: #555; border-radius: 6px;"
        )
        layout.addWidget(self._dot)

        self._label = QLabel(label)
        self._label.setStyleSheet("color: #888;")
        layout.addWidget(self._label)
        layout.addStretch()

    def set_status(self, connected: bool, text: str = ""):
        color = "#1db954" if connected else "#e74c3c"
        self._dot.setStyleSheet(
            f"background-color: {color}; border-radius: 6px;"
        )
        if text:
            self._label.setText(text)
            self._label.setStyleSheet(f"color: {'#ccc' if connected else '#e74c3c'};")


class Separator(QFrame):
    """Linha horizontal separadora."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setStyleSheet("background-color: #333; max-height: 1px; margin: 8px 0;")