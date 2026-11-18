' DeskRobo Silent Background Launcher
' Runs DeskRobo as a pure background daemon (0 black console windows, 0 taskbar buttons)
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

WshShell.CurrentDirectory = "D:\DeskRobo"

' Use system pythonw.exe or standard Python310 path
pythonwPath = "pythonw.exe"
If fso.FileExists("C:\Program Files\Python310\pythonw.exe") Then
    pythonwPath = """C:\Program Files\Python310\pythonw.exe"""
End If

WshShell.Run pythonwPath & " main.py", 0, False
