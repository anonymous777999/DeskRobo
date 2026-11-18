"""
DeskRobo System Tray Integration
Background daemon tray icon with quick actions, Windows autostart toggle, and exit handlers.
"""

import os
import threading
from typing import Callable
from PIL import Image, ImageDraw
import pystray

from core.config import NOTES_DIR
from core.autostart import is_autostart_enabled, toggle_autostart


def create_robot_tray_image() -> Image.Image:
    """Generates a 64x64 cute robot tray icon dynamically."""
    size = (64, 64)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Antenna stem & glowing cyan tip
    draw.line([(32, 16), (32, 6)], fill="#6366F1", width=3)
    draw.ellipse([(28, 2), (36, 10)], fill="#06B6D4", outline="#22D3EE", width=1)

    # Robot Head
    draw.rounded_rectangle([(10, 14), (54, 56)], radius=12, fill="#1E2235", outline="#4F46E5", width=3)

    # Visor Screen
    draw.rounded_rectangle([(16, 22), (48, 48)], radius=6, fill="#0B0D14", outline="#1E293B", width=1)

    # Glowing Cyan Eyes
    draw.ellipse([(20, 29), (28, 37)], fill="#06B6D4")
    draw.ellipse([(36, 29), (44, 37)], fill="#06B6D4")

    # Eye sparkles
    draw.ellipse([(24, 31), (27, 34)], fill="#FFFFFF")
    draw.ellipse([(40, 31), (43, 34)], fill="#FFFFFF")

    return img


class TrayIconManager:
    def __init__(
        self,
        on_summon: Callable[[], None],
        on_archive: Callable[[], None],
        on_exit: Callable[[], None]
    ):
        self.on_summon = on_summon
        self.on_archive = on_archive
        self.on_exit = on_exit
        self.icon = None

    def open_folder(self):
        os.startfile(str(NOTES_DIR))

    def on_toggle_autostart(self, icon, item):
        """Toggles Windows startup shortcut and updates menu checkbox."""
        toggle_autostart()
        if self.icon:
            self.icon.update_menu()

    def run(self):
        image = create_robot_tray_image()
        menu = pystray.Menu(
            pystray.MenuItem("🤖 Summon DeskRobo (Alt+Q / Alt+N)", lambda icon, item: self.on_summon(), default=True),
            pystray.MenuItem("📚 View Notes Archive (Ctrl+H)", lambda icon, item: self.on_archive()),
            pystray.MenuItem("📁 Open Notes Folder", lambda icon, item: self.open_folder()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "🚀 Run on Windows Startup",
                self.on_toggle_autostart,
                checked=lambda item: is_autostart_enabled()
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Exit DeskRobo", lambda icon, item: self.on_exit())
        )
        self.icon = pystray.Icon("DeskRobo", image, "DeskRobo — Desktop Companion", menu)
        self.icon.run()

    def stop(self):
        if self.icon:
            self.icon.stop()
