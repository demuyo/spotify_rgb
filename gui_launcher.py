# gui_launcher.py
"""
Launcher que integra a GUI com o sistema de áudio reativo.
Pode ser usado standalone ou integrado ao main.py existente.
"""

import sys
import threading
from PyQt6.QtWidgets import QApplication

from gui.tray_icon import TrayManager
from config_manager import ConfigManager


class AppBridge:
    """
    Ponte entre a GUI e o core do sistema.
    Expõe métodos que a GUI usa pra obter status e enviar comandos.
    """

    def __init__(self):
        self._status = {
            'spotify_connected': False,
            'audio_active': False,
            'openrgb_connected': False,
            'is_playing': False,
            'current_track': '',
            'led_count': 0,
            'album_colors': [],
        }
        self._monitor_data = {
            'bands': {'percussion': 0.0, 'bass': 0.0, 'melody': 0.0},
            'band_colors': {},
            'led_colors': [],
            'fps': 0,
            'track': '',
            'is_playing': False,
            'led_count': 0,
        }
        self._paused = False
        self._reactive_system = None
        self._lock = threading.Lock()

    def set_reactive_system(self, system):
        """Conecta com o AudioReactiveSpotifyOnly do main.py."""
        self._reactive_system = system

    def get_status(self) -> dict:
        """Retorna status atual do sistema."""
        if self._reactive_system:
            try:
                self._update_from_reactive()
            except Exception:
                pass
        with self._lock:
            return dict(self._status)

    def get_monitor_data(self) -> dict:
        """Retorna dados de monitoramento pra visualização ao vivo."""
        if self._reactive_system:
            try:
                self._update_monitor_from_reactive()
            except Exception:
                pass
        with self._lock:
            return dict(self._monitor_data)

    def set_paused(self, paused: bool):
        self._paused = paused
        if self._reactive_system and hasattr(self._reactive_system, 'set_paused'):
            self._reactive_system.set_paused(paused)

    def shutdown(self):
        """Desliga tudo de forma limpa."""
        if self._reactive_system and hasattr(self._reactive_system, 'stop'):
            self._reactive_system.stop()

    def _update_from_reactive(self):
        """Atualiza status a partir do sistema reativo."""
        rs = self._reactive_system
        if not rs:
            return

        with self._lock:
            # Spotify
            if hasattr(rs, 'sp') and rs.sp:
                self._status['spotify_connected'] = True
            if hasattr(rs, 'current_track_name'):
                self._status['current_track'] = getattr(rs, 'current_track_name', '')
            if hasattr(rs, 'is_playing'):
                self._status['is_playing'] = getattr(rs, 'is_playing', False)

            # Audio
            if hasattr(rs, 'audio_active'):
                self._status['audio_active'] = getattr(rs, 'audio_active', False)

            # OpenRGB
            if hasattr(rs, 'rgb_client') and rs.rgb_client:
                self._status['openrgb_connected'] = True
                if hasattr(rs, 'total_leds'):
                    self._status['led_count'] = getattr(rs, 'total_leds', 0)

            # Album colors
            if hasattr(rs, 'album_colors'):
                self._status['album_colors'] = list(getattr(rs, 'album_colors', []))

    def _update_monitor_from_reactive(self):
        """Atualiza dados de monitoramento."""
        rs = self._reactive_system
        if not rs:
            return

        with self._lock:
            # Band levels
            if hasattr(rs, 'current_bands'):
                bands = getattr(rs, 'current_bands', {})
                self._monitor_data['bands'] = {
                    'percussion': bands.get('percussion', 0.0),
                    'bass': bands.get('bass', 0.0),
                    'melody': bands.get('melody', 0.0),
                }

            # Band colors
            if hasattr(rs, 'current_band_colors'):
                self._monitor_data['band_colors'] = dict(
                    getattr(rs, 'current_band_colors', {})
                )

            # LED colors (current frame)
            if hasattr(rs, 'current_led_colors'):
                self._monitor_data['led_colors'] = list(
                    getattr(rs, 'current_led_colors', [])
                )

            # FPS
            if hasattr(rs, 'fps'):
                self._monitor_data['fps'] = getattr(rs, 'fps', 0)

            # Track info
            self._monitor_data['track'] = self._status.get('current_track', '')
            self._monitor_data['is_playing'] = self._status.get('is_playing', False)
            self._monitor_data['led_count'] = self._status.get('led_count', 0)

    # ── Métodos pra atualização manual (caso o main.py prefira push) ──

    def update_status(self, key: str, value):
        with self._lock:
            self._status[key] = value

    def update_bands(self, percussion: float, bass: float, melody: float):
        with self._lock:
            self._monitor_data['bands'] = {
                'percussion': percussion,
                'bass': bass,
                'melody': melody,
            }

    def update_led_colors(self, colors: list):
        with self._lock:
            self._monitor_data['led_colors'] = colors

    def update_band_colors(self, colors: dict):
        with self._lock:
            self._monitor_data['band_colors'] = colors


def launch_gui(app_bridge: AppBridge = None):
    """
    Lança a GUI.
    Pode ser chamado do main.py passando um AppBridge conectado.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setQuitOnLastWindowClosed(False)

    if app_bridge is None:
        app_bridge = AppBridge()

    tray = TrayManager(app, app_ref=app_bridge)
    tray.show()

    # Mostra a janela na primeira vez
    tray.show_window()

    return app, tray


def launch_gui_standalone():
    """Lança a GUI standalone (sem o core rodando)."""
    app, tray = launch_gui()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_gui_standalone()