# gui/tabs/tab_colors.py
"""Aba de configuração de cores (estratégia, atribuição, hue shifts, saturação)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QScrollArea, QLabel,
)
from PyQt6.QtCore import Qt

from gui.widgets import LabeledSlider, LabeledCombo, Separator
from config_manager import ConfigManager


class TabColors(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # ══════════════════════════════════════════
        # ESTRATÉGIA DE CORES (NOVO — no topo!)
        # ══════════════════════════════════════════
        grp_strategy = QGroupBox("🎨 Estratégia de Cores do Álbum")
        stl = QVBoxLayout(grp_strategy)

        desc_strat = QLabel(
            "Controla como as cores são extraídas da capa e distribuídas entre as bandas.\n"
            "Só se aplica quando o esquema de cores é 'album_colors'."
        )
        desc_strat.setStyleSheet("color: #888; font-size: 11px;")
        desc_strat.setWordWrap(True)
        stl.addWidget(desc_strat)

        # ── Seleção ──
        self.w_selection_strategy = LabeledCombo(
            "Seleção de Cores",
            ["vibrant", "contrast", "max_saturation", "adaptive", "balanced"],
            self.cfg.get("COLOR_SELECTION_STRATEGY", "vibrant"),
            "vibrant = cores vivas  |  contrast = máxima diferença  |  "
            "max_saturation = só as mais saturadas  |  adaptive = automático  |  "
            "balanced = comportamento antigo",
        )
        self.w_selection_strategy.currentTextChanged.connect(
            lambda v: self._set_color("COLOR_SELECTION_STRATEGY", v)
        )
        stl.addWidget(self.w_selection_strategy)

        # ── Atribuição ──
        self.w_assignment_mode = LabeledCombo(
            "Atribuição às Bandas",
            ["vibrant_bass", "even", "inverted", "luminance"],
            self.cfg.get("COLOR_ASSIGNMENT_MODE", "vibrant_bass"),
            "vibrant_bass = baixo recebe cor mais vibrante  |  "
            "even = brilho equalizado  |  inverted = baixo claro, percussão escura  |  "
            "luminance = comportamento antigo (escura→baixo)",
        )
        self.w_assignment_mode.currentTextChanged.connect(
            lambda v: self._set_color("COLOR_ASSIGNMENT_MODE", v)
        )
        stl.addWidget(self.w_assignment_mode)

        # ── Saturação Mínima ──
        self.w_min_saturation = LabeledSlider(
            "Saturação Mínima", 0.0, 0.80, 0.05,
            self.cfg.get("COLOR_MIN_SATURATION", 0.45),
            description="Piso de saturação pra LEDs. 0 = sem piso (original). "
                        "Valores altos = cores sempre vibrantes.",
        )
        self.w_min_saturation.valueChanged.connect(
            lambda v: self._set_color("COLOR_MIN_SATURATION", v)
        )
        stl.addWidget(self.w_min_saturation)

        layout.addWidget(grp_strategy)

        # ══════════════════════════════════════════
        # HUE SHIFT POR BANDA (existente)
        # ══════════════════════════════════════════
        grp_hue = QGroupBox("Ajuste de Matiz (Hue Shift)")
        hl = QVBoxLayout(grp_hue)

        desc = QLabel(
            "Desloca a matiz da cor de cada banda em relação à cor extraída do álbum.\n"
            "Valores positivos → mais quente | Negativos → mais frio\n"
            "⚠ Só funciona no esquema 'custom' (aba Bandas)."
        )
        desc.setStyleSheet("color: #666; font-size: 11px;")
        desc.setWordWrap(True)
        hl.addWidget(desc)

        self.w_hue_perc = LabeledSlider(
            "🥁 Percussão", -0.5, 0.5, 0.01, self.cfg.get("BAND_HUE_PERCUSSION"),
        )
        self.w_hue_perc.valueChanged.connect(
            lambda v: self._set("BAND_HUE_PERCUSSION", v)
        )
        hl.addWidget(self.w_hue_perc)

        self.w_hue_bass = LabeledSlider(
            "🎸 Baixo", -0.5, 0.5, 0.01, self.cfg.get("BAND_HUE_BASS"),
        )
        self.w_hue_bass.valueChanged.connect(
            lambda v: self._set("BAND_HUE_BASS", v)
        )
        hl.addWidget(self.w_hue_bass)

        self.w_hue_melody = LabeledSlider(
            "🎹 Melodia", -0.5, 0.5, 0.01, self.cfg.get("BAND_HUE_MELODY"),
        )
        self.w_hue_melody.valueChanged.connect(
            lambda v: self._set("BAND_HUE_MELODY", v)
        )
        hl.addWidget(self.w_hue_melody)

        layout.addWidget(grp_hue)

        # ══════════════════════════════════════════
        # SATURAÇÃO POR BANDA (existente)
        # ══════════════════════════════════════════
        grp_sat = QGroupBox("Saturação por Banda")
        sl = QVBoxLayout(grp_sat)

        desc_sat = QLabel(
            "Multiplicador de saturação por banda.\n"
            "⚠ Só funciona no esquema 'custom' (aba Bandas)."
        )
        desc_sat.setStyleSheet("color: #666; font-size: 11px;")
        desc_sat.setWordWrap(True)
        sl.addWidget(desc_sat)

        self.w_sat_perc = LabeledSlider(
            "🥁 Percussão", 0.0, 2.0, 0.05, self.cfg.get("BAND_SAT_PERCUSSION"),
        )
        self.w_sat_perc.valueChanged.connect(
            lambda v: self._set("BAND_SAT_PERCUSSION", v)
        )
        sl.addWidget(self.w_sat_perc)

        self.w_sat_bass = LabeledSlider(
            "🎸 Baixo", 0.0, 2.0, 0.05, self.cfg.get("BAND_SAT_BASS"),
        )
        self.w_sat_bass.valueChanged.connect(
            lambda v: self._set("BAND_SAT_BASS", v)
        )
        sl.addWidget(self.w_sat_bass)

        self.w_sat_melody = LabeledSlider(
            "🎹 Melodia", 0.0, 2.0, 0.05, self.cfg.get("BAND_SAT_MELODY"),
        )
        self.w_sat_melody.valueChanged.connect(
            lambda v: self._set("BAND_SAT_MELODY", v)
        )
        sl.addWidget(self.w_sat_melody)

        layout.addWidget(grp_sat)

        # ══════════════════════════════════════════
        # VISUAL DAS BANDAS (existente)
        # ══════════════════════════════════════════
        grp_visual = QGroupBox("Visual das Bandas")
        vl = QVBoxLayout(grp_visual)

        self.w_gradient = LabeledSlider(
            "Gradiente Interno", 0.0, 0.5, 0.01,
            self.cfg.get("BAND_INTERNAL_GRADIENT"),
            description="Gradiente de brilho dentro de cada zona",
        )
        self.w_gradient.valueChanged.connect(
            lambda v: self._set("BAND_INTERNAL_GRADIENT", v)
        )
        vl.addWidget(self.w_gradient)

        self.w_color_lerp = LabeledSlider(
            "Color Lerp", 0.0, 1.0, 0.05, self.cfg.get("BAND_COLOR_LERP"),
            description="Suavização da transição de cor entre frames",
        )
        self.w_color_lerp.valueChanged.connect(
            lambda v: self._set("BAND_COLOR_LERP", v)
        )
        vl.addWidget(self.w_color_lerp)

        self.w_blend_width = LabeledSlider(
            "Blend entre Zonas", 0.0, 5.0, 1.0,
            self.cfg.get("BAND_ZONE_BLEND_WIDTH"),
            description="Quantos LEDs de transição entre zonas",
        )
        self.w_blend_width.valueChanged.connect(
            lambda v: self._set("BAND_ZONE_BLEND_WIDTH", int(v))
        )
        vl.addWidget(self.w_blend_width)

        self.w_beat_color_shift = LabeledSlider(
            "Beat Color Shift", 0.0, 0.5, 0.01,
            self.cfg.get("BAND_BEAT_COLOR_SHIFT"),
            description="Quanto a cor muda durante o beat",
        )
        self.w_beat_color_shift.valueChanged.connect(
            lambda v: self._set("BAND_BEAT_COLOR_SHIFT", v)
        )
        vl.addWidget(self.w_beat_color_shift)

        self.w_response_curve = LabeledCombo(
            "Curva de Resposta",
            ["linear", "sqrt", "square", "log"],
            self.cfg.get("BAND_RESPONSE_CURVE"),
            "Curva aplicada à intensidade antes do mapeamento",
        )
        self.w_response_curve.currentTextChanged.connect(
            lambda v: self._set("BAND_RESPONSE_CURVE", v)
        )
        vl.addWidget(self.w_response_curve)

        layout.addWidget(grp_visual)

        layout.addStretch()
        self.setWidget(container)

    # ──────────────────────────────────────────────
    # SETTERS
    # ──────────────────────────────────────────────

    def _set(self, key, val):
        """Set normal (sem limpar cache)."""
        self.cfg.set(key, val)
        self.cfg.apply_to_config_module()

    def _set_color(self, key, val):
        """Set de config de cor — limpa cache pra reaplicar na próxima música."""
        self.cfg.set(key, val)
        self.cfg.apply_to_config_module()
        try:
            from color_module import clear_cache
            clear_cache()
        except Exception:
            pass

    # ──────────────────────────────────────────────
    # RELOAD
    # ──────────────────────────────────────────────

    def reload_values(self):
        # Novos
        self.w_selection_strategy.setCurrentText(
            self.cfg.get("COLOR_SELECTION_STRATEGY", "vibrant")
        )
        self.w_assignment_mode.setCurrentText(
            self.cfg.get("COLOR_ASSIGNMENT_MODE", "vibrant_bass")
        )
        self.w_min_saturation.setValue(
            self.cfg.get("COLOR_MIN_SATURATION", 0.45)
        )
        # Existentes
        self.w_hue_perc.setValue(self.cfg.get("BAND_HUE_PERCUSSION"))
        self.w_hue_bass.setValue(self.cfg.get("BAND_HUE_BASS"))
        self.w_hue_melody.setValue(self.cfg.get("BAND_HUE_MELODY"))
        self.w_sat_perc.setValue(self.cfg.get("BAND_SAT_PERCUSSION"))
        self.w_sat_bass.setValue(self.cfg.get("BAND_SAT_BASS"))
        self.w_sat_melody.setValue(self.cfg.get("BAND_SAT_MELODY"))
        self.w_gradient.setValue(self.cfg.get("BAND_INTERNAL_GRADIENT"))
        self.w_color_lerp.setValue(self.cfg.get("BAND_COLOR_LERP"))
        self.w_blend_width.setValue(self.cfg.get("BAND_ZONE_BLEND_WIDTH"))
        self.w_beat_color_shift.setValue(self.cfg.get("BAND_BEAT_COLOR_SHIFT"))
        self.w_response_curve.setCurrentText(self.cfg.get("BAND_RESPONSE_CURVE"))