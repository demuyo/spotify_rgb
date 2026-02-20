@echo off
echo Removendo auto-start...

set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup

del /Q "%STARTUP_FOLDER%\SpotifyRGBSync.vbs" 2>nul

echo.
echo Auto-start removido!
pause