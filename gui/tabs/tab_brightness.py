# gui/tabs/tab_brightness.py
"""Aba de configuração de brilho e mapeamento."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QScrollArea,
)
from PyQt6.QtCore import Qt

from gui.widgets import LabeledSlider, BrightnessMapEditor, Separator
from config_manager import ConfigManager


class TabBrightness(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # ── Brightness Map ──
        grp_map = QGroupBox("Curva de Brilho")
        ml = QVBoxLayout(grp_map)

        self.w_brightness_map = BrightnessMapEditor(
            self.cfg.get("BRIGHTNESS_MAP")
        )
        self.w_brightness_map.mapChanged.connect(
            lambda m: self._set("BRIGHTNESS_MAP", m)
        )
        ml.addWidget(self.w_brightness_map)

        layout.addWidget(grp_map)

        # ── Brightness Levels ──
        grp_levels = QGroupBox("Níveis de Brilho por Evento")
        ll = QVBoxLayout(grp_levels)

        self.w_floor = LabeledSlider(
            "Floor (Mínimo)", 0.0, 0.3, 0.01, self.cfg.get("BRIGHTNESS_FLOOR"),
            description="Brilho mínimo absoluto (nunca abaixo disso)",
        )
        self.w_floor.valueChanged.connect(
            lambda v: self._set("BRIGHTNESS_FLOOR", v)
        )
        ll.addWidget(self.w_floor)

        self.w_base = LabeledSlider(
            "Base (Normal)", 0.1, 1.0, 0.05, self.cfg.get("BRIGHTNESS_BASE"),
            description="Brilho padrão durante a música",
        )
        self.w_base.valueChanged.connect(
            lambda v: self._set("BRIGHTNESS_BASE", v)
        )
        ll.addWidget(self.w_base)

        ll.addWidget(Separator())

        self.w_kick = LabeledSlider(
            "Kick", 0.3, 1.0, 0.05, self.cfg.get("BRIGHTNESS_KICK"),
            description="Brilho no hit de kick/bumbo",
        )
        self.w_kick.valueChanged.connect(
            lambda v: self._set("BRIGHTNESS_KICK", v)
        )
        ll.addWidget(self.w_kick)

        self.w_snare = LabeledSlider(
            "Snare", 0.3, 1.0, 0.05, self.cfg.get("BRIGHTNESS_SNARE"),
            description="Brilho no hit de snare/caixa",
        )
        self.w_snare.valueChanged.connect(
            lambda v: self._set("BRIGHTNESS_SNARE", v)
        )
        ll.addWidget(self.w_snare)

        self.w_peak = LabeledSlider(
            "Peak", 0.3, 1.0, 0.05, self.cfg.get("BRIGHTNESS_PEAK"),
            description="Brilho em picos de energia",
        )
        self.w_peak.valueChanged.connect(
            lambda v: self._set("BRIGHTNESS_PEAK", v)
        )
        ll.addWidget(self.w_peak)

        layout.addWidget(grp_levels)

        # ── Color Shift on Events ──
        grp_shift = QGroupBox("Color Shift em Eventos")
        sl = QVBoxLayout(grp_shift)

        self.w_shift_kick = LabeledSlider(
            "Shift no Kick", 0.0, 0.5, 0.01, self.cfg.get("COLOR_SHIFT_KICK"),
            description="Quanto a cor muda no kick",
        )
        self.w_shift_kick.valueChanged.connect(
            lambda v: self._set("COLOR_SHIFT_KICK", v)
        )
        sl.addWidget(self.w_shift_kick)

        self.w_shift_snare = LabeledSlider(
            "Shift no Snare", 0.0, 0.5, 0.01, self.cfg.get("COLOR_SHIFT_SNARE"),
        )
        self.w_shift_snare.valueChanged.connect(
            lambda v: self._set("COLOR_SHIFT_SNARE", v)
        )
        sl.addWidget(self.w_shift_snare)

        self.w_shift_peak = LabeledSlider(
            "Shift no Peak", 0.0, 0.5, 0.01, self.cfg.get("COLOR_SHIFT_PEAK"),
        )
        self.w_shift_peak.valueChanged.connect(
            lambda v: self._set("COLOR_SHIFT_PEAK", v)
        )
        sl.addWidget(self.w_shift_peak)

        layout.addWidget(grp_shift)

        layout.addStretch()
        self.setWidget(container)

    def _set(self, key, val):
        self.cfg.set(key, val)
        self.cfg.apply_to_config_module()

    def reload_values(self):
        self.w_brightness_map.set_map(self.cfg.get("BRIGHTNESS_MAP"))
        self.w_floor.setValue(self.cfg.get("BRIGHTNESS_FLOOR"))
        self.w_base.setValue(self.cfg.get("BRIGHTNESS_BASE"))
        self.w_kick.setValue(self.cfg.get("BRIGHTNESS_KICK"))
        self.w_snare.setValue(self.cfg.get("BRIGHTNESS_SNARE"))
        self.w_peak.setValue(self.cfg.get("BRIGHTNESS_PEAK"))
        self.w_shift_kick.setValue(self.cfg.get("COLOR_SHIFT_KICK"))
        self.w_shift_snare.setValue(self.cfg.get("COLOR_SHIFT_SNARE"))
        self.w_shift_peak.setValue(self.cfg.get("COLOR_SHIFT_PEAK"))