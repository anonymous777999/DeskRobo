"""
DeskRobo Autostart Manager
Configures Windows Startup shortcut so DeskRobo runs silently in the background on system boot.
"""

import os
from pathlib import Path

STARTUP_DIR = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
SHORTCUT_PATH = STARTUP_DIR / "DeskRobo.lnk"
TARGET_VBS = Path("D:/DeskRobo/launch_silent.vbs").resolve()


def is_autostart_enabled() -> bool:
    """Returns True if the DeskRobo shortcut exists in the Windows Startup directory."""
    return SHORTCUT_PATH.exists()


def enable_autostart() -> bool:
    """Creates a Windows Startup shortcut pointing to launch_silent.vbs."""
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(str(SHORTCUT_PATH))
        shortcut.TargetPath = str(TARGET_VBS)
        shortcut.WorkingDirectory = str(TARGET_VBS.parent)
        shortcut.Description = "DeskRobo — Desktop Bug & Note Companion"
        shortcut.Save()
        return True
    except Exception as e:
        # Fallback to PowerShell shortcut creation
        try:
            cmd = (
                f'$ws = New-Object -ComObject WScript.Shell; '
                f'$s = $ws.CreateShortcut("{SHORTCUT_PATH}"); '
                f'$s.TargetPath = "{TARGET_VBS}"; '
                f'$s.WorkingDirectory = "{TARGET_VBS.parent}"; '
                f'$s.Description = "DeskRobo"; '
                f'$s.Save()'
            )
            os.system(f'powershell -Command "{cmd}"')
            return SHORTCUT_PATH.exists()
        except Exception:
            return False


def disable_autostart() -> bool:
    """Removes the DeskRobo shortcut from Windows Startup."""
    try:
        if SHORTCUT_PATH.exists():
            SHORTCUT_PATH.unlink()
        return True
    except Exception:
        return False


def toggle_autostart() -> bool:
    """Toggles Windows Startup state and returns the new state."""
    if is_autostart_enabled():
        disable_autostart()
        return False
    else:
        enable_autostart()
        return True

