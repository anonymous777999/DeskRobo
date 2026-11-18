"""
DeskRobo Window Tracker
Captures foreground window metadata (title, process, geometry) with DWM physical bounds and Z-order resolution.
"""

import os
import ctypes
from ctypes import wintypes
from typing import Dict, Any, Tuple

try:
    import win32gui
    import win32process
    import win32api
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

DWMWA_EXTENDED_FRAME_BOUNDS = 9


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


IGNORED_CLASSES = {
    "Shell_TrayWnd",
    "Shell_SecondaryTrayWnd",
    "Progman",
    "WorkerW",
    "NotifyIconOverflowWindow",
    "Windows.UI.Core.CoreWindow",
    "ApplicationFrameWindow_Ghost",
}

IGNORED_TITLES = {
    "DeskRobo HUD",
    "DeskRobo Daemon",
    "",
}


def get_screen_dimensions() -> Tuple[int, int]:
    """Returns physical screen dimensions in pixels."""
    try:
        sw = ctypes.windll.user32.GetSystemMetrics(0)
        sh = ctypes.windll.user32.GetSystemMetrics(1)
        if sw > 0 and sh > 0:
            return (sw, sh)
    except Exception:
        pass
    return (1920, 1080)


def get_window_physical_bounds(hwnd: int) -> Tuple[int, int, int, int]:
    """
    Returns the real physical screen rectangle (left, top, right, bottom)
    using DWM Extended Frame Bounds, which removes invisible DWM drop shadows
    and accurately aligns with physical pixels across all Windows DPI scale factors.
    """
    sw, sh = get_screen_dimensions()
    fallback_rect = (0, 0, sw, sh)

    if not HAS_WIN32 or not hwnd or not win32gui.IsWindow(hwnd):
        return fallback_rect

    # Try DWM physical extended frame bounds (accurate physical pixels)
    rect = RECT()
    try:
        res = ctypes.windll.dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(hwnd),
            wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
            ctypes.byref(rect),
            ctypes.sizeof(rect),
        )
        if res == 0:
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            if w > 50 and h > 50:
                # Clamp to screen boundary
                left = max(0, rect.left)
                top = max(0, rect.top)
                right = min(sw, rect.right)
                bottom = min(sh, rect.bottom)
                return (left, top, right, bottom)
    except Exception:
        pass

    # Fallback to win32gui.GetWindowRect
    try:
        r = win32gui.GetWindowRect(hwnd)
        left = max(0, r[0])
        top = max(0, r[1])
        right = min(sw, r[2])
        bottom = min(sh, r[3])
        return (left, top, right, bottom)
    except Exception:
        return fallback_rect


def is_valid_user_window(hwnd: int) -> bool:
    """Checks whether hwnd is an actual interactive user application window."""
    if not HAS_WIN32 or not hwnd or not win32gui.IsWindow(hwnd):
        return False
    if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
        return False

    try:
        cls = win32gui.GetClassName(hwnd)
        if cls in IGNORED_CLASSES:
            return False

        title = win32gui.GetWindowText(hwnd).strip()
        if title in IGNORED_TITLES:
            return False

        rect = get_window_physical_bounds(hwnd)
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]

        # Ignore tiny taskbar strips, off-screen hidden windows, or tooltips
        if width < 150 or height < 150:
            return False

        return True
    except Exception:
        return False


def find_active_target_window() -> Tuple[int, bool]:
    """
    Finds the active application window.
    If the immediate foreground window is the Taskbar, Desktop, or DeskRobo itself,
    walks down the Z-order to find the topmost underlying user application.
    Returns: (hwnd, is_desktop)
    """
    if not HAS_WIN32:
        return (0, True)

    try:
        fg = win32gui.GetForegroundWindow()
        if is_valid_user_window(fg):
            return (fg, False)

        # Foreground is Taskbar/Desktop/Tray. Walk down Z-order from fg
        curr = win32gui.GetWindow(fg, win32con.GW_HWNDNEXT) if fg else None
        if not curr:
            curr = win32gui.GetTopWindow(win32gui.GetDesktopWindow())

        visited = set()
        while curr and curr not in visited:
            visited.add(curr)
            if is_valid_user_window(curr):
                return (curr, False)
            curr = win32gui.GetWindow(curr, win32con.GW_HWNDNEXT)

        # If no user app window is found in Z-order, it is the desktop
        return (0, True)
    except Exception:
        return (0, True)


def get_foreground_window_info() -> Dict[str, Any]:
    """
    Returns metadata about the active application window before DeskRobo was summoned.
    """
    sw, sh = get_screen_dimensions()
    screen_rect = (0, 0, sw, sh)

    default_info = {
        "hwnd": 0,
        "title": "Desktop / Full Screen",
        "app_name": "Desktop",
        "pid": 0,
        "rect": screen_rect,
        "is_desktop": True,
    }

    if not HAS_WIN32:
        return default_info

    try:
        hwnd, is_desktop = find_active_target_window()
        if is_desktop or not hwnd:
            return default_info

        title = win32gui.GetWindowText(hwnd).strip() or "Active Window"

        # Get Process ID and executable name
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        app_name = "Unknown"
        if pid:
            try:
                handle = win32api.OpenProcess(
                    win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ,
                    False,
                    pid,
                )
                if handle:
                    exe_path = win32process.GetModuleFileNameEx(handle, 0)
                    app_name = os.path.basename(exe_path)
                    win32api.CloseHandle(handle)
            except Exception:
                app_name = f"Process-{pid}"

        rect = get_window_physical_bounds(hwnd)

        return {
            "hwnd": hwnd,
            "title": title,
            "app_name": app_name,
            "pid": pid,
            "rect": rect,
            "is_desktop": False,
        }
    except Exception:
        return default_info
