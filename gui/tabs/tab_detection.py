# gui/tabs/tab_detection.py
"""Aba de configuração de detecção de batidas."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QScrollArea,
)
from PyQt6.QtCore import Qt

from gui.widgets import LabeledSlider, LabeledCombo, Separator
from config_manager import ConfigManager


class TabDetection(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # ── Sensitivity Presets ──
        grp_preset = QGroupBox("Presets de Sensibilidade")
        pl = QVBoxLayout(grp_preset)

        self.w_sensitivity = LabeledCombo(
            "Sensibilidade Onset (Aubio)",
            ["low", "medium", "high", "custom"],
            self.cfg.get("SENSITIVITY"),
            "Presets para detecção de kick/snare",
        )
        self.w_sensitivity.currentTextChanged.connect(
            lambda v: self._set("SENSITIVITY", v)
        )
        pl.addWidget(self.w_sensitivity)

        self.w_peaks_sens = LabeledCombo(
            "Sensibilidade Peaks (FFT)",
            ["low", "medium", "high", "custom"],
            self.cfg.get("PEAKS_SENSITIVITY"),
        )
        self.w_peaks_sens.currentTextChanged.connect(
            lambda v: self._set("PEAKS_SENSITIVITY", v)
        )
        pl.addWidget(self.w_peaks_sens)

        layout.addWidget(grp_preset)

        # ── Custom Thresholds ──
        grp_custom = QGroupBox("Thresholds Customizados")
        cl = QVBoxLayout(grp_custom)

        self.w_kick_thresh = LabeledSlider(
            "Kick Threshold", 0.1, 1.0, 0.05, self.cfg.get("CUSTOM_KICK_THRESHOLD"),
            description="Limiar para detectar kick (menor = mais sensível)",
        )
        self.w_kick_thresh.valueChanged.connect(
            lambda v: self._set("CUSTOM_KICK_THRESHOLD", v)
        )
        cl.addWidget(self.w_kick_thresh)

        self.w_snare_thresh = LabeledSlider(
            "Snare Threshold", 0.1, 1.0, 0.05, self.cfg.get("CUSTOM_SNARE_THRESHOLD"),
        )
        self.w_snare_thresh.valueChanged.connect(
            lambda v: self._set("CUSTOM_SNARE_THRESHOLD", v)
        )
        cl.addWidget(self.w_snare_thresh)

        cl.addWidget(Separator())

        self.w_kick_energy = LabeledSlider(
            "Kick Min Energy", 0.001, 0.05, 0.001, self.cfg.get("CUSTOM_KICK_MIN_ENERGY"),
            description="Energia mínima para considerar um kick real",
        )
        self.w_kick_energy.valueChanged.connect(
            lambda v: self._set("CUSTOM_KICK_MIN_ENERGY", v)
        )
        cl.addWidget(self.w_kick_energy)

        self.w_snare_energy = LabeledSlider(
            "Snare Min Energy", 0.001, 0.05, 0.001, self.cfg.get("CUSTOM_SNARE_MIN_ENERGY"),
        )
        self.w_snare_energy.valueChanged.connect(
            lambda v: self._set("CUSTOM_SNARE_MIN_ENERGY", v)
        )
        cl.addWidget(self.w_snare_energy)

        cl.addWidget(Separator())

        self.w_kick_minioi = LabeledSlider(
            "Kick Min Interval", 0.01, 0.2, 0.01, self.cfg.get("CUSTOM_KICK_MINIOI"), "s",
            description="Tempo mínimo entre dois kicks (segundos)",
        )
        self.w_kick_minioi.valueChanged.connect(
            lambda v: self._set("CUSTOM_KICK_MINIOI", v)
        )
        cl.addWidget(self.w_kick_minioi)

        self.w_snare_minioi = LabeledSlider(
            "Snare Min Interval", 0.01, 0.2, 0.01, self.cfg.get("CUSTOM_SNARE_MINIOI"), "s",
        )
        self.w_snare_minioi.valueChanged.connect(
            lambda v: self._set("CUSTOM_SNARE_MINIOI", v)
        )
        cl.addWidget(self.w_snare_minioi)

        layout.addWidget(grp_custom)

        # ── Timing ──
        grp_timing = QGroupBox("Timing")
        tl = QVBoxLayout(grp_timing)

        self.w_peak_hold = LabeledSlider(
            "Peak Hold Time", 0.01, 0.5, 0.01, self.cfg.get("PEAK_HOLD_TIME"), "s",
            description="Quanto tempo o peak fica ativo",
        )
        self.w_peak_hold.valueChanged.connect(
            lambda v: self._set("PEAK_HOLD_TIME", v)
        )
        tl.addWidget(self.w_peak_hold)

        self.w_peak_interval = LabeledSlider(
            "Peak Min Interval", 0.01, 0.2, 0.01, self.cfg.get("PEAK_MIN_INTERVAL"), "s",
        )
        self.w_peak_interval.valueChanged.connect(
            lambda v: self._set("PEAK_MIN_INTERVAL", v)
        )
        tl.addWidget(self.w_peak_interval)

        self.w_hit_hold = LabeledSlider(
            "Hit Hold Time", 0.05, 0.5, 0.01, self.cfg.get("HIT_HOLD_TIME"), "s",
            description="Quanto tempo o hit (kick/snare) fica ativo",
        )
        self.w_hit_hold.valueChanged.connect(
            lambda v: self._set("HIT_HOLD_TIME", v)
        )
        tl.addWidget(self.w_hit_hold)

        layout.addWidget(grp_timing)

        layout.addStretch()
        self.setWidget(container)

    def _set(self, key, val):
        self.cfg.set(key, val)
        self.cfg.apply_to_config_module()

    def reload_values(self):
        self.w_sensitivity.setCurrentText(self.cfg.get("SENSITIVITY"))
        self.w_peaks_sens.setCurrentText(self.cfg.get("PEAKS_SENSITIVITY"))
        self.w_kick_thresh.setValue(self.cfg.get("CUSTOM_KICK_THRESHOLD"))
        self.w_snare_thresh.setValue(self.cfg.get("CUSTOM_SNARE_THRESHOLD"))
        self.w_kick_energy.setValue(self.cfg.get("CUSTOM_KICK_MIN_ENERGY"))
        self.w_snare_energy.setValue(self.cfg.get("CUSTOM_SNARE_MIN_ENERGY"))
        self.w_kick_minioi.setValue(self.cfg.get("CUSTOM_KICK_MINIOI"))
        self.w_snare_minioi.setValue(self.cfg.get("CUSTOM_SNARE_MINIOI"))
        self.w_peak_hold.setValue(self.cfg.get("PEAK_HOLD_TIME"))
        self.w_peak_interval.setValue(self.cfg.get("PEAK_MIN_INTERVAL"))
        self.w_hit_hold.setValue(self.cfg.get("HIT_HOLD_TIME"))