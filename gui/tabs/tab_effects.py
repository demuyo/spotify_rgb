# gui/tabs/tab_effects.py
"""Aba de configuração dos efeitos visuais (chase, frequency, hybrid)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QScrollArea,
)
from PyQt6.QtCore import Qt

from gui.widgets import (
    LabeledSlider, LabeledIntSlider, LabeledCombo, LabeledCheck, Separator,
)
from config_manager import ConfigManager


class TabEffects(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # ── Chase Effect ──
        grp_chase = QGroupBox("🏃 Chase Effect")
        cl = QVBoxLayout(grp_chase)

        self.w_chase_enabled = LabeledCheck(
            "Chase Ativo", self.cfg.get("CHASE_ENABLED"),
            "LED 'correndo' pela fita",
        )
        self.w_chase_enabled.toggled.connect(
            lambda v: self._set("CHASE_ENABLED", v)
        )
        cl.addWidget(self.w_chase_enabled)

        self.w_chase_speed = LabeledSlider(
            "Velocidade Máx", 0.1, 2.0, 0.1, self.cfg.get("CHASE_SPEED_MAX"),
        )
        self.w_chase_speed.valueChanged.connect(
            lambda v: self._set("CHASE_SPEED_MAX", v)
        )
        cl.addWidget(self.w_chase_speed)

        self.w_chase_tail = LabeledIntSlider(
            "Tamanho da Cauda", 1, 20, self.cfg.get("CHASE_TAIL_LENGTH"), " LEDs",
        )
        self.w_chase_tail.valueChanged.connect(
            lambda v: self._set("CHASE_TAIL_LENGTH", v)
        )
        cl.addWidget(self.w_chase_tail)

        self.w_chase_bmin = LabeledSlider(
            "Brilho Mín", 0.0, 0.5, 0.01, self.cfg.get("CHASE_BRIGHTNESS_MIN"),
        )
        self.w_chase_bmin.valueChanged.connect(
            lambda v: self._set("CHASE_BRIGHTNESS_MIN", v)
        )
        cl.addWidget(self.w_chase_bmin)

        self.w_chase_bmax = LabeledSlider(
            "Brilho Máx", 0.1, 1.0, 0.05, self.cfg.get("CHASE_BRIGHTNESS_MAX"),
        )
        self.w_chase_bmax.valueChanged.connect(
            lambda v: self._set("CHASE_BRIGHTNESS_MAX", v)
        )
        cl.addWidget(self.w_chase_bmax)

        self.w_chase_flash = LabeledSlider(
            "Beat Flash", 0.0, 1.0, 0.05, self.cfg.get("CHASE_BEAT_FLASH"),
        )
        self.w_chase_flash.valueChanged.connect(
            lambda v: self._set("CHASE_BEAT_FLASH", v)
        )
        cl.addWidget(self.w_chase_flash)

        self.w_chase_bg = LabeledSlider(
            "Brilho Background", 0.0, 0.5, 0.01, self.cfg.get("CHASE_BG_BRIGHTNESS"),
        )
        self.w_chase_bg.valueChanged.connect(
            lambda v: self._set("CHASE_BG_BRIGHTNESS", v)
        )
        cl.addWidget(self.w_chase_bg)

        layout.addWidget(grp_chase)

        # ── Frequency Effect ──
        grp_freq = QGroupBox("📊 Frequency Effect")
        fl = QVBoxLayout(grp_freq)

        self.w_freq_attack = LabeledSlider(
            "Smoothing Attack", 0.05, 1.0, 0.01, self.cfg.get("FREQ_SMOOTHING_ATTACK"),
        )
        self.w_freq_attack.valueChanged.connect(
            lambda v: self._set("FREQ_SMOOTHING_ATTACK", v)
        )
        fl.addWidget(self.w_freq_attack)

        self.w_freq_decay = LabeledSlider(
            "Smoothing Decay", 0.01, 0.5, 0.01, self.cfg.get("FREQ_SMOOTHING_DECAY"),
        )
        self.w_freq_decay.valueChanged.connect(
            lambda v: self._set("FREQ_SMOOTHING_DECAY", v)
        )
        fl.addWidget(self.w_freq_decay)

        self.w_freq_beat = LabeledSlider(
            "Beat Amount", 0.0, 1.0, 0.05, self.cfg.get("FREQ_BEAT_AMOUNT"),
        )
        self.w_freq_beat.valueChanged.connect(
            lambda v: self._set("FREQ_BEAT_AMOUNT", v)
        )
        fl.addWidget(self.w_freq_beat)

        self.w_freq_bass_mult = LabeledSlider(
            "Bass Multiplier", 0.1, 2.0, 0.05, self.cfg.get("FREQ_BASS_MULT"),
        )
        self.w_freq_bass_mult.valueChanged.connect(
            lambda v: self._set("FREQ_BASS_MULT", v)
        )
        fl.addWidget(self.w_freq_bass_mult)

        self.w_freq_bg = LabeledSlider(
            "Brilho Background", 0.0, 0.5, 0.01, self.cfg.get("FREQ_BG_BRIGHTNESS"),
        )
        self.w_freq_bg.valueChanged.connect(
            lambda v: self._set("FREQ_BG_BRIGHTNESS", v)
        )
        fl.addWidget(self.w_freq_bg)

        layout.addWidget(grp_freq)

        # ── Hybrid Effect ──
        grp_hybrid = QGroupBox("🔀 Hybrid Effect")
        hl = QVBoxLayout(grp_hybrid)

        self.w_hybrid_intensity = LabeledSlider(
            "Chase Intensity", 0.0, 1.0, 0.05, self.cfg.get("HYBRID_CHASE_INTENSITY"),
        )
        self.w_hybrid_intensity.valueChanged.connect(
            lambda v: self._set("HYBRID_CHASE_INTENSITY", v)
        )
        hl.addWidget(self.w_hybrid_intensity)

        self.w_hybrid_speed = LabeledSlider(
            "Chase Speed", 0.1, 2.0, 0.1, self.cfg.get("HYBRID_CHASE_SPEED"),
        )
        self.w_hybrid_speed.valueChanged.connect(
            lambda v: self._set("HYBRID_CHASE_SPEED", v)
        )
        hl.addWidget(self.w_hybrid_speed)

        self.w_hybrid_tail = LabeledIntSlider(
            "Chase Tail", 1, 20, self.cfg.get("HYBRID_CHASE_TAIL"), " LEDs",
        )
        self.w_hybrid_tail.valueChanged.connect(
            lambda v: self._set("HYBRID_CHASE_TAIL", v)
        )
        hl.addWidget(self.w_hybrid_tail)

        self.w_hybrid_mode = LabeledCombo(
            "Chase Mode",
            ["blend", "add", "overlay"],
            self.cfg.get("HYBRID_CHASE_MODE"),
        )
        self.w_hybrid_mode.currentTextChanged.connect(
            lambda v: self._set("HYBRID_CHASE_MODE", v)
        )
        hl.addWidget(self.w_hybrid_mode)

        layout.addWidget(grp_hybrid)

        layout.addStretch()
        self.setWidget(container)

    def _set(self, key, val):
        self.cfg.set(key, val)
        self.cfg.apply_to_config_module()

    def reload_values(self):
        self.w_chase_enabled.setChecked(self.cfg.get("CHASE_ENABLED"))
        self.w_chase_speed.setValue(self.cfg.get("CHASE_SPEED_MAX"))
        self.w_chase_tail.setValue(self.cfg.get("CHASE_TAIL_LENGTH"))
        self.w_chase_bmin.setValue(self.cfg.get("CHASE_BRIGHTNESS_MIN"))
        self.w_chase_bmax.setValue(self.cfg.get("CHASE_BRIGHTNESS_MAX"))
        self.w_chase_flash.setValue(self.cfg.get("CHASE_BEAT_FLASH"))
        self.w_chase_bg.setValue(self.cfg.get("CHASE_BG_BRIGHTNESS"))
        self.w_freq_attack.setValue(self.cfg.get("FREQ_SMOOTHING_ATTACK"))
        self.w_freq_decay.setValue(self.cfg.get("FREQ_SMOOTHING_DECAY"))
        self.w_freq_beat.setValue(self.cfg.get("FREQ_BEAT_AMOUNT"))
        self.w_freq_bass_mult.setValue(self.cfg.get("FREQ_BASS_MULT"))
        self.w_freq_bg.setValue(self.cfg.get("FREQ_BG_BRIGHTNESS"))
        self.w_hybrid_intensity.setValue(self.cfg.get("HYBRID_CHASE_INTENSITY"))
        self.w_hybrid_speed.setValue(self.cfg.get("HYBRID_CHASE_SPEED"))
        self.w_hybrid_tail.setValue(self.cfg.get("HYBRID_CHASE_TAIL"))
        self.w_hybrid_mode.setCurrentText(self.cfg.get("HYBRID_CHASE_MODE"))