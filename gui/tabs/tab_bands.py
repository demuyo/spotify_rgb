# gui/tabs/tab_bands.py
"""Aba de configuração das bandas (percussão, baixo, melodia)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QScrollArea, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt

from gui.widgets import (
    LabeledSlider, LabeledCombo, LabeledCheck, Separator,
)
from config_manager import ConfigManager


class ZonePreview(QWidget):
    """Preview visual da distribuição das zonas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self._zones = (0.36, 0.32, 0.32)
        self._colors = [(255, 100, 100), (100, 100, 255), (100, 255, 100)]
        self._labels = ["Perc", "Baixo", "Melodia"]

    def set_zones(self, perc, bass, melody):
        self._zones = (perc, bass, melody)
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QBrush, QColor, QPen

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width() - 4
        h = self.height() - 4
        x = 2

        total = sum(self._zones)
        for i, (zone_pct, color, label) in enumerate(
            zip(self._zones, self._colors, self._labels)
        ):
            zone_w = int(w * zone_pct / total)
            r, g, b = color
            painter.setBrush(QBrush(QColor(r, g, b, 180)))
            painter.setPen(QPen(QColor(r, g, b), 1))
            painter.drawRoundedRect(x, 2, zone_w, h, 4, 4)

            painter.setPen(QPen(QColor(255, 255, 255), 1))
            font = painter.font()
            font.setPointSize(9)
            font.setBold(True)
            painter.setFont(font)
            pct_text = f"{label} {zone_pct * 100:.0f}%"
            painter.drawText(x, 2, zone_w, h, Qt.AlignmentFlag.AlignCenter, pct_text)

            x += zone_w + 2

        painter.end()


class TabBands(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # ── Distribuição de Zonas ──
        grp_zones = QGroupBox("Distribuição de Zonas")
        zl = QVBoxLayout(grp_zones)

        self.zone_preview = ZonePreview()
        zl.addWidget(self.zone_preview)

        self.w_zone_perc = LabeledSlider(
            "🥁 Percussão", 0.1, 0.6, 0.01,
            self.cfg.get("BAND_ZONE_PERCUSSION"), suffix="%",
            description="Porcentagem dos LEDs para percussão",
        )
        self.w_zone_perc.valueChanged.connect(self._on_zone_change)
        zl.addWidget(self.w_zone_perc)

        self.w_zone_bass = LabeledSlider(
            "🎸 Baixo", 0.1, 0.6, 0.01,
            self.cfg.get("BAND_ZONE_BASS"), suffix="%",
            description="Porcentagem dos LEDs para baixo",
        )
        self.w_zone_bass.valueChanged.connect(self._on_zone_change)
        zl.addWidget(self.w_zone_bass)

        self.w_zone_melody = LabeledSlider(
            "🎹 Melodia", 0.1, 0.6, 0.01,
            self.cfg.get("BAND_ZONE_MELODY"), suffix="%",
            description="Porcentagem dos LEDs para melodia",
        )
        self.w_zone_melody.valueChanged.connect(self._on_zone_change)
        zl.addWidget(self.w_zone_melody)

        layout.addWidget(grp_zones)

        # ── Color Scheme ──
        grp_color = QGroupBox("Esquema de Cores")
        cl = QVBoxLayout(grp_color)

        self.w_color_scheme = LabeledCombo(
            "Esquema",
            ["album_colors", "fixed_hue", "complementary", "analogous"],
            self.cfg.get("BAND_COLOR_SCHEME"),
            "album_colors = extrai 3 cores do álbum",
        )
        self.w_color_scheme.currentTextChanged.connect(
            lambda v: self._set("BAND_COLOR_SCHEME", v)
        )
        cl.addWidget(self.w_color_scheme)

        layout.addWidget(grp_color)

        # ── Boost & Dynamics ──
        grp_boost = QGroupBox("Boost & Dinâmica por Banda")
        bl = QVBoxLayout(grp_boost)

        # Percussion
        bl.addWidget(QLabel("🥁 Percussão"))
        self.w_boost_perc = LabeledSlider(
            "Boost", 0.5, 4.0, 0.1, self.cfg.get("BAND_BOOST_PERCUSSION"), "x"
        )
        self.w_boost_perc.valueChanged.connect(
            lambda v: self._set("BAND_BOOST_PERCUSSION", v)
        )
        bl.addWidget(self.w_boost_perc)

        self.w_exp_perc = LabeledSlider(
            "Expansão", 1.0, 4.0, 0.1, self.cfg.get("BAND_EXPANSION_PERCUSSION"), "x",
            "Aumenta contraste entre volumes baixos e altos",
        )
        self.w_exp_perc.valueChanged.connect(
            lambda v: self._set("BAND_EXPANSION_PERCUSSION", v)
        )
        bl.addWidget(self.w_exp_perc)

        bl.addWidget(Separator())

        # Bass
        bl.addWidget(QLabel("🎸 Baixo"))
        self.w_boost_bass = LabeledSlider(
            "Boost", 0.5, 4.0, 0.1, self.cfg.get("BAND_BOOST_BASS"), "x"
        )
        self.w_boost_bass.valueChanged.connect(
            lambda v: self._set("BAND_BOOST_BASS", v)
        )
        bl.addWidget(self.w_boost_bass)

        self.w_exp_bass = LabeledSlider(
            "Expansão", 1.0, 4.0, 0.1, self.cfg.get("BAND_EXPANSION_BASS"), "x"
        )
        self.w_exp_bass.valueChanged.connect(
            lambda v: self._set("BAND_EXPANSION_BASS", v)
        )
        bl.addWidget(self.w_exp_bass)

        bl.addWidget(Separator())

        # Melody
        bl.addWidget(QLabel("🎹 Melodia"))
        self.w_boost_melody = LabeledSlider(
            "Boost", 0.5, 4.0, 0.1, self.cfg.get("BAND_BOOST_MELODY"), "x"
        )
        self.w_boost_melody.valueChanged.connect(
            lambda v: self._set("BAND_BOOST_MELODY", v)
        )
        bl.addWidget(self.w_boost_melody)

        self.w_exp_melody = LabeledSlider(
            "Expansão", 1.0, 4.0, 0.1, self.cfg.get("BAND_EXPANSION_MELODY"), "x"
        )
        self.w_exp_melody.valueChanged.connect(
            lambda v: self._set("BAND_EXPANSION_MELODY", v)
        )
        bl.addWidget(self.w_exp_melody)

        layout.addWidget(grp_boost)

        # ── Smoothing ──
        grp_smooth = QGroupBox("Suavização & Timing")
        sl = QVBoxLayout(grp_smooth)

        self.w_attack = LabeledSlider(
            "Attack", 0.05, 1.0, 0.01, self.cfg.get("BAND_ATTACK"),
            description="Velocidade de subida (maior = mais rápido)",
        )
        self.w_attack.valueChanged.connect(
            lambda v: self._set("BAND_ATTACK", v)
        )
        sl.addWidget(self.w_attack)

        self.w_decay = LabeledSlider(
            "Decay", 0.01, 0.5, 0.01, self.cfg.get("BAND_DECAY"),
            description="Velocidade de descida (menor = mais lento)",
        )
        self.w_decay.valueChanged.connect(
            lambda v: self._set("BAND_DECAY", v)
        )
        sl.addWidget(self.w_decay)

        sl.addWidget(Separator())

        self.w_beat_flash = LabeledSlider(
            "Beat Flash", 0.0, 1.0, 0.05, self.cfg.get("BAND_BEAT_FLASH"),
            description="Intensidade do flash no beat",
        )
        self.w_beat_flash.valueChanged.connect(
            lambda v: self._set("BAND_BEAT_FLASH", v)
        )
        sl.addWidget(self.w_beat_flash)

        self.w_bg_brightness = LabeledSlider(
            "Brilho de Fundo", 0.0, 0.2, 0.005, self.cfg.get("BAND_BG_BRIGHTNESS"),
            description="Brilho mínimo quando a banda está silenciosa",
        )
        self.w_bg_brightness.valueChanged.connect(
            lambda v: self._set("BAND_BG_BRIGHTNESS", v)
        )
        sl.addWidget(self.w_bg_brightness)

        layout.addWidget(grp_smooth)

        # ── Compression ──
        grp_comp = QGroupBox("Compressão")
        cpl = QVBoxLayout(grp_comp)

        self.w_comp_enabled = LabeledCheck(
            "Compressão Ativa",
            self.cfg.get("BAND_COMPRESSION_ENABLED"),
            "Limita volumes muito altos pra manter contraste",
        )
        self.w_comp_enabled.toggled.connect(
            lambda v: self._set("BAND_COMPRESSION_ENABLED", v)
        )
        cpl.addWidget(self.w_comp_enabled)

        self.w_comp_threshold = LabeledSlider(
            "Threshold", 0.3, 1.0, 0.05, self.cfg.get("BAND_COMPRESSION_THRESHOLD"),
            description="Acima desse nível, começa a comprimir",
        )
        self.w_comp_threshold.valueChanged.connect(
            lambda v: self._set("BAND_COMPRESSION_THRESHOLD", v)
        )
        cpl.addWidget(self.w_comp_threshold)

        self.w_comp_ratio = LabeledSlider(
            "Ratio", 1.0, 10.0, 0.5, self.cfg.get("BAND_COMPRESSION_RATIO"), ":1",
            description="Taxa de compressão (maior = mais comprimido)",
        )
        self.w_comp_ratio.valueChanged.connect(
            lambda v: self._set("BAND_COMPRESSION_RATIO", v)
        )
        cpl.addWidget(self.w_comp_ratio)

        layout.addWidget(grp_comp)

        layout.addStretch()
        self.setWidget(container)

        self._update_zone_preview()

    def _on_zone_change(self, _=None):
        self._set("BAND_ZONE_PERCUSSION", self.w_zone_perc.value())
        self._set("BAND_ZONE_BASS", self.w_zone_bass.value())
        self._set("BAND_ZONE_MELODY", self.w_zone_melody.value())
        self._update_zone_preview()

    def _update_zone_preview(self):
        self.zone_preview.set_zones(
            self.w_zone_perc.value(),
            self.w_zone_bass.value(),
            self.w_zone_melody.value(),
        )

    def _set(self, key, val):
        self.cfg.set(key, val)
        self.cfg.apply_to_config_module()

    def reload_values(self):
        self.w_zone_perc.setValue(self.cfg.get("BAND_ZONE_PERCUSSION"))
        self.w_zone_bass.setValue(self.cfg.get("BAND_ZONE_BASS"))
        self.w_zone_melody.setValue(self.cfg.get("BAND_ZONE_MELODY"))
        self.w_color_scheme.setCurrentText(self.cfg.get("BAND_COLOR_SCHEME"))
        self.w_boost_perc.setValue(self.cfg.get("BAND_BOOST_PERCUSSION"))
        self.w_boost_bass.setValue(self.cfg.get("BAND_BOOST_BASS"))
        self.w_boost_melody.setValue(self.cfg.get("BAND_BOOST_MELODY"))
        self.w_exp_perc.setValue(self.cfg.get("BAND_EXPANSION_PERCUSSION"))
        self.w_exp_bass.setValue(self.cfg.get("BAND_EXPANSION_BASS"))
        self.w_exp_melody.setValue(self.cfg.get("BAND_EXPANSION_MELODY"))
        self.w_attack.setValue(self.cfg.get("BAND_ATTACK"))
        self.w_decay.setValue(self.cfg.get("BAND_DECAY"))
        self.w_beat_flash.setValue(self.cfg.get("BAND_BEAT_FLASH"))
        self.w_bg_brightness.setValue(self.cfg.get("BAND_BG_BRIGHTNESS"))
        self.w_comp_enabled.setChecked(self.cfg.get("BAND_COMPRESSION_ENABLED"))
        self.w_comp_threshold.setValue(self.cfg.get("BAND_COMPRESSION_THRESHOLD"))
        self.w_comp_ratio.setValue(self.cfg.get("BAND_COMPRESSION_RATIO"))
        self._update_zone_preview()