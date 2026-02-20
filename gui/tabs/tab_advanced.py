# gui/tabs/tab_advanced.py
"""Aba de configurações avançadas (LEDs, OpenRGB, quantized)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QScrollArea, QLabel,
    QLineEdit, QHBoxLayout, QPushButton,
)
from PyQt6.QtCore import Qt

from gui.widgets import LabeledIntSlider, LabeledSlider, Separator
from config_manager import ConfigManager


class TabAdvanced(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # ── OpenRGB ──
        grp_rgb = QGroupBox("OpenRGB")
        rl = QVBoxLayout(grp_rgb)

        row_host = QHBoxLayout()
        row_host.addWidget(QLabel("Host:"))
        self.w_host = QLineEdit(self.cfg.get("OPENRGB_HOST"))
        self.w_host.setFixedWidth(200)
        self.w_host.editingFinished.connect(
            lambda: self._set("OPENRGB_HOST", self.w_host.text())
        )
        row_host.addWidget(self.w_host)
        row_host.addStretch()
        rl.addLayout(row_host)

        self.w_port = LabeledIntSlider(
            "Porta", 1024, 65535, self.cfg.get("OPENRGB_PORT"),
        )
        self.w_port.valueChanged.connect(
            lambda v: self._set("OPENRGB_PORT", v)
        )
        rl.addWidget(self.w_port)

        row_name = QHBoxLayout()
        row_name.addWidget(QLabel("Nome:"))
        self.w_name = QLineEdit(self.cfg.get("OPENRGB_NAME"))
        self.w_name.setFixedWidth(200)
        self.w_name.editingFinished.connect(
            lambda: self._set("OPENRGB_NAME", self.w_name.text())
        )
        row_name.addWidget(self.w_name)
        row_name.addStretch()
        rl.addLayout(row_name)

        layout.addWidget(grp_rgb)

        # ── LED Configuration ──
        grp_led = QGroupBox("Configuração de LEDs")
        ll = QVBoxLayout(grp_led)

        self.w_skip_start = LabeledIntSlider(
            "Pular no Início", 0, 30, self.cfg.get("LED_SKIP_START"), " LEDs",
            "LEDs invisíveis no começo da fita (ex: backplate)",
        )
        self.w_skip_start.valueChanged.connect(
            lambda v: self._set("LED_SKIP_START", v)
        )
        ll.addWidget(self.w_skip_start)

        self.w_skip_end = LabeledIntSlider(
            "Pular no Final", 0, 30, self.cfg.get("LED_SKIP_END"), " LEDs",
        )
        self.w_skip_end.valueChanged.connect(
            lambda v: self._set("LED_SKIP_END", v)
        )
        ll.addWidget(self.w_skip_end)

        info = QLabel(
            "💡 LED_COUNT = None → auto-detecta\n"
            "💡 SELECTED_DEVICES = None → usa todos"
        )
        info.setStyleSheet("color: #666; font-size: 11px;")
        ll.addWidget(info)

        layout.addWidget(grp_led)

        # ── Quantized ──
        grp_quant = QGroupBox("Quantized Update")
        ql = QVBoxLayout(grp_quant)

        self.w_quant_interval = LabeledSlider(
            "Update Interval", 0.05, 1.0, 0.05, self.cfg.get("QUANTIZED_UPDATE_INTERVAL"), "s",
            "Intervalo entre updates dos LEDs (menor = mais fluido, mais CPU)",
        )
        self.w_quant_interval.valueChanged.connect(
            lambda v: self._set("QUANTIZED_UPDATE_INTERVAL", v)
        )
        ql.addWidget(self.w_quant_interval)

        self.w_quant_levels = LabeledIntSlider(
            "Níveis", 2, 20, self.cfg.get("QUANTIZED_LEVELS"),
            description="Número de níveis de quantização",
        )
        self.w_quant_levels.valueChanged.connect(
            lambda v: self._set("QUANTIZED_LEVELS", v)
        )
        ql.addWidget(self.w_quant_levels)

        layout.addWidget(grp_quant)

        layout.addStretch()
        self.setWidget(container)

    def _set(self, key, val):
        self.cfg.set(key, val)
        self.cfg.apply_to_config_module()

    def reload_values(self):
        self.w_host.setText(self.cfg.get("OPENRGB_HOST"))
        self.w_port.setValue(self.cfg.get("OPENRGB_PORT"))
        self.w_name.setText(self.cfg.get("OPENRGB_NAME"))
        self.w_skip_start.setValue(self.cfg.get("LED_SKIP_START"))
        self.w_skip_end.setValue(self.cfg.get("LED_SKIP_END"))
        self.w_quant_interval.setValue(self.cfg.get("QUANTIZED_UPDATE_INTERVAL"))
        self.w_quant_levels.setValue(self.cfg.get("QUANTIZED_LEVELS"))