"""
Automated unit tests for DeskRobo Window Tracker and Snipper Engine.
"""

import os
import sys
import unittest
from pathlib import Path
from PIL import Image

# Ensure DeskRobo root is in python path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.window_tracker import (
    get_screen_dimensions,
    get_window_physical_bounds,
    is_valid_user_window,
    find_active_target_window,
    get_foreground_window_info,
)
from core.snipper import (
    save_screenshot_image,
    capture_active_window,
    capture_clipboard_image,
)
from core.config import SCREENSHOTS_DIR


class TestWindowTrackerAndSnipper(unittest.TestCase):
    def test_screen_dimensions(self):
        sw, sh = get_screen_dimensions()
        self.assertGreater(sw, 500)
        self.assertGreater(sh, 400)

    def test_invalid_window_bounds_fallback(self):
        # Handle 0 should fallback to full screen bounds
        bounds = get_window_physical_bounds(0)
        self.assertEqual(bounds[0], 0)
        self.assertEqual(bounds[1], 0)
        self.assertGreater(bounds[2], 500)
        self.assertGreater(bounds[3], 400)

    def test_is_valid_user_window(self):
        # 0 is not a valid window
        self.assertFalse(is_valid_user_window(0))
        # 9999999 is not a valid window
        self.assertFalse(is_valid_user_window(9999999))

    def test_find_active_target_window_returns_tuple(self):
        hwnd, is_desktop = find_active_target_window()
        self.assertIsInstance(hwnd, int)
        self.assertIsInstance(is_desktop, bool)

    def test_get_foreground_window_info(self):
        info = get_foreground_window_info()
        self.assertIn("hwnd", info)
        self.assertIn("title", info)
        self.assertIn("app_name", info)
        self.assertIn("rect", info)
        self.assertIn("is_desktop", info)
        self.assertEqual(len(info["rect"]), 4)

    def test_save_screenshot_image(self):
        test_img = Image.new("RGB", (200, 200), color=(6, 182, 212))
        saved_path = save_screenshot_image(test_img, prefix="test_snip")
        self.assertTrue(os.path.exists(saved_path))
        self.assertTrue(saved_path.endswith(".png"))
        
        # Verify saved image properties
        with Image.open(saved_path) as img:
            self.assertEqual(img.size, (200, 200))
            
        # Clean up test file
        try:
            os.remove(saved_path)
        except Exception:
            pass

    def test_small_rect_does_not_capture_strip(self):
        # A tiny 60px strip (like a taskbar) should never be captured as-is;
        # capture_active_window must fallback to capture_fullscreen() or return None if headless
        tiny_rect = (0, 1020, 1920, 1080) # 60px height
        # In session 0 screen grab returns None gracefully rather than writing a 60px file
        path = capture_active_window(rect=tiny_rect, is_desktop=False)
        if path:
            with Image.open(path) as img:
                self.assertNotEqual(img.size[1], 60)
            try:
                os.remove(path)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
