' startup.vbs
' Inicia o Spotify RGB Sync silenciosamente (sem janela de console)

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Usa pythonw.exe (sem console)
WshShell.Run "pythonw.exe main.py", 0, False

Set WshShell = Nothing