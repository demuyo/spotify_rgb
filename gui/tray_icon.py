# gui/tray_icon.py
"""
System tray icon para o Spotify RGB Sync.
Permite abrir/fechar a GUI, pausar/continuar e sair.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction
from PyQt6.QtCore import QTimer

from gui.main_window import MainWindow
from config_manager import ConfigManager


def create_default_icon() -> QIcon:
    """Cria um ícone padrão caso não exista icon.png."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Circle background
    painter.setBrush(QColor(30, 185, 84))
    painter.setPen(QColor(30, 185, 84))
    painter.drawEllipse(4, 4, 56, 56)

    # "RGB" text
    painter.setPen(QColor(0, 0, 0))
    font = painter.font()
    font.setPointSize(14)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(4, 4, 56, 56, 0x0084, "RGB")  # AlignCenter

    painter.end()
    return QIcon(pixmap)


class TrayManager:
    """Gerencia o tray icon e a janela principal."""

    def __init__(self, app: QApplication, app_ref=None):
        self.app = app
        self.app_ref = app_ref
        self.cfg = ConfigManager()

        # Load or create icon
        try:
            self.icon = QIcon("icon.png")
            if self.icon.isNull():
                self.icon = create_default_icon()
        except Exception:
            self.icon = create_default_icon()

        # Create tray icon
        self.tray = QSystemTrayIcon(self.icon)
        self.tray.setToolTip("Spotify RGB Sync")
        self.tray.activated.connect(self._on_tray_activated)

        # Create menu
        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #252525;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px;
                color: #e0e0e0;
            }
            QMenu::item {
                padding: 6px 30px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #1db954;
                color: #000;
            }
            QMenu::separator {
                height: 1px;
                background: #444;
                margin: 4px 8px;
            }
        """)

        # Actions
        self.action_show = QAction("⚙️ Configurações", self.menu)
        self.action_show.triggered.connect(self.show_window)
        self.menu.addAction(self.action_show)

        self.menu.addSeparator()

        self.action_status = QAction("🔄 Aguardando...", self.menu)
        self.action_status.setEnabled(False)
        self.menu.addAction(self.action_status)

        self.action_track = QAction("🎵 ---", self.menu)
        self.action_track.setEnabled(False)
        self.menu.addAction(self.action_track)

        self.menu.addSeparator()

        self.action_pause = QAction("⏸ Pausar LEDs", self.menu)
        self.action_pause.triggered.connect(self._toggle_pause)
        self.menu.addAction(self.action_pause)

        self.menu.addSeparator()

        self.action_save = QAction("💾 Salvar Config", self.menu)
        self.action_save.triggered.connect(self._save_config)
        self.menu.addAction(self.action_save)

        self.menu.addSeparator()

        self.action_quit = QAction("❌ Sair", self.menu)
        self.action_quit.triggered.connect(self._quit)
        self.menu.addAction(self.action_quit)

        self.tray.setContextMenu(self.menu)

        # Main window (criada lazy)
        self._window = None

        # Status update timer
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_tray_status)
        self._status_timer.start(3000)

        self._paused = False

    def show(self):
        """Mostra o tray icon."""
        self.tray.show()

    def show_window(self):
        """Mostra/cria a janela de configurações."""
        if self._window is None:
            self._window = MainWindow(app_ref=self.app_ref)
            self._window.closing.connect(self._on_window_hidden)

        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    def _on_window_hidden(self):
        """Chamado quando a janela é fechada (escondida pro tray)."""
        self.tray.showMessage(
            "Spotify RGB Sync",
            "Minimizado para a bandeja do sistema",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()

    def _toggle_pause(self):
        self._paused = not self._paused
        if self.app_ref and hasattr(self.app_ref, 'set_paused'):
            self.app_ref.set_paused(self._paused)

        if self._paused:
            self.action_pause.setText("▶ Retomar LEDs")
        else:
            self.action_pause.setText("⏸ Pausar LEDs")

    def _save_config(self):
        try:
            self.cfg.apply_to_config_module()
            self.cfg.save_to_file()
            self.tray.showMessage(
                "Spotify RGB Sync",
                "Configuração salva com sucesso!",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
        except Exception as e:
            self.tray.showMessage(
                "Erro",
                f"Falha ao salvar: {e}",
                QSystemTrayIcon.MessageIcon.Critical,
                3000,
            )

    def _update_tray_status(self):
        if not self.app_ref:
            return

        try:
            if hasattr(self.app_ref, 'get_status'):
                status = self.app_ref.get_status()

                if status.get('is_playing'):
                    track = status.get('current_track', '---')
                    self.action_status.setText("▶ Tocando")
                    self.action_track.setText(f"🎵 {track[:50]}")
                    self.tray.setToolTip(f"Spotify RGB Sync\n▶ {track}")
                elif status.get('spotify_connected'):
                    self.action_status.setText("⏸ Pausado")
                    self.action_track.setText("🎵 ---")
                    self.tray.setToolTip("Spotify RGB Sync\n⏸ Pausado")
                else:
                    self.action_status.setText("🔴 Desconectado")
                    self.action_track.setText("🎵 ---")
                    self.tray.setToolTip("Spotify RGB Sync\n🔴 Desconectado")
        except Exception:
            pass

    def _quit(self):
        """Sai do programa completamente."""
        if self._window:
            self._window.set_close_to_tray(False)
            self._window.close()

        # Tentar limpar LEDs
        if self.app_ref and hasattr(self.app_ref, 'shutdown'):
            self.app_ref.shutdown()

        self.tray.hide()
        self.app.quit()