"""
DeskRobo Snipper Engine
Screen captures, window bounding boxes, interactive region drag-crops, and clipboard image extraction.
Optimized for Windows High-DPI scaling and DWM frame bounds.
"""

import os
import datetime
import tkinter as tk
from pathlib import Path
from typing import Optional, Tuple, Callable
from PIL import Image, ImageGrab, ImageTk

from core.config import SCREENSHOTS_DIR
from core.window_tracker import get_window_physical_bounds, get_screen_dimensions

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False


def _safe_screen_grab(bbox: Optional[Tuple[int, int, int, int]] = None) -> Optional[Image.Image]:
    """
    Captures screen using ImageGrab with layered windows support and MSS fallback.
    bbox: (left, top, right, bottom) in physical pixels
    """
    # 1. Try ImageGrab with layered windows support (captures modern transparent UI)
    try:
        if bbox:
            left, top, right, bottom = bbox
            if right > left and bottom > top:
                img = ImageGrab.grab(bbox=(left, top, right, bottom), include_layered_windows=True, all_screens=True)
                if img and img.size[0] > 0 and img.size[1] > 0:
                    return img
        else:
            img = ImageGrab.grab(include_layered_windows=True, all_screens=True)
            if img and img.size[0] > 0 and img.size[1] > 0:
                return img
    except Exception:
        # Fallback to standard ImageGrab without extra flags if needed
        try:
            img = ImageGrab.grab(bbox=bbox)
            if img and img.size[0] > 0 and img.size[1] > 0:
                return img
        except Exception:
            pass

    # 2. Fallback to MSS if ImageGrab fails
    if HAS_MSS:
        try:
            with mss.MSS() as sct:
                if bbox:
                    monitor = {
                        "left": bbox[0],
                        "top": bbox[1],
                        "width": max(1, bbox[2] - bbox[0]),
                        "height": max(1, bbox[3] - bbox[1]),
                    }
                else:
                    # Monitor 0 is the virtual union of all monitors
                    monitor = sct.monitors[0] if len(sct.monitors) > 0 else sct.monitors[1]
                sct_img = sct.grab(monitor)
                return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        except Exception:
            pass

    return None


def capture_active_window(
    rect: Tuple[int, int, int, int],
    hwnd: Optional[int] = None,
    is_desktop: bool = False
) -> Optional[str]:
    """
    Captures the bounding rectangle of the target window and saves it to disk.
    If the target is the desktop, or the window is smaller than 150px (e.g. taskbar),
    it automatically captures full screen instead of a partial strip.
    """
    if is_desktop:
        return capture_fullscreen()

    # If hwnd is provided and valid, refresh physical bounds immediately
    if hwnd:
        try:
            rect = get_window_physical_bounds(hwnd)
        except Exception:
            pass

    left, top, right, bottom = rect
    width = right - left
    height = bottom - top

    # If window is smaller than 150x150 (taskbar, minimized icon, or off-screen), fallback to fullscreen
    if width < 150 or height < 150:
        return capture_fullscreen()

    img = _safe_screen_grab(bbox=(left, top, right, bottom))
    if img:
        return save_screenshot_image(img, prefix="window_snip")

    # If bounding grab failed, fallback to fullscreen
    return capture_fullscreen()


def capture_fullscreen() -> Optional[str]:
    """Captures full screen and saves to disk."""
    img = _safe_screen_grab()
    if img:
        return save_screenshot_image(img, prefix="fullscreen")
    return None


def capture_clipboard_image() -> Optional[str]:
    """Checks if an image is in the Windows clipboard and saves it."""
    try:
        data = ImageGrab.grabclipboard()
        if isinstance(data, Image.Image):
            return save_screenshot_image(data, prefix="clipboard_snip")
    except Exception:
        pass
    return None


def save_screenshot_image(img: Image.Image, prefix: str = "snip") -> str:
    """Saves PIL Image to screenshots directory with timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.png"
    filepath = SCREENSHOTS_DIR / filename
    img.save(filepath, "PNG", optimize=True)
    return str(filepath)


def get_thumbnail_photo(image_path: str, max_size: Tuple[int, int] = (160, 90)) -> Optional[ImageTk.PhotoImage]:
    """Loads and resizes an image for HUD thumbnail display."""
    if not image_path or not Path(image_path).exists():
        return None
    try:
        with Image.open(image_path) as img:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
    except Exception:
        return None


class InteractiveRegionSnipper:
    """
    Full-screen semi-transparent overlay for clicking and dragging a rectangular snip box.
    """
    def __init__(self, on_complete_callback: Callable[[Optional[str]], None]):
        self.on_complete = on_complete_callback
        self.root = tk.Toplevel()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.root.attributes("-topmost", True)
        self.root.config(cursor="cross")

        self.canvas = tk.Canvas(self.root, cursor="cross", bg="gray20", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start_x = 0
        self.start_y = 0
        self.rect_id = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<Escape>", lambda e: self.cancel())

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="#06B6D4", width=2, fill="#06B6D4"
        )

    def on_move_press(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)

        left = int(min(self.start_x, end_x))
        top = int(min(self.start_y, end_y))
        right = int(max(self.start_x, end_x))
        bottom = int(max(self.start_y, end_y))

        # Hide overlay before capturing so there is no gray tint on the screenshot
        self.root.withdraw()
        self.root.update()
        self.root.destroy()

        if (right - left) > 15 and (bottom - top) > 15:
            img = _safe_screen_grab(bbox=(left, top, right, bottom))
            if img:
                saved_path = save_screenshot_image(img, prefix="region_snip")
                self.on_complete(saved_path)
                return

        self.on_complete(None)

    def cancel(self):
        self.root.withdraw()
        self.root.destroy()
        self.on_complete(None)
