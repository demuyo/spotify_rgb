# gui/tabs/tab_spotify.py
"""Aba de configuração do Spotify (polling, status)."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QScrollArea, QLabel, QHBoxLayout,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap

from gui.widgets import LabeledSlider, StatusIndicator, Separator
from config_manager import ConfigManager


class TabSpotify(QScrollArea):
    def __init__(self, app_ref=None, parent=None):
        super().__init__(parent)
        self.cfg = ConfigManager()
        self.app_ref = app_ref  # Referência ao app principal pra pegar status
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(12)

        # ── Status ──
        grp_status = QGroupBox("Status da Conexão")
        sl = QVBoxLayout(grp_status)

        self.status_spotify = StatusIndicator("Spotify API")
        sl.addWidget(self.status_spotify)

        self.status_audio = StatusIndicator("Captura de Áudio")
        sl.addWidget(self.status_audio)

        self.status_openrgb = StatusIndicator("OpenRGB")
        sl.addWidget(self.status_openrgb)

        sl.addWidget(Separator())

        # Now playing info
        self._now_playing = QLabel("Nenhuma música tocando")
        self._now_playing.setStyleSheet("color: #ccc; font-size: 13px;")
        self._now_playing.setWordWrap(True)
        sl.addWidget(self._now_playing)

        # Album art preview
        self._album_art = QLabel()
        self._album_art.setFixedSize(120, 120)
        self._album_art.setStyleSheet("border: 1px solid #333; border-radius: 4px;")
        sl.addWidget(self._album_art)

        # Colors extracted
        self._colors_row = QHBoxLayout()
        self._color_previews = []
        for i in range(3):
            frame = QWidget()
            frame.setFixedSize(40, 40)
            frame.setStyleSheet("background-color: #333; border-radius: 4px;")
            self._color_previews.append(frame)
            self._colors_row.addWidget(frame)
        self._colors_row.addStretch()
        sl.addLayout(self._colors_row)

        layout.addWidget(grp_status)

        # ── Polling Rates ──
        grp_poll = QGroupBox("Polling Rates")
        pl = QVBoxLayout(grp_poll)

        self.w_poll_interval = LabeledSlider(
            "Intervalo Normal", 1.0, 15.0, 0.5, self.cfg.get("POLL_INTERVAL"), "s",
            "Frequência de checagem quando tocando normalmente",
        )
        self.w_poll_interval.valueChanged.connect(
            lambda v: self._set("POLL_INTERVAL", v)
        )
        pl.addWidget(self.w_poll_interval)

        self.w_poll_ending = LabeledSlider(
            "Perto do Final", 0.5, 5.0, 0.5, self.cfg.get("POLL_ENDING"), "s",
            "Frequência quando a música está quase acabando",
        )
        self.w_poll_ending.valueChanged.connect(
            lambda v: self._set("POLL_ENDING", v)
        )
        pl.addWidget(self.w_poll_ending)

        self.w_poll_ending_soon = LabeledSlider(
            "Quase Acabando", 0.1, 2.0, 0.1, self.cfg.get("POLL_ENDING_SOON"), "s",
        )
        self.w_poll_ending_soon.valueChanged.connect(
            lambda v: self._set("POLL_ENDING_SOON", v)
        )
        pl.addWidget(self.w_poll_ending_soon)

        self.w_poll_change = LabeledSlider(
            "Após Mudança", 0.5, 5.0, 0.5, self.cfg.get("POLL_AFTER_CHANGE"), "s",
        )
        self.w_poll_change.valueChanged.connect(
            lambda v: self._set("POLL_AFTER_CHANGE", v)
        )
        pl.addWidget(self.w_poll_change)

        self.w_poll_idle = LabeledSlider(
            "Idle", 5.0, 60.0, 1.0, self.cfg.get("POLL_IDLE"), "s",
            "Frequência quando nada está tocando",
        )
        self.w_poll_idle.valueChanged.connect(
            lambda v: self._set("POLL_IDLE", v)
        )
        pl.addWidget(self.w_poll_idle)

        layout.addWidget(grp_poll)

        layout.addStretch()
        self.setWidget(container)

        # Status update timer
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(2000)

    def _set(self, key, val):
        self.cfg.set(key, val)
        self.cfg.apply_to_config_module()

    def _update_status(self):
        """Atualiza indicadores de status periodicamente."""
        if not self.app_ref:
            return

        try:
            # Tenta pegar status do app
            if hasattr(self.app_ref, 'get_status'):
                status = self.app_ref.get_status()
                self.status_spotify.set_status(
                    status.get('spotify_connected', False),
                    "Conectado" if status.get('spotify_connected') else "Desconectado",
                )
                self.status_audio.set_status(
                    status.get('audio_active', False),
                    "Capturando" if status.get('audio_active') else "Inativo",
                )
                self.status_openrgb.set_status(
                    status.get('openrgb_connected', False),
                    f"{status.get('led_count', 0)} LEDs" if status.get('openrgb_connected') else "Desconectado",
                )

                track = status.get('current_track', '')
                if track:
                    self._now_playing.setText(f"🎵 {track}")
                else:
                    self._now_playing.setText("Nenhuma música tocando")

                colors = status.get('album_colors', [])
                for i, preview in enumerate(self._color_previews):
                    if i < len(colors):
                        r, g, b = colors[i]
                        preview.setStyleSheet(
                            f"background-color: rgb({r},{g},{b}); border-radius: 4px;"
                        )
                    else:
                        preview.setStyleSheet("background-color: #333; border-radius: 4px;")
        except Exception:
            pass

    def reload_values(self):
        self.w_poll_interval.setValue(self.cfg.get("POLL_INTERVAL"))
        self.w_poll_ending.setValue(self.cfg.get("POLL_ENDING"))
        self.w_poll_ending_soon.setValue(self.cfg.get("POLL_ENDING_SOON"))
        self.w_poll_change.setValue(self.cfg.get("POLL_AFTER_CHANGE"))
        self.w_poll_idle.setValue(self.cfg.get("POLL_IDLE"))