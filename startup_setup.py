# startup_setup.py
"""
Configura o SpotifyRGB pra iniciar com o Windows.
Roda isso UMA VEZ como administrador.
"""

import os
import sys
import winreg
import shutil
from pathlib import Path


def get_pythonw():
    """Encontra o pythonw.exe (python sem console)."""
    python_dir = Path(sys.executable).parent
    pythonw = python_dir / "pythonw.exe"
    if pythonw.exists():
        return str(pythonw)
    # fallback: venv
    pythonw = python_dir / "Scripts" / "pythonw.exe"
    if pythonw.exists():
        return str(pythonw)
    return None


def create_vbs_launcher():
    """
    Cria um .vbs que lança o script sem NENHUMA janela.
    pythonw já não mostra console, mas o .vbs garante 
    que nem flash de janela apareça.
    """
    project_dir = Path(__file__).parent.resolve()
    main_script = project_dir / "main.py"
    vbs_path = project_dir / "launch_hidden.vbs"

    pythonw = get_pythonw()
    if not pythonw:
        print("  ❌ pythonw.exe não encontrado!")
        print("     Instale Python pelo instalador oficial (não pela Store).")
        return None

    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{project_dir}"
WshShell.Run """{pythonw}"" ""{main_script}"" --tray", 0, False
'''

    vbs_path.write_text(vbs_content, encoding="utf-8")
    print(f"  ✅ Launcher criado: {vbs_path}")
    return str(vbs_path)


def add_to_startup_registry(vbs_path: str):
    """Adiciona ao registro do Windows pra iniciar automaticamente."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "SpotifyRGB", 0, winreg.REG_SZ, f'wscript.exe "{vbs_path}"')
        winreg.CloseKey(key)
        print("  ✅ Adicionado à inicialização do Windows")
        return True
    except Exception as e:
        print(f"  ❌ Erro no registro: {e}")
        return False


def remove_from_startup():
    """Remove da inicialização do Windows."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "SpotifyRGB")
        winreg.CloseKey(key)
        print("  ✅ Removido da inicialização")
    except FileNotFoundError:
        print("  ℹ️  Não estava na inicialização")
    except Exception as e:
        print(f"  ❌ Erro: {e}")


def check_status():
    """Verifica se tá configurado."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, "SpotifyRGB")
        winreg.CloseKey(key)
        print(f"  ✅ Ativo na inicialização")
        print(f"     Comando: {value}")
        return True
    except FileNotFoundError:
        print("  ❌ NÃO está na inicialização")
        return False


if __name__ == "__main__":
    print()
    print("=" * 55)
    print("  🎨 SpotifyRGB — Setup de Inicialização")
    print("=" * 55)
    print()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--remove":
            remove_from_startup()
            vbs = Path(__file__).parent / "launch_hidden.vbs"
            if vbs.exists():
                vbs.unlink()
                print("  ✅ Launcher removido")
            sys.exit(0)

        elif sys.argv[1] == "--status":
            check_status()
            sys.exit(0)

    # Verifica pythonw
    pythonw = get_pythonw()
    if not pythonw:
        print("  ❌ pythonw.exe não encontrado!")
        print("     Precisa do Python instalado pelo instalador oficial.")
        sys.exit(1)

    print(f"  📁 Projeto: {Path(__file__).parent.resolve()}")
    print(f"  🐍 Python:  {pythonw}")
    print()

    # Cria launcher
    vbs_path = create_vbs_launcher()
    if not vbs_path:
        sys.exit(1)

    # Adiciona ao startup
    add_to_startup_registry(vbs_path)

    print()
    print("  ─────────────────────────────────────────")
    print("  Pronto! Na próxima vez que ligar o PC,")
    print("  o SpotifyRGB vai iniciar sozinho na")
    print("  bandeja do sistema (system tray).")
    print()
    print("  🔹 Ver status:   python startup_setup.py --status")
    print("  🔹 Desativar:    python startup_setup.py --remove")
    print("  ─────────────────────────────────────────")
    print()