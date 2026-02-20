# tray_minimal.py
"""
Tray icon MÍNIMO usando pystray.
NÃO importa PyQt6 até clicar em "Configurações".
"""

import threading
import time
import sys
import os
import logging

logger = logging.getLogger(__name__)

# Importa pystray e PIL (leves)
try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    print("pip install pystray pillow")
    sys.exit(1)


class MinimalTray:
    """
    Tray icon minimalista.
    GUI só é importada/criada quando o usuário clica em "Configurações".
    """
    
    def __init__(self, on_quit_callback=None, get_status_callback=None):
        self._on_quit = on_quit_callback
        self._get_status = get_status_callback
        
        self._icon = None
        self._gui_window = None
        self._gui_app = None
        self._current_color = (100, 0, 200)
        self._running = True
        
        # Status
        self._track_name = ""
        self._is_playing = False
        
    def _create_icon_image(self, color: tuple = None) -> Image.Image:
        """Cria ícone colorido simples."""
        if color is None:
            color = self._current_color
            
        img = Image.new('RGB', (64, 64), color)
        draw = ImageDraw.Draw(img)
        
        # Borda preta pra destacar
        draw.rectangle([0, 0, 63, 63], outline=(0, 0, 0), width=2)
        
        # Indicador de status (bolinha)
        if self._is_playing:
            draw.ellipse([50, 50, 62, 62], fill=(0, 255, 0))  # Verde = tocando
        else:
            draw.ellipse([50, 50, 62, 62], fill=(100, 100, 100))  # Cinza = pausado
        
        return img
    
    def _open_settings(self, icon, item):
        """
        Abre a GUI de configurações.
        LAZY LOAD: Só importa PyQt6 aqui!
        """
        # Roda em thread separada pra não bloquear o tray
        threading.Thread(target=self._launch_gui, daemon=True).start()
    
    def _launch_gui(self):
        """Lança a GUI (lazy load)."""
        try:
            # Só agora importa PyQt6 (pesado)
            from PyQt6.QtWidgets import QApplication
            from PyQt6.QtCore import Qt
            
            # Verifica se já existe uma instância
            if self._gui_app is None:
                self._gui_app = QApplication.instance()
                if self._gui_app is None:
                    self._gui_app = QApplication(sys.argv)
                    self._gui_app.setQuitOnLastWindowClosed(False)
            
            # Importa a janela principal
            from gui.main_window import MainWindow
            
            if self._gui_window is None:
                # Cria AppBridge se disponível
                try:
                    from gui_launcher import AppBridge
                    bridge = AppBridge()
                except:
                    bridge = None
                
                self._gui_window = MainWindow(app_ref=bridge)
                self._gui_window.set_close_to_tray(True)
            
            self._gui_window.show()
            self._gui_window.raise_()
            self._gui_window.activateWindow()
            
            # Processa eventos se não estiver rodando
            if not self._gui_app.property("running"):
                self._gui_app.setProperty("running", True)
                # Event loop em thread separada
                self._gui_app.exec()
                
        except ImportError as e:
            logger.warning(f"GUI não disponível: {e}")
            self._show_notification("GUI não disponível", "PyQt6 não instalado")
        except Exception as e:
            logger.error(f"Erro ao abrir GUI: {e}")
    
    def _show_log(self, icon, item):
        """Abre o arquivo de log."""
        import subprocess
        try:
            subprocess.Popen(["notepad.exe", "spotify_rgb.log"])
        except:
            pass
    
    def _quit(self, icon, item):
        """Encerra o programa."""
        self._running = False
        
        # Fecha GUI se existir
        if self._gui_window:
            try:
                self._gui_window.set_close_to_tray(False)
                self._gui_window.close()
            except:
                pass
        
        # Callback de quit
        if self._on_quit:
            self._on_quit()
        
        # Para o ícone
        icon.stop()
    
    def _show_notification(self, title: str, message: str):
        """Mostra notificação do sistema."""
        if self._icon:
            try:
                self._icon.notify(message, title)
            except:
                pass
    
    def _build_menu(self):
        """Constrói o menu do tray."""
        # Status (desabilitado)
        status_text = "▶ Tocando" if self._is_playing else "⏸ Pausado"
        track_text = self._track_name[:40] if self._track_name else "---"
        
        return pystray.Menu(
            pystray.MenuItem(
                f"🎵 Spotify RGB Sync",
                None,
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                f"{status_text}",
                None,
                enabled=False
            ),
            pystray.MenuItem(
                f"♪ {track_text}",
                None,
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "⚙️ Configurações",
                self._open_settings
            ),
            pystray.MenuItem(
                "📄 Ver Log",
                self._show_log
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "❌ Sair",
                self._quit
            ),
        )
    
    def update_status(self, track_name: str = None, is_playing: bool = None, color: tuple = None):
        """Atualiza status do tray (thread-safe)."""
        if track_name is not None:
            self._track_name = track_name
        if is_playing is not None:
            self._is_playing = is_playing
        if color is not None:
            self._current_color = color
        
        # Atualiza ícone e menu
        if self._icon:
            try:
                self._icon.icon = self._create_icon_image()
                self._icon.menu = self._build_menu()
            except:
                pass
    
    def run(self):
        """Inicia o tray icon."""
        self._icon = pystray.Icon(
            name="SpotifyRGB",
            icon=self._create_icon_image(),
            title="Spotify RGB Sync",
            menu=self._build_menu()
        )
        
        # Thread pra atualizar status periodicamente
        def update_loop():
            while self._running:
                if self._get_status:
                    try:
                        status = self._get_status()
                        self.update_status(
                            track_name=status.get('track', ''),
                            is_playing=status.get('is_playing', False),
                            color=status.get('color', (100, 0, 200))
                        )
                    except:
                        pass
                time.sleep(3)  # Atualiza a cada 3 segundos
        
        threading.Thread(target=update_loop, daemon=True).start()
        
        # Roda o tray (bloqueia)
        self._icon.run()