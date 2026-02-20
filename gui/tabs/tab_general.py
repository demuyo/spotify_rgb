# gui/tabs/tab_general.py
"""Aba de configurações gerais."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QScrollArea,
)
from PyQt6.QtCore import Qt

from gui.widgets import (
    LabeledCombo, LabeledCheck, ColorPickerButton, Separator,
)
from config_manager import ConfigManager


class TabGeneral(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # ── Visual Effect ──
        grp_visual = QGroupBox("Efeito Visual")
        vl = QVBoxLayout(grp_visual)

        self.w_effect = LabeledCombo(
            "Efeito Ativo",
            ["bands", "chase", "frequency", "hybrid"],
            self.cfg.get("VISUAL_EFFECT"),
            "Define como os LEDs reagem à música",
        )
        self.w_effect.currentTextChanged.connect(
            lambda v: self._set("VISUAL_EFFECT", v)
        )
        vl.addWidget(self.w_effect)

        self.w_detection = LabeledCombo(
            "Modo de Detecção",
            ["both", "onset", "peaks", "none"],
            self.cfg.get("DETECTION_MODE"),
            "Como detectar batidas: onset (aubio), peaks (FFT), ambos",
        )
        self.w_detection.currentTextChanged.connect(
            lambda v: self._set("DETECTION_MODE", v)
        )
        vl.addWidget(self.w_detection)

        layout.addWidget(grp_visual)

        # ── Reactive Mode ──
        grp_reactive = QGroupBox("Modo Reativo")
        rl = QVBoxLayout(grp_reactive)

        self.w_reactive = LabeledCheck(
            "Modo Reativo Ativo",
            self.cfg.get("REACTIVE_MODE"),
            "Quando desligado, usa cor estática",
        )
        self.w_reactive.toggled.connect(
            lambda v: self._set("REACTIVE_MODE", v)
        )
        rl.addWidget(self.w_reactive)

        self.w_led_mode = LabeledCombo(
            "Modo LED (Não-Reativo)",
            ["breathing", "static", "pulse"],
            self.cfg.get("LED_MODE"),
            "Modo dos LEDs quando reativo está desligado",
        )
        self.w_led_mode.currentTextChanged.connect(
            lambda v: self._set("LED_MODE", v)
        )
        rl.addWidget(self.w_led_mode)

        self.w_hit_style = LabeledCombo(
            "Estilo de Hit",
            ["both", "brightness", "color", "none"],
            self.cfg.get("HIT_STYLE"),
            "Como os hits (kick/snare) afetam os LEDs",
        )
        self.w_hit_style.currentTextChanged.connect(
            lambda v: self._set("HIT_STYLE", v)
        )
        rl.addWidget(self.w_hit_style)

        layout.addWidget(grp_reactive)

        # ── Default Color ──
        grp_color = QGroupBox("Cor Padrão")
        cl = QVBoxLayout(grp_color)

        self.w_default_color = ColorPickerButton(
            "Cor Padrão (Fallback)", self.cfg.get("DEFAULT_COLOR")
        )
        self.w_default_color.colorChanged.connect(
            lambda v: self._set("DEFAULT_COLOR", v)
        )
        cl.addWidget(self.w_default_color)

        layout.addWidget(grp_color)

        layout.addStretch()
        self.setWidget(container)

    def _set(self, key, val):
        self.cfg.set(key, val)
        self.cfg.apply_to_config_module()

    def reload_values(self):
        self.w_effect.setCurrentText(self.cfg.get("VISUAL_EFFECT"))
        self.w_detection.setCurrentText(self.cfg.get("DETECTION_MODE"))
        self.w_reactive.setChecked(self.cfg.get("REACTIVE_MODE"))
        self.w_led_mode.setCurrentText(self.cfg.get("LED_MODE"))
        self.w_hit_style.setCurrentText(self.cfg.get("HIT_STYLE"))
        self.w_default_color.setColor(self.cfg.get("DEFAULT_COLOR"))