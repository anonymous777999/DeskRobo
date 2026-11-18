"""
DeskRobo Configuration & Constants
Sleek cyberpunk dark-glass aesthetic, multi-key hotkeys, and geometry settings.
"""

import os
from pathlib import Path

# Paths
BASE_DIR = Path("D:/DeskRobo").resolve()
DATA_DIR = BASE_DIR / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
NOTES_DIR = BASE_DIR / "notes"
ASSETS_DIR = BASE_DIR / "assets"
DB_PATH = DATA_DIR / "deskrobo.db"

# Ensure directories exist
for directory in [DATA_DIR, SCREENSHOTS_DIR, NOTES_DIR, ASSETS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Multiple Global Hotkeys (Super fast 1-hand Alt+Q, intuitive Alt+N, or classic Ctrl+Alt+N)
GLOBAL_HOTKEYS = [
    "<alt>+q",
    "<alt>+n",
    "<ctrl>+<alt>+n",
]
HOTKEY_DISPLAY_NAME = "Alt + Q  or  Alt + N"

# Auto-dismiss countdown in seconds (when pristine/idle)
AUTO_DISMISS_SECONDS = 8

# Window geometry (spacious, ultra-modern card)
HUD_WIDTH = 490
HUD_HEIGHT = 460

# Modern Cyberpunk Dark-Glass Color Palette
COLORS = {
    "bg_dark": "#0B0F19",            # Deep Obsidian
    "bg_card": "#0F172A",            # Rich Slate Glass
    "bg_input": "#131C2E",           # Input Container
    "bg_hover": "#223048",           # Hover State
    "border_subtle": "#243247",      # Subtle Slate Divider
    "border_glow": "#334155",        # Clean Modern Slate Border
    "border_active": "#06B6D4",      # Electric Cyan Focus
    "accent_cyan": "#06B6D4",        # Neon Cyber Cyan
    "accent_pink": "#EC4899",        # Neon Pink
    "accent_green": "#10B981",       # Emerald Green
    "accent_amber": "#F59E0B",       # Vivid Amber
    "accent_indigo": "#6366F1",      # Electric Indigo
    "accent_rose": "#F43F5E",        # Crimson Rose
    "text_main": "#F8FAFC",          # Pure Crisp White
    "text_dim": "#CBD5E1",           # Soft Silver
    "text_muted": "#64748B",         # Steel Muted Gray
    "btn_primary": "#4F46E5",        # Indigo Primary
    "btn_primary_hover": "#6366F1",  # Lighter Indigo
    "btn_secondary": "#1E293B",      # Card Button
    "btn_secondary_hover": "#334155",# Card Button Hover
    "tag_bug": "#F43F5E",
    "tag_idea": "#F59E0B",
    "tag_todo": "#10B981",
    "tag_note": "#06B6D4",
}

# Tag Definitions with Keyboard Shortcuts (Alt+1..4)
TAGS = [
    {"id": "bug", "label": "🐛 Bug", "shortcut": "1", "color": COLORS["tag_bug"]},
    {"id": "idea", "label": "💡 Idea", "shortcut": "2", "color": COLORS["tag_idea"]},
    {"id": "todo", "label": "✅ Todo", "shortcut": "3", "color": COLORS["tag_todo"]},
    {"id": "note", "label": "📝 Note", "shortcut": "4", "color": COLORS["tag_note"]},
]
