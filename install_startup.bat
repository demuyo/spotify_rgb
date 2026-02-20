@echo off
echo ========================================
echo  Spotify RGB Sync - Instalador
echo ========================================
echo.

:: Pega o caminho atual
set SCRIPT_DIR=%~dp0
set VBS_FILE=%SCRIPT_DIR%startup.vbs

:: Caminho da pasta Startup do Windows
set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

:: Cria atalho na pasta Startup
echo Instalando auto-start...

:: Cria o arquivo .vbs se não existir
if not exist "%VBS_FILE%" (
    echo Set WshShell = CreateObject^("WScript.Shell"^) > "%VBS_FILE%"
    echo WshShell.CurrentDirectory = "%SCRIPT_DIR%" >> "%VBS_FILE%"
    echo WshShell.Run "pythonw.exe main.py", 0, False >> "%VBS_FILE%"
    echo Set WshShell = Nothing >> "%VBS_FILE%"
)

:: Copia pra Startup
copy /Y "%VBS_FILE%" "%STARTUP_FOLDER%\SpotifyRGBSync.vbs" >nul

if %ERRORLEVEL% == 0 (
    echo.
    echo ========================================
    echo  SUCESSO!
    echo ========================================
    echo.
    echo O programa vai iniciar automaticamente
    echo com o Windows.
    echo.
    echo Para remover: delete o arquivo
    echo %STARTUP_FOLDER%\SpotifyRGBSync.vbs
    echo.
) else (
    echo.
    echo ERRO: Nao foi possivel instalar.
    echo Tente rodar como Administrador.
)

pause