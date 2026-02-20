Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\nessy\Desktop\spotify_rgb"
WshShell.Run """C:\Users\nessy\Desktop\spotify_rgb\.venv\Scripts\pythonw.exe"" ""C:\Users\nessy\Desktop\spotify_rgb\main.py"" ", 0, False
