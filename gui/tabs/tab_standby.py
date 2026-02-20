# gui/tabs/tab_standby.py
"""Aba de configuração do modo standby (breathing quando pausado)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QScrollArea, QLabel,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from gui.widgets import LabeledSlider
from config_manager import ConfigManager

import math


class BreathingPreview(QWidget):
    """Preview animado do efeito breathing."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self._min_b = 0.15
        self._max_b = 0.40
        self._speed = 0.025
        self._phase = 0.0
        self._color = (100, 0, 200)

        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)  # ~30fps

    def _tick(self):
        self._phase += self._speed
        self.update()

    def set_params(self, min_b, max_b, speed):
        self._min_b = min_b
        self._max_b = max_b
        self._speed = speed

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QBrush

        painter = QPainter(self)

        brightness = self._min_b + (self._max_b - self._min_b) * (
            0.5 + 0.5 * math.sin(self._phase * 2 * math.pi)
        )

        r, g, b = self._color
        r = int(r * brightness)
        g = int(g * brightness)
        b = int(b * brightness)

        painter.fillRect(0, 0, self.width(), self.height(), QBrush(QColor(r, g, b)))
        painter.end()


class TabStandby(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        grp = QGroupBox("Modo Standby (Quando Pausado)")
        gl = QVBoxLayout(grp)

        desc = QLabel(
            "Quando o Spotify está pausado, os LEDs fazem um efeito de\n"
            "'respiração' suave com a última cor do álbum."
        )
        desc.setStyleSheet("color: #888;")
        desc.setWordWrap(True)
        gl.addWidget(desc)

        # Preview
        self.preview = BreathingPreview()
        gl.addWidget(self.preview)

        self.w_min = LabeledSlider(
            "Brilho Mínimo", 0.0, 0.5, 0.01, self.cfg.get("STANDBY_BRIGHTNESS_MIN"),
            description="Brilho mais baixo do breathing",
        )
        self.w_min.valueChanged.connect(self._on_change)
        gl.addWidget(self.w_min)

        self.w_max = LabeledSlider(
            "Brilho Máximo", 0.1, 1.0, 0.01, self.cfg.get("STANDBY_BRIGHTNESS_MAX"),
            description="Brilho mais alto do breathing",
        )
        self.w_max.valueChanged.connect(self._on_change)
        gl.addWidget(self.w_max)

        self.w_speed = LabeledSlider(
            "Velocidade", 0.005, 0.1, 0.005, self.cfg.get("STANDBY_BREATHING_SPEED"),
            description="Velocidade da oscilação (maior = mais rápido)",
        )
        self.w_speed.valueChanged.connect(self._on_change)
        gl.addWidget(self.w_speed)

        layout.addWidget(grp)
        layout.addStretch()
        self.setWidget(container)

    def _on_change(self, _=None):
        min_b = self.w_min.value()
        max_b = self.w_max.value()
        speed = self.w_speed.value()

        self.cfg.set("STANDBY_BRIGHTNESS_MIN", min_b)
        self.cfg.set("STANDBY_BRIGHTNESS_MAX", max_b)
        self.cfg.set("STANDBY_BREATHING_SPEED", speed)
        self.cfg.apply_to_config_module()

        self.preview.set_params(min_b, max_b, speed)

    def reload_values(self):
        self.w_min.setValue(self.cfg.get("STANDBY_BRIGHTNESS_MIN"))
        self.w_max.setValue(self.cfg.get("STANDBY_BRIGHTNESS_MAX"))
        self.w_speed.setValue(self.cfg.get("STANDBY_BREATHING_SPEED"))
        self.preview.set_params(
            self.w_min.value(), self.w_max.value(), self.w_speed.value()
        )