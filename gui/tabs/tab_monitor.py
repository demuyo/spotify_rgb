# gui/tabs/tab_monitor.py
"""Aba de monitoramento ao vivo (visualização das bandas e LEDs)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont


class BandMeter(QWidget):
    """Medidor vertical de uma banda."""

    def __init__(self, label: str, color: tuple = (100, 255, 100), parent=None):
        super().__init__(parent)
        self._label = label
        self._color = color
        self._value = 0.0
        self._peak = 0.0
        self._peak_decay = 0.02
        self.setFixedWidth(60)
        self.setMinimumHeight(200)

    def set_value(self, v: float):
        """Atualiza valor (0.0-1.0)."""
        self._value = min(max(v, 0.0), 1.0)
        if v > self._peak:
            self._peak = v
        else:
            self._peak = max(self._peak - self._peak_decay, self._value)
        self.update()

    def set_color(self, color: tuple):
        """Atualiza cor RGB."""
        if color and len(color) >= 3:
            self._color = color
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        bar_w = 40
        bar_h = h - 40
        bar_x = (w - bar_w) // 2
        bar_y = 10

        # Background (escuro)
        painter.fillRect(bar_x, bar_y, bar_w, bar_h, QBrush(QColor(30, 30, 30)))

        # Barra de valor (com a cor da banda)
        fill_h = int(bar_h * self._value)
        r, g, b = self._color
        
        # Aplica gamma pra visualização
        display_r = min(255, int((r / 255) ** 0.7 * 255))
        display_g = min(255, int((g / 255) ** 0.7 * 255))
        display_b = min(255, int((b / 255) ** 0.7 * 255))
        
        painter.fillRect(
            bar_x, bar_y + bar_h - fill_h,
            bar_w, fill_h,
            QBrush(QColor(display_r, display_g, display_b, 220)),
        )

        # Peak marker (linha branca)
        if self._peak > 0.01:
            peak_y = bar_y + bar_h - int(bar_h * self._peak)
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(bar_x, peak_y, bar_x + bar_w, peak_y)

        # Label (nome da banda)
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(0, h - 20, w, 20, Qt.AlignmentFlag.AlignCenter, self._label)

        # Valor numérico
        painter.setPen(QPen(QColor(display_r, display_g, display_b), 1))
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(
            0, h - 8, w, 15, Qt.AlignmentFlag.AlignCenter,
            f"{self._value:.2f}",
        )

        painter.end()


class LEDStripPreview(QWidget):
    """Preview da fita de LED com gamma correction."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self._colors = []
        self._brightness_floor = 15
        self._gamma = 0.6

    def set_colors(self, colors: list):
        """Atualiza cores dos LEDs."""
        self._colors = colors if colors else []
        self.update()

    def _enhance_color(self, r: int, g: int, b: int) -> tuple:
        """Aplica melhorias visuais."""
        r_norm = r / 255.0
        g_norm = g / 255.0
        b_norm = b / 255.0

        r_gamma = r_norm ** self._gamma
        g_gamma = g_norm ** self._gamma
        b_gamma = b_norm ** self._gamma

        r_out = int(r_gamma * 255)
        g_out = int(g_gamma * 255)
        b_out = int(b_gamma * 255)

        max_component = max(r_out, g_out, b_out)
        if max_component < self._brightness_floor and max_component > 0:
            scale = self._brightness_floor / max_component
            r_out = min(255, int(r_out * scale))
            g_out = min(255, int(g_out * scale))
            b_out = min(255, int(b_out * scale))

        return (r_out, g_out, b_out)

    def paintEvent(self, event):
        if not self._colors:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        w = self.width()
        h = self.height()
        n = len(self._colors)

        if n == 0:
            painter.end()
            return

        led_w = w / n

        for i, color in enumerate(self._colors):
            if not color or len(color) < 3:
                continue
            r, g, b = color[0], color[1], color[2]
            r_display, g_display, b_display = self._enhance_color(r, g, b)

            x = int(i * led_w)
            w_rect = int(led_w) + 1
            painter.fillRect(
                x, 0, w_rect, h,
                QBrush(QColor(r_display, g_display, b_display))
            )

        painter.end()


class TabMonitor(QWidget):
    """Aba de monitoramento ao vivo."""

    def __init__(self, app_ref=None, parent=None):
        super().__init__(parent)
        self.app_ref = app_ref
        
        # Tenta importar o bridge
        self._bridge = None
        try:
            from monitor_bridge import monitor
            self._bridge = monitor
        except ImportError:
            pass

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ══════════════════════════════════════════════════
        # LED STRIP PREVIEW
        # ══════════════════════════════════════════════════
        grp_leds = QGroupBox("Preview dos LEDs")
        ll = QVBoxLayout(grp_leds)
        self.led_preview = LEDStripPreview()
        ll.addWidget(self.led_preview)
        layout.addWidget(grp_leds)

        # ══════════════════════════════════════════════════
        # BAND METERS
        # ══════════════════════════════════════════════════
        grp_bands = QGroupBox("Bandas de Frequência")
        bl = QHBoxLayout(grp_bands)
        bl.setSpacing(20)

        bl.addStretch()
        self.meter_perc = BandMeter("🥁 Perc", (255, 100, 100))
        bl.addWidget(self.meter_perc)
        self.meter_bass = BandMeter("🎸 Bass", (100, 100, 255))
        bl.addWidget(self.meter_bass)
        self.meter_melody = BandMeter("🎹 Melody", (100, 255, 100))
        bl.addWidget(self.meter_melody)
        bl.addStretch()

        layout.addWidget(grp_bands)

        # ══════════════════════════════════════════════════
        # INFO
        # ══════════════════════════════════════════════════
        grp_info = QGroupBox("Informações")
        il = QVBoxLayout(grp_info)

        self._info_label = QLabel("Aguardando dados...")
        self._info_label.setStyleSheet("color: #888; font-family: monospace;")
        self._info_label.setWordWrap(True)
        il.addWidget(self._info_label)

        layout.addWidget(grp_info)

        layout.addStretch()

        # ══════════════════════════════════════════════════
        # UPDATE TIMER
        # ══════════════════════════════════════════════════
        self._timer = QTimer()
        self._timer.timeout.connect(self._update)
        self._timer.start(50)  # 20fps

        # FPS tracking
        self._last_update_count = 0
        self._fps_timer = QTimer()
        self._fps_timer.timeout.connect(self._calc_fps)
        self._fps_timer.start(1000)
        self._update_count = 0
        self._current_fps = 0

    def _calc_fps(self):
        """Calcula FPS do monitor."""
        self._current_fps = self._update_count - self._last_update_count
        self._last_update_count = self._update_count

    def _get_data(self) -> dict:
        """
        Pega dados do monitor.
        Tenta: bridge > app_ref.get_monitor_data() > None
        """
        # Tenta bridge primeiro (mais confiável)
        if self._bridge:
            try:
                return self._bridge.get_data()
            except Exception:
                pass
        
        # Fallback: app_ref
        if self.app_ref and hasattr(self.app_ref, 'get_monitor_data'):
            try:
                return self.app_ref.get_monitor_data()
            except Exception:
                pass
        
        return None

    def _update(self):
        """Atualiza visualização."""
        self._update_count += 1

        try:
            data = self._get_data()

            if not data:
                self._info_label.setText(
                    "⚠ Sem dados do engine\n"
                    "Verifique se o main.py está rodando"
                )
                return

            # ── Band levels ──
            bands = data.get('bands', {})
            self.meter_perc.set_value(bands.get('percussion', 0.0))
            self.meter_bass.set_value(bands.get('bass', 0.0))
            self.meter_melody.set_value(bands.get('melody', 0.0))

            # ── Band colors ──
            colors = data.get('band_colors', {})
            if colors.get('percussion'):
                self.meter_perc.set_color(colors['percussion'])
            if colors.get('bass'):
                self.meter_bass.set_color(colors['bass'])
            if colors.get('melody'):
                self.meter_melody.set_color(colors['melody'])

            # ── LED colors ──
            led_colors = data.get('led_colors', [])
            if led_colors:
                self.led_preview.set_colors(led_colors)

            # ── Info text ──
            info_parts = []
            info_parts.append(f"Monitor FPS: {self._current_fps}")

            if 'fps' in data:
                info_parts.append(f"Engine FPS: {data['fps']:.0f}")
            
            if 'track' in data and data['track']:
                track = data['track']
                if len(track) > 50:
                    track = track[:47] + "..."
                info_parts.append(f"🎵 {track}")
            
            if 'is_playing' in data:
                status = "▶ Playing" if data['is_playing'] else "⏸ Paused"
                info_parts.append(f"Status: {status}")
            
            if 'led_count' in data:
                info_parts.append(f"LEDs: {data['led_count']}")
            
            if 'agc_gain' in data:
                info_parts.append(f"AGC Gain: {data['agc_gain']:.2f}x")

            # Mostra valores das bandas
            if bands:
                band_str = (
                    f"🥁 {bands.get('percussion', 0.0):.2f}  "
                    f"🎸 {bands.get('bass', 0.0):.2f}  "
                    f"🎹 {bands.get('melody', 0.0):.2f}"
                )
                info_parts.append(band_str)
            
            if 'state' in data and data['state'] != 'idle':
                info_parts.append(f"🎯 {data['state'].upper()}")

            self._info_label.setText("\n".join(info_parts))

        except Exception as e:
            import traceback
            self._info_label.setText(
                f"❌ Erro:\n{e}\n\n{traceback.format_exc()}"
            )

    def reload_values(self):
        """Monitor não tem config pra reload."""
        pass