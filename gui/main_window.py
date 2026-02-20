# gui/main_window.py
"""
Janela principal da GUI do Spotify RGB Sync.
Contém todas as abas e a barra de status.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStatusBar, QLabel, QFileDialog, QMessageBox,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QCloseEvent

from gui.styles import DARK_THEME
from gui.tabs.tab_general import TabGeneral
from gui.tabs.tab_bands import TabBands
from gui.tabs.tab_brightness import TabBrightness
from gui.tabs.tab_colors import TabColors
from gui.tabs.tab_detection import TabDetection
from gui.tabs.tab_effects import TabEffects
from gui.tabs.tab_standby import TabStandby
from gui.tabs.tab_spotify import TabSpotify
from gui.tabs.tab_advanced import TabAdvanced
from gui.tabs.tab_monitor import TabMonitor
from config_manager import ConfigManager


class MainWindow(QMainWindow):
    """Janela principal com abas de configuração."""

    closing = pyqtSignal()  # Emite quando a janela fecha (pra esconder, não sair)

    def __init__(self, app_ref=None, parent=None):
        super().__init__(parent)
        self.app_ref = app_ref
        self.cfg = ConfigManager()
        self._close_to_tray = True

        self.setWindowTitle("Spotify RGB Sync - Configurações")
        self.setMinimumSize(700, 600)
        self.resize(850, 700)
        self.setStyleSheet(DARK_THEME)

        # Try to set icon
        try:
            self.setWindowIcon(QIcon("icon.png"))
        except Exception:
            pass

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        # Create tabs
        self.tab_general = TabGeneral()
        self.tab_bands = TabBands()
        self.tab_brightness = TabBrightness()
        self.tab_colors = TabColors()
        self.tab_detection = TabDetection()
        self.tab_effects = TabEffects()
        self.tab_standby = TabStandby()
        self.tab_spotify = TabSpotify(app_ref=app_ref)
        self.tab_advanced = TabAdvanced()
        self.tab_monitor = TabMonitor(app_ref=app_ref)

        self.tabs.addTab(self.tab_monitor, "📊 Monitor")
        self.tabs.addTab(self.tab_general, "⚙️ Geral")
        self.tabs.addTab(self.tab_bands, "🎵 Bandas")
        self.tabs.addTab(self.tab_brightness, "💡 Brilho")
        self.tabs.addTab(self.tab_colors, "🎨 Cores")
        self.tabs.addTab(self.tab_detection, "🥁 Detecção")
        self.tabs.addTab(self.tab_effects, "✨ Efeitos")
        self.tabs.addTab(self.tab_standby, "😴 Standby")
        self.tabs.addTab(self.tab_spotify, "🎧 Spotify")
        self.tabs.addTab(self.tab_advanced, "🔧 Avançado")

        main_layout.addWidget(self.tabs)

        # Bottom buttons
        btn_layout = QHBoxLayout()

        self.btn_save = QPushButton("💾 Salvar Config")
        self.btn_save.setProperty("class", "primary")
        self.btn_save.clicked.connect(self._save_config)
        btn_layout.addWidget(self.btn_save)

        self.btn_reload = QPushButton("🔄 Reload Tudo")
        self.btn_reload.clicked.connect(self._reload_all)
        btn_layout.addWidget(self.btn_reload)

        self.btn_reset = QPushButton("↩️ Reset Padrão")
        self.btn_reset.setProperty("class", "danger")
        self.btn_reset.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(self.btn_reset)

        btn_layout.addStretch()

        self.btn_export = QPushButton("📤 Exportar Preset")
        self.btn_export.clicked.connect(self._export_preset)
        btn_layout.addWidget(self.btn_export)

        self.btn_import = QPushButton("📥 Importar Preset")
        self.btn_import.clicked.connect(self._import_preset)
        btn_layout.addWidget(self.btn_import)

        main_layout.addLayout(btn_layout)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._status_label = QLabel("Pronto")
        self.status_bar.addPermanentWidget(self._status_label)

        # Status update timer
        self._status_timer = QTimer()
        self._status_timer.timeout.connect(self._update_status_bar)
        self._status_timer.start(1000)

    def _save_config(self):
        try:
            self.cfg.apply_to_config_module()
            self.cfg.save_to_file()
            self._show_status("✅ Configuração salva com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Salvar", str(e))

    def _reload_all(self):
        """Recarrega todos os valores das abas a partir do ConfigManager."""
        all_tabs = [
            self.tab_general, self.tab_bands, self.tab_brightness,
            self.tab_colors, self.tab_detection, self.tab_effects,
            self.tab_standby, self.tab_spotify, self.tab_advanced,
            self.tab_monitor,
        ]
        for tab in all_tabs:
            if hasattr(tab, 'reload_values'):
                tab.reload_values()
        self._show_status("🔄 Configurações recarregadas")

    def _reset_defaults(self):
        reply = QMessageBox.question(
            self, "Reset",
            "Tem certeza que deseja restaurar TODAS as configurações para o padrão?\n"
            "Isso não pode ser desfeito.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.cfg.reset_all()
            self.cfg.apply_to_config_module()
            self._reload_all()
            self._show_status("↩️ Configurações restauradas para o padrão")

    def _export_preset(self):
        from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(
            self, "Exportar Preset", "Nome do preset:"
        )
        if ok and name:
            try:
                path = self.cfg.export_preset(name)
                self._show_status(f"📤 Preset '{name}' exportado para {path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))

    def _import_preset(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar Preset", "", "JSON Files (*.json)"
        )
        if path:
            try:
                self.cfg.import_preset(path)
                self._reload_all()
                self._show_status(f"📥 Preset importado de {path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))

    def _show_status(self, msg: str, timeout: int = 5000):
        self._status_label.setText(msg)
        if timeout:
            QTimer.singleShot(timeout, lambda: self._status_label.setText("Pronto"))

    def _update_status_bar(self):
        if self.app_ref and hasattr(self.app_ref, 'get_status'):
            try:
                status = self.app_ref.get_status()
                parts = []
                if status.get('spotify_connected'):
                    parts.append("🟢 Spotify")
                else:
                    parts.append("🔴 Spotify")
                if status.get('openrgb_connected'):
                    parts.append(f"🟢 OpenRGB ({status.get('led_count', 0)} LEDs)")
                else:
                    parts.append("🔴 OpenRGB")
                if status.get('is_playing'):
                    parts.append("▶")
                else:
                    parts.append("⏸")

                current = self._status_label.text()
                if not current.startswith(("✅", "🔄", "↩️", "📤", "📥")):
                    self._status_label.setText("  |  ".join(parts))
            except Exception:
                pass

    def set_close_to_tray(self, enabled: bool):
        self._close_to_tray = enabled

    def closeEvent(self, event: QCloseEvent):
        if self._close_to_tray:
            event.ignore()
            self.hide()
            self.closing.emit()
        else:
            event.accept()