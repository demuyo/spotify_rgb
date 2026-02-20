# startup_manager.py
"""
Gerencia inicialização automática com Windows.
Usa o Registro do Windows (mais limpo que pasta Startup).
"""

import sys
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Nome da chave no registro
APP_NAME = "SpotifyRGBSync"


def _get_executable_path() -> str:
    """Retorna o caminho do executável."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        # Em desenvolvimento, usa pythonw.exe com o script
        python = sys.executable
        script = Path(__file__).parent / "main.py"
        return f'"{python}" "{script}"'


def is_startup_enabled() -> bool:
    """Verifica se o programa está configurado para iniciar com Windows."""
    try:
        import winreg
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        
        try:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
            
    except Exception as e:
        logger.debug(f"Erro ao verificar startup: {e}")
        return False


def enable_startup() -> bool:
    """Adiciona o programa para iniciar com Windows."""
    try:
        import winreg
        
        exe_path = _get_executable_path()
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        
        logger.info(f"✅ Startup habilitado: {exe_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao habilitar startup: {e}")
        return False


def disable_startup() -> bool:
    """Remove o programa da inicialização com Windows."""
    try:
        import winreg
        
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass  # Já não existe
        
        winreg.CloseKey(key)
        
        logger.info("✅ Startup desabilitado")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao desabilitar startup: {e}")
        return False


def set_startup(enabled: bool) -> bool:
    """Define se o programa deve iniciar com Windows."""
    if enabled:
        return enable_startup()
    else:
        return disable_startup()