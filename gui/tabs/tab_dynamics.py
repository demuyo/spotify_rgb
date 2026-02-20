# gui/tabs/tab_dynamics.py
"""
Aba de configuração de dinâmica (AGC, Compressor, Smoothing).
Controla o comportamento em volume baixo.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QScrollArea, QLabel,
    QHBoxLayout, QPushButton,
)
from PyQt6.QtCore import Qt

from gui.widgets import LabeledSlider, LabeledCombo, LabeledToggle
from config_manager import ConfigManager


class TabDynamics(QScrollArea):
    """Aba de controle de dinâmica de áudio."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # ══════════════════════════════════════════════════
        # HEADER
        # ══════════════════════════════════════════════════
        header = QLabel(
            "🎚️ <b>Controle de Dinâmica</b><br>"
            "<span style='color: #888; font-size: 11px;'>"
            "Ajusta comportamento em volume baixo. "
            "Evita LEDs piscando violentamente."
            "</span>"
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        # ══════════════════════════════════════════════════
        # AGC (Automatic Gain Control)
        # ══════════════════════════════════════════════════
        grp_agc = QGroupBox("🎚️ AGC (Controle Automático de Ganho)")
        agc_layout = QVBoxLayout(grp_agc)

        desc_agc = QLabel(
            "Aumenta ganho quando volume está baixo, "
            "mantendo energia visual consistente."
        )
        desc_agc.setStyleSheet("color: #666; font-size: 11px;")
        desc_agc.setWordWrap(True)
        agc_layout.addWidget(desc_agc)

        # Toggle
        self.w_agc_enabled = LabeledToggle(
            "AGC Habilitado",
            self.cfg.get("AGC_ENABLED", True),
        )
        self.w_agc_enabled.toggled.connect(
            lambda v: self._set("AGC_ENABLED", v)
        )
        agc_layout.addWidget(self.w_agc_enabled)

        # Max Gain
        self.w_agc_max = LabeledSlider(
            "Ganho Máximo", 1.0, 6.0, 0.5,
            self.cfg.get("AGC_MAX_GAIN", 3.5),
            description="Quanto amplifica em volume muito baixo (1.0 = sem boost)",
        )
        self.w_agc_max.valueChanged.connect(
            lambda v: self._set("AGC_MAX_GAIN", v)
        )
        agc_layout.addWidget(self.w_agc_max)

        # Min Gain
        self.w_agc_min = LabeledSlider(
            "Ganho Mínimo", 0.3, 1.0, 0.1,
            self.cfg.get("AGC_MIN_GAIN", 0.8),
            description="Quanto reduz em volume muito alto (evita saturar)",
        )
        self.w_agc_min.valueChanged.connect(
            lambda v: self._set("AGC_MIN_GAIN", v)
        )
        agc_layout.addWidget(self.w_agc_min)

        # Target
        self.w_agc_target = LabeledSlider(
            "Volume Alvo", 0.1, 0.6, 0.05,
            self.cfg.get("AGC_TARGET", 0.35),
            description="AGC tenta manter a energia média nesse nível",
        )
        self.w_agc_target.valueChanged.connect(
            lambda v: self._set("AGC_TARGET", v)
        )
        agc_layout.addWidget(self.w_agc_target)

        # Attack/Release
        self.w_agc_attack = LabeledSlider(
            "Velocidade (Volume Subindo)", 0.01, 0.15, 0.01,
            self.cfg.get("AGC_ATTACK", 0.03),
            description="Mais alto = reage mais rápido quando volume sobe",
        )
        self.w_agc_attack.valueChanged.connect(
            lambda v: self._set("AGC_ATTACK", v)
        )
        agc_layout.addWidget(self.w_agc_attack)

        self.w_agc_release = LabeledSlider(
            "Velocidade (Volume Caindo)", 0.005, 0.05, 0.005,
            self.cfg.get("AGC_RELEASE", 0.01),
            description="Mais baixo = demora mais pra aumentar ganho",
        )
        self.w_agc_release.valueChanged.connect(
            lambda v: self._set("AGC_RELEASE", v)
        )
        agc_layout.addWidget(self.w_agc_release)

        layout.addWidget(grp_agc)

        # ══════════════════════════════════════════════════
        # COMPRESSOR
        # ══════════════════════════════════════════════════
        grp_comp = QGroupBox("📊 Compressor de Dinâmica")
        comp_layout = QVBoxLayout(grp_comp)

        desc_comp = QLabel(
            "Reduz diferença entre sons baixos e altos. "
            "Evita que batidas pulem de 0 pra 100."
        )
        desc_comp.setStyleSheet("color: #666; font-size: 11px;")
        desc_comp.setWordWrap(True)
        comp_layout.addWidget(desc_comp)

        # Toggle (usa BAND_COMPRESSION_ENABLED que já existe)
        self.w_comp_enabled = LabeledToggle(
            "Compressor Habilitado",
            self.cfg.get("BAND_COMPRESSION_ENABLED", True),
        )
        self.w_comp_enabled.toggled.connect(
            lambda v: self._set("BAND_COMPRESSION_ENABLED", v)
        )
        comp_layout.addWidget(self.w_comp_enabled)

        # Threshold
        self.w_comp_thresh = LabeledSlider(
            "Threshold", 0.1, 0.6, 0.05,
            self.cfg.get("COMPRESSOR_THRESHOLD", 0.25),
            description="Acima desse valor, começa a comprimir",
        )
        self.w_comp_thresh.valueChanged.connect(
            lambda v: self._set("COMPRESSOR_THRESHOLD", v)
        )
        comp_layout.addWidget(self.w_comp_thresh)

        # Ratio
        self.w_comp_ratio = LabeledSlider(
            "Ratio", 1.5, 6.0, 0.5,
            self.cfg.get("COMPRESSOR_RATIO", 2.5),
            description="Quanto comprime (2.0 = 2:1, 4.0 = 4:1)",
        )
        self.w_comp_ratio.valueChanged.connect(
            lambda v: self._set("COMPRESSOR_RATIO", v)
        )
        comp_layout.addWidget(self.w_comp_ratio)

        # Knee
        self.w_comp_knee = LabeledSlider(
            "Knee (Suavidade)", 0.0, 0.4, 0.05,
            self.cfg.get("COMPRESSOR_KNEE", 0.15),
            description="0 = transição dura, 0.3+ = transição suave",
        )
        self.w_comp_knee.valueChanged.connect(
            lambda v: self._set("COMPRESSOR_KNEE", v)
        )
        comp_layout.addWidget(self.w_comp_knee)

        # Makeup
        self.w_comp_makeup = LabeledSlider(
            "Makeup Gain", 1.0, 2.0, 0.1,
            self.cfg.get("COMPRESSOR_MAKEUP", 1.4),
            description="Compensa a redução de volume (1.0 = sem compensação)",
        )
        self.w_comp_makeup.valueChanged.connect(
            lambda v: self._set("COMPRESSOR_MAKEUP", v)
        )
        comp_layout.addWidget(self.w_comp_makeup)

        layout.addWidget(grp_comp)

        # ══════════════════════════════════════════════════
        # SMOOTHING ADAPTATIVO
        # ══════════════════════════════════════════════════
        grp_smooth = QGroupBox("🌊 Smoothing Adaptativo")
        smooth_layout = QVBoxLayout(grp_smooth)

        desc_smooth = QLabel(
            "Em volume baixo, os LEDs demoram mais pra apagar. "
            "Evita piscadas violentas."
        )
        desc_smooth.setStyleSheet("color: #666; font-size: 11px;")
        desc_smooth.setWordWrap(True)
        smooth_layout.addWidget(desc_smooth)

        # Toggle
        self.w_smooth_enabled = LabeledToggle(
            "Smoothing Adaptativo",
            self.cfg.get("ADAPTIVE_SMOOTHING", True),
        )
        self.w_smooth_enabled.toggled.connect(
            lambda v: self._set("ADAPTIVE_SMOOTHING", v)
        )
        smooth_layout.addWidget(self.w_smooth_enabled)

        # Mult
        self.w_smooth_mult = LabeledSlider(
            "Multiplicador em Volume Baixo", 1.0, 5.0, 0.5,
            self.cfg.get("SMOOTHING_LOW_VOL_MULT", 2.5),
            description="Quanto mais lento fica o decay (2.0 = 2x mais lento)",
        )
        self.w_smooth_mult.valueChanged.connect(
            lambda v: self._set("SMOOTHING_LOW_VOL_MULT", v)
        )
        smooth_layout.addWidget(self.w_smooth_mult)

        # Threshold
        self.w_smooth_thresh = LabeledSlider(
            "Limiar de Volume Baixo", 0.1, 0.6, 0.05,
            self.cfg.get("SMOOTHING_LOW_VOL_THRESH", 0.35),
            description="Abaixo desse volume, o smoothing adaptativo ativa",
        )
        self.w_smooth_thresh.valueChanged.connect(
            lambda v: self._set("SMOOTHING_LOW_VOL_THRESH", v)
        )
        smooth_layout.addWidget(self.w_smooth_thresh)

        layout.addWidget(grp_smooth)

        # ══════════════════════════════════════════════════
        # FLOOR DINÂMICO
        # ══════════════════════════════════════════════════
        grp_floor = QGroupBox("💡 Floor Dinâmico")
        floor_layout = QVBoxLayout(grp_floor)

        desc_floor = QLabel(
            "Em volume baixo, os LEDs nunca apagam completamente. "
            "Mantém um brilho mínimo visível."
        )
        desc_floor.setStyleSheet("color: #666; font-size: 11px;")
        desc_floor.setWordWrap(True)
        floor_layout.addWidget(desc_floor)

        # Toggle
        self.w_floor_enabled = LabeledToggle(
            "Floor Dinâmico",
            self.cfg.get("DYNAMIC_FLOOR_ENABLED", True),
        )
        self.w_floor_enabled.toggled.connect(
            lambda v: self._set("DYNAMIC_FLOOR_ENABLED", v)
        )
        floor_layout.addWidget(self.w_floor_enabled)

        # Max Floor
        self.w_floor_max = LabeledSlider(
            "Floor Máximo", 0.05, 0.30, 0.01,
            self.cfg.get("DYNAMIC_FLOOR_MAX", 0.15),
            description="Brilho mínimo quando volume está muito baixo",
        )
        self.w_floor_max.valueChanged.connect(
            lambda v: self._set("DYNAMIC_FLOOR_MAX", v)
        )
        floor_layout.addWidget(self.w_floor_max)

        # Threshold
        self.w_floor_thresh = LabeledSlider(
            "Limiar de Ativação", 0.1, 0.5, 0.05,
            self.cfg.get("DYNAMIC_FLOOR_THRESH", 0.30),
            description="Abaixo desse volume, o floor começa a subir",
        )
        self.w_floor_thresh.valueChanged.connect(
            lambda v: self._set("DYNAMIC_FLOOR_THRESH", v)
        )
        floor_layout.addWidget(self.w_floor_thresh)

        layout.addWidget(grp_floor)

        # ══════════════════════════════════════════════════
        # PRESETS
        # ══════════════════════════════════════════════════
        grp_presets = QGroupBox("⚡ Presets Rápidos")
        presets_layout = QHBoxLayout(grp_presets)

        btn_aggressive = QPushButton("🔥 Agressivo")
        btn_aggressive.setToolTip("Pouca compressão, resposta rápida")
        btn_aggressive.clicked.connect(self._preset_aggressive)
        presets_layout.addWidget(btn_aggressive)

        btn_balanced = QPushButton("⚖️ Balanceado")
        btn_balanced.setToolTip("Configuração padrão, bom pra maioria")
        btn_balanced.clicked.connect(self._preset_balanced)
        presets_layout.addWidget(btn_balanced)

        btn_smooth = QPushButton("🌊 Suave")
        btn_smooth.setToolTip("Muita compressão, transições lentas")
        btn_smooth.clicked.connect(self._preset_smooth)
        presets_layout.addWidget(btn_smooth)

        btn_lowvol = QPushButton("🔈 Volume Baixo")
        btn_lowvol.setToolTip("Otimizado pra usar em volume ~20-40%")
        btn_lowvol.clicked.connect(self._preset_lowvol)
        presets_layout.addWidget(btn_lowvol)

        layout.addWidget(grp_presets)

        layout.addStretch()
        self.setWidget(container)

    # ──────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────

    def _set(self, key, val):
        """Salva config e aplica."""
        self.cfg.set(key, val)
        self.cfg.apply_to_config_module()

    def _apply_preset(self, values: dict):
        """Aplica um preset de valores."""
        for key, val in values.items():
            self.cfg.set(key, val)
        self.cfg.apply_to_config_module()
        self.reload_values()

    # ──────────────────────────────────────────────
    # PRESETS
    # ──────────────────────────────────────────────

    def _preset_aggressive(self):
        """Pouca compressão, resposta rápida."""
        self._apply_preset({
            "AGC_ENABLED": True,
            "AGC_MAX_GAIN": 2.0,
            "AGC_MIN_GAIN": 0.9,
            "AGC_TARGET": 0.40,
            "AGC_ATTACK": 0.08,
            "AGC_RELEASE": 0.02,
            "BAND_COMPRESSION_ENABLED": True,
            "COMPRESSOR_THRESHOLD": 0.50,
            "COMPRESSOR_RATIO": 1.5,
            "COMPRESSOR_KNEE": 0.05,
            "COMPRESSOR_MAKEUP": 1.1,
            "ADAPTIVE_SMOOTHING": False,
            "DYNAMIC_FLOOR_ENABLED": False,
        })

    def _preset_balanced(self):
        """Configuração padrão."""
        self._apply_preset({
            "AGC_ENABLED": True,
            "AGC_MAX_GAIN": 3.5,
            "AGC_MIN_GAIN": 0.8,
            "AGC_TARGET": 0.35,
            "AGC_ATTACK": 0.03,
            "AGC_RELEASE": 0.01,
            "BAND_COMPRESSION_ENABLED": True,
            "COMPRESSOR_THRESHOLD": 0.25,
            "COMPRESSOR_RATIO": 2.5,
            "COMPRESSOR_KNEE": 0.15,
            "COMPRESSOR_MAKEUP": 1.4,
            "ADAPTIVE_SMOOTHING": True,
            "SMOOTHING_LOW_VOL_MULT": 2.5,
            "SMOOTHING_LOW_VOL_THRESH": 0.35,
            "DYNAMIC_FLOOR_ENABLED": True,
            "DYNAMIC_FLOOR_MAX": 0.15,
            "DYNAMIC_FLOOR_THRESH": 0.30,
        })

    def _preset_smooth(self):
        """Muita compressão, transições suaves."""
        self._apply_preset({
            "AGC_ENABLED": True,
            "AGC_MAX_GAIN": 4.0,
            "AGC_MIN_GAIN": 0.7,
            "AGC_TARGET": 0.30,
            "AGC_ATTACK": 0.02,
            "AGC_RELEASE": 0.005,
            "BAND_COMPRESSION_ENABLED": True,
            "COMPRESSOR_THRESHOLD": 0.20,
            "COMPRESSOR_RATIO": 4.0,
            "COMPRESSOR_KNEE": 0.25,
            "COMPRESSOR_MAKEUP": 1.6,
            "ADAPTIVE_SMOOTHING": True,
            "SMOOTHING_LOW_VOL_MULT": 4.0,
            "SMOOTHING_LOW_VOL_THRESH": 0.45,
            "DYNAMIC_FLOOR_ENABLED": True,
            "DYNAMIC_FLOOR_MAX": 0.20,
            "DYNAMIC_FLOOR_THRESH": 0.40,
        })

    def _preset_lowvol(self):
        """Otimizado pra volume baixo (~20-40%)."""
        self._apply_preset({
            "AGC_ENABLED": True,
            "AGC_MAX_GAIN": 5.0,
            "AGC_MIN_GAIN": 0.6,
            "AGC_TARGET": 0.25,
            "AGC_ATTACK": 0.02,
            "AGC_RELEASE": 0.008,
            "BAND_COMPRESSION_ENABLED": True,
            "COMPRESSOR_THRESHOLD": 0.15,
            "COMPRESSOR_RATIO": 3.5,
            "COMPRESSOR_KNEE": 0.20,
            "COMPRESSOR_MAKEUP": 1.8,
            "ADAPTIVE_SMOOTHING": True,
            "SMOOTHING_LOW_VOL_MULT": 3.5,
            "SMOOTHING_LOW_VOL_THRESH": 0.50,
            "DYNAMIC_FLOOR_ENABLED": True,
            "DYNAMIC_FLOOR_MAX": 0.25,
            "DYNAMIC_FLOOR_THRESH": 0.45,
        })

    # ──────────────────────────────────────────────
    # RELOAD
    # ──────────────────────────────────────────────

    def reload_values(self):
        """Recarrega valores dos widgets."""
        # AGC
        self.w_agc_enabled.setChecked(self.cfg.get("AGC_ENABLED", True))
        self.w_agc_max.setValue(self.cfg.get("AGC_MAX_GAIN", 3.5))
        self.w_agc_min.setValue(self.cfg.get("AGC_MIN_GAIN", 0.8))
        self.w_agc_target.setValue(self.cfg.get("AGC_TARGET", 0.35))
        self.w_agc_attack.setValue(self.cfg.get("AGC_ATTACK", 0.03))
        self.w_agc_release.setValue(self.cfg.get("AGC_RELEASE", 0.01))
        
        # Compressor
        self.w_comp_enabled.setChecked(self.cfg.get("BAND_COMPRESSION_ENABLED", True))
        self.w_comp_thresh.setValue(self.cfg.get("COMPRESSOR_THRESHOLD", 0.25))
        self.w_comp_ratio.setValue(self.cfg.get("COMPRESSOR_RATIO", 2.5))
        self.w_comp_knee.setValue(self.cfg.get("COMPRESSOR_KNEE", 0.15))
        self.w_comp_makeup.setValue(self.cfg.get("COMPRESSOR_MAKEUP", 1.4))
        
        # Smoothing
        self.w_smooth_enabled.setChecked(self.cfg.get("ADAPTIVE_SMOOTHING", True))
        self.w_smooth_mult.setValue(self.cfg.get("SMOOTHING_LOW_VOL_MULT", 2.5))
        self.w_smooth_thresh.setValue(self.cfg.get("SMOOTHING_LOW_VOL_THRESH", 0.35))
        
        # Floor
        self.w_floor_enabled.setChecked(self.cfg.get("DYNAMIC_FLOOR_ENABLED", True))
        self.w_floor_max.setValue(self.cfg.get("DYNAMIC_FLOOR_MAX", 0.15))
        self.w_floor_thresh.setValue(self.cfg.get("DYNAMIC_FLOOR_THRESH", 0.30))