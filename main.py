"""
DeskRobo — Desktop Companion & Instant Bug/Note HUD
Main Entry Point
"""

import sys
import ctypes
import threading
import tkinter as tk
from pynput import keyboard

from core.config import GLOBAL_HOTKEYS, HOTKEY_DISPLAY_NAME
from core.storage import StorageManager
from core.robot_hud import RobotHUD
from core.archive_viewer import ArchiveViewer
from core.tray import TrayIconManager

# Enable Per-Monitor High DPI awareness on Windows (Mode 2 = Per-Monitor v2, 1 = System)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class DeskRoboApp:
    def __init__(self):
        # Master Tkinter root (remains hidden as event controller)
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("DeskRobo Daemon")

        # Core Services
        self.storage = StorageManager()

        # UI Components
        self.archive_viewer = ArchiveViewer(self.root, self.storage)
        self.hud = RobotHUD(self.root, self.storage, on_open_archive=self.show_archive)

        # Multi-key Global Hotkey Listener (Alt+Q, Alt+N, Ctrl+Alt+N)
        hotkey_map = {hk: self.trigger_summon for hk in GLOBAL_HOTKEYS}
        self.hotkey_listener = keyboard.GlobalHotKeys(hotkey_map)
        self.hotkey_listener.start()

        # System Tray Daemon
        self.tray = TrayIconManager(
            on_summon=self.trigger_summon,
            on_archive=self.show_archive,
            on_exit=self.quit_app
        )
        self.tray_thread = threading.Thread(target=self.tray.run, daemon=True)
        self.tray_thread.start()

        print(f"🤖 DeskRobo is running! Press {HOTKEY_DISPLAY_NAME} to summon.")

    def trigger_summon(self):
        """Thread-safe callback to summon the HUD."""
        self.root.after(0, self._summon_on_main_thread)

    def _summon_on_main_thread(self):
        if self.hud.is_visible:
            # If already visible, focus it or reset timer
            self.hud.win.lift()
            self.hud.win.focus_force()
        else:
            self.hud.summon()

    def show_archive(self):
        """Thread-safe callback to display notes archive."""
        self.root.after(0, self.archive_viewer.show)

    def quit_app(self):
        """Clean shutdown of all threads and listeners."""
        print("🤖 DeskRobo shutting down. Goodbye!")
        try:
            self.hotkey_listener.stop()
        except Exception:
            pass

        try:
            self.tray.stop()
        except Exception:
            pass

        self.root.after(0, self.root.destroy)
        sys.exit(0)

    def run(self):
        """Starts the Tkinter main event loop."""
        self.root.mainloop()


if __name__ == "__main__":
    app = DeskRoboApp()
    app.run()
