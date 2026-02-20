# gui/tabs/tab_general.py
"""Aba de configurações gerais."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QScrollArea, QLabel,
    QHBoxLayout, QCheckBox, QPushButton, QMessageBox,
)
from PyQt6.QtCore import Qt

from gui.widgets import LabeledCombo, LabeledToggle, LabeledSlider
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

        # ══════════════════════════════════════════════════
        # INICIALIZAÇÃO
        # ══════════════════════════════════════════════════
        grp_startup = QGroupBox("🚀 Inicialização")
        startup_layout = QVBoxLayout(grp_startup)

        # Checkbox de iniciar com Windows
        self.chk_startup = QCheckBox("Iniciar com o Windows")
        self.chk_startup.setToolTip(
            "Quando marcado, o programa inicia automaticamente quando você liga o PC"
        )
        self._load_startup_state()
        self.chk_startup.toggled.connect(self._on_startup_changed)
        startup_layout.addWidget(self.chk_startup)

        # Checkbox de iniciar minimizado
        self.chk_minimized = QCheckBox("Iniciar minimizado (só tray)")
        self.chk_minimized.setToolTip(
            "Inicia apenas com o ícone na bandeja, sem janela"
        )
        self.chk_minimized.setChecked(self.cfg.get("START_MINIMIZED", True))
        self.chk_minimized.toggled.connect(
            lambda v: self._set("START_MINIMIZED", v)
        )
        startup_layout.addWidget(self.chk_minimized)

        layout.addWidget(grp_startup)

        # ══════════════════════════════════════════════════
        # MODO DE OPERAÇÃO
        # ══════════════════════════════════════════════════
        grp_mode = QGroupBox("🎮 Modo de Operação")
        mode_layout = QVBoxLayout(grp_mode)

        self.w_reactive = LabeledToggle(
            "Modo Reativo (áudio)",
            self.cfg.get("REACTIVE_MODE", True),
        )
        self.w_reactive.toggled.connect(
            lambda v: self._set("REACTIVE_MODE", v)
        )
        mode_layout.addWidget(self.w_reactive)

        self.w_visual_effect = LabeledCombo(
            "Efeito Visual",
            ["bands", "chase", "frequency", "hybrid", "solid"],
            self.cfg.get("VISUAL_EFFECT", "bands"),
            "bands = por instrumento | chase = corrida | frequency = espectro",
        )
        self.w_visual_effect.currentTextChanged.connect(
            lambda v: self._set("VISUAL_EFFECT", v)
        )
        mode_layout.addWidget(self.w_visual_effect)

        self.w_detection = LabeledCombo(
            "Modo de Detecção",
            ["peaks", "drums", "both"],
            self.cfg.get("DETECTION_MODE", "peaks"),
            "peaks = picos gerais | drums = kick/snare | both = ambos",
        )
        self.w_detection.currentTextChanged.connect(
            lambda v: self._set("DETECTION_MODE", v)
        )
        mode_layout.addWidget(self.w_detection)

        layout.addWidget(grp_mode)

        # ══════════════════════════════════════════════════
        # LEDs
        # ══════════════════════════════════════════════════
        grp_leds = QGroupBox("💡 Configuração de LEDs")
        leds_layout = QVBoxLayout(grp_leds)

        self.w_skip_start = LabeledSlider(
            "Pular LEDs (início)", 0, 20, 1,
            self.cfg.get("LED_SKIP_START", 0),
            description="Quantos LEDs ignorar no início da fita",
        )
        self.w_skip_start.valueChanged.connect(
            lambda v: self._set("LED_SKIP_START", int(v))
        )
        leds_layout.addWidget(self.w_skip_start)

        self.w_skip_end = LabeledSlider(
            "Pular LEDs (fim)", 0, 20, 1,
            self.cfg.get("LED_SKIP_END", 0),
            description="Quantos LEDs ignorar no final da fita",
        )
        self.w_skip_end.valueChanged.connect(
            lambda v: self._set("LED_SKIP_END", int(v))
        )
        leds_layout.addWidget(self.w_skip_end)

        layout.addWidget(grp_leds)

        # ══════════════════════════════════════════════════
        # PERFORMANCE
        # ══════════════════════════════════════════════════
        grp_perf = QGroupBox("⚡ Performance")
        perf_layout = QVBoxLayout(grp_perf)

        desc_perf = QLabel(
            "Reduza a taxa de atualização se tiver problemas de performance."
        )
        desc_perf.setStyleSheet("color: #888; font-size: 11px;")
        desc_perf.setWordWrap(True)
        perf_layout.addWidget(desc_perf)

        self.w_fps_limit = LabeledSlider(
            "FPS Máximo", 15, 120, 5,
            self.cfg.get("MAX_FPS", 60),
            description="Limita quantas vezes por segundo os LEDs atualizam",
        )
        self.w_fps_limit.valueChanged.connect(
            lambda v: self._set("MAX_FPS", int(v))
        )
        perf_layout.addWidget(self.w_fps_limit)

        self.w_standby_fps = LabeledSlider(
            "FPS em Standby", 5, 30, 5,
            self.cfg.get("STANDBY_FPS", 15),
            description="FPS quando a música está pausada (economia de CPU)",
        )
        self.w_standby_fps.valueChanged.connect(
            lambda v: self._set("STANDBY_FPS", int(v))
        )
        perf_layout.addWidget(self.w_standby_fps)

        layout.addWidget(grp_perf)

        layout.addStretch()
        self.setWidget(container)

    def _set(self, key, val):
        self.cfg.set(key, val)
        self.cfg.apply_to_config_module()

    def _load_startup_state(self):
        """Carrega o estado atual do startup."""
        try:
            from startup_manager import is_startup_enabled
            self.chk_startup.setChecked(is_startup_enabled())
        except Exception as e:
            self.chk_startup.setEnabled(False)
            self.chk_startup.setToolTip(f"Erro ao verificar: {e}")

    def _on_startup_changed(self, checked: bool):
        """Altera configuração de startup."""
        try:
            from startup_manager import set_startup
            success = set_startup(checked)
            
            if not success:
                # Reverte o checkbox
                self.chk_startup.blockSignals(True)
                self.chk_startup.setChecked(not checked)
                self.chk_startup.blockSignals(False)
                
                QMessageBox.warning(
                    self,
                    "Erro",
                    "Não foi possível alterar a configuração de inicialização.\n"
                    "Tente executar como administrador."
                )
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def reload_values(self):
        self._load_startup_state()
        self.chk_minimized.setChecked(self.cfg.get("START_MINIMIZED", True))
        self.w_reactive.setChecked(self.cfg.get("REACTIVE_MODE", True))
        self.w_visual_effect.setCurrentText(self.cfg.get("VISUAL_EFFECT", "bands"))
        self.w_detection.setCurrentText(self.cfg.get("DETECTION_MODE", "peaks"))
        self.w_skip_start.setValue(self.cfg.get("LED_SKIP_START", 0))
        self.w_skip_end.setValue(self.cfg.get("LED_SKIP_END", 0))
        self.w_fps_limit.setValue(self.cfg.get("MAX_FPS", 60))
        self.w_standby_fps.setValue(self.cfg.get("STANDBY_FPS", 15))