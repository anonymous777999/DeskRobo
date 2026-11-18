"""
DeskRobo HUD Window
The floating, animated, auto-dismissing desktop companion card.
Redesigned with a sleek cyberpunk dark-glass aesthetic, game-HUD progress bar, and instant hotkeys.
"""

import os
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from typing import Optional, Callable
from PIL import Image

from core.config import (
    HUD_WIDTH, HUD_HEIGHT, COLORS, TAGS,
    AUTO_DISMISS_SECONDS, HOTKEY_DISPLAY_NAME
)
from core.robot_canvas import RobotCanvas
from core.window_tracker import get_foreground_window_info
from core.storage import StorageManager
from core.snipper import (
    capture_active_window, capture_fullscreen, capture_clipboard_image,
    get_thumbnail_photo, InteractiveRegionSnipper
)


class RobotHUD:
    def __init__(self, root: tk.Tk, storage: StorageManager, on_open_archive: Callable[[], None]):
        self.root = root
        self.storage = storage
        self.on_open_archive = on_open_archive

        # State
        self.is_visible = False
        self.active_context = {}
        self.selected_tag = "note"
        self.attached_screenshot: Optional[str] = None
        self.thumbnail_photo = None
        self.countdown_remaining = float(AUTO_DISMISS_SECONDS)
        self.is_timer_frozen = False
        self._countdown_job = None
        self.is_saving = False
        self.has_placeholder = True
        self.placeholder_text = "What did you notice? Describe symptoms, error stack, or ideas..."

        # Window creation
        self.win = tk.Toplevel(self.root)
        self.win.withdraw()  # Start hidden
        self.win.overrideredirect(True)  # Frameless sleek floating HUD
        self.win.attributes("-topmost", True)
        self.win.configure(bg=COLORS["border_glow"])

        # Drag tracking
        self.drag_x = 0
        self.drag_y = 0

        self.setup_ui()
        self.bind_shortcuts()

    def setup_ui(self):
        # Outer Glowing Border Wrapper (1px sharp outline)
        self.card = tk.Frame(self.win, bg=COLORS["bg_card"], padx=16, pady=14)
        self.card.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        # -------------------------------------------------------------
        # 1. Header Frame (Mascot + Title + Status Badges + Close)
        # -------------------------------------------------------------
        header_frame = tk.Frame(self.card, bg=COLORS["bg_card"])
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Drag handler on header
        header_frame.bind("<ButtonPress-1>", self.start_drag)
        header_frame.bind("<B1-Motion>", self.do_drag)

        # Cute Animated Robot Mascot Avatar
        self.robot = RobotCanvas(header_frame, size=68, bg=COLORS["bg_card"])
        self.robot.pack(side=tk.LEFT, padx=(0, 12))

        # Mascot Speech Bubble & Title Bar
        bubble_frame = tk.Frame(header_frame, bg=COLORS["bg_card"])
        bubble_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        title_row = tk.Frame(bubble_frame, bg=COLORS["bg_card"])
        title_row.pack(anchor="w", fill=tk.X)

        self.title_label = tk.Label(
            title_row,
            text="DeskRobo",
            font=("Segoe UI", 13, "bold"),
            fg=COLORS["text_main"],
            bg=COLORS["bg_card"]
        )
        self.title_label.pack(side=tk.LEFT, padx=(0, 8))

        # Status Pill: ● ACTIVE
        self.status_pill = tk.Label(
            title_row,
            text="● ACTIVE",
            font=("Segoe UI", 7, "bold"),
            fg=COLORS["accent_green"],
            bg="#064E3B",
            padx=6,
            pady=1
        )
        self.status_pill.pack(side=tk.LEFT, padx=(0, 6))

        # Hotkey Reminder Pill
        self.hotkey_pill = tk.Label(
            title_row,
            text="Alt+Q",
            font=("Segoe UI", 7, "bold"),
            fg=COLORS["accent_cyan"],
            bg=COLORS["bg_input"],
            padx=6,
            pady=1
        )
        self.hotkey_pill.pack(side=tk.LEFT)

        # Dynamic Responsive Speech Label
        self.speech_label = tk.Label(
            bubble_frame,
            text="Bleep! Ready to capture your thoughts or bugs...",
            font=("Segoe UI", 9),
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"],
            anchor="w"
        )
        self.speech_label.pack(anchor="w", pady=(3, 0))

        # Close '✕' Button
        close_btn = tk.Label(
            header_frame,
            text="✕",
            font=("Segoe UI", 11, "bold"),
            fg=COLORS["text_muted"],
            bg=COLORS["bg_input"],
            padx=7,
            pady=2,
            cursor="hand2"
        )
        close_btn.pack(side=tk.RIGHT, anchor="ne")
        close_btn.bind("<Button-1>", lambda e: self.hide())
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg=COLORS["accent_rose"], fg="#FFFFFF"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg=COLORS["bg_input"], fg=COLORS["text_muted"]))

        # -------------------------------------------------------------
        # 2. Active Window Context Pill (Terminal Badge Style)
        # -------------------------------------------------------------
        self.context_frame = tk.Frame(self.card, bg=COLORS["bg_input"], padx=10, pady=5)
        self.context_frame.pack(fill=tk.X, pady=(0, 10))

        self.context_icon = tk.Label(
            self.context_frame,
            text="🎯",
            font=("Segoe UI", 9),
            bg=COLORS["bg_input"]
        )
        self.context_icon.pack(side=tk.LEFT, padx=(0, 6))

        self.context_badge = tk.Label(
            self.context_frame,
            text="Target: Desktop / Full Screen",
            font=("Segoe UI", 8, "bold"),
            fg=COLORS["accent_cyan"],
            bg=COLORS["bg_input"],
            anchor="w"
        )
        self.context_badge.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # -------------------------------------------------------------
        # 3. Interactive Tag Selector Pills (Alt+1..4)
        # -------------------------------------------------------------
        tag_frame = tk.Frame(self.card, bg=COLORS["bg_card"])
        tag_frame.pack(fill=tk.X, pady=(0, 10))

        self.tag_buttons = {}
        for tag in TAGS:
            btn = tk.Label(
                tag_frame,
                text=f"{tag['label']} ({tag['shortcut']})",
                font=("Segoe UI", 8, "bold"),
                fg=COLORS["text_dim"],
                bg=COLORS["bg_input"],
                padx=11,
                pady=5,
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=(0, 6))
            btn.bind("<Button-1>", lambda e, t=tag["id"]: self.select_tag(t))
            btn.bind("<Enter>", lambda e, b=btn, t=tag["id"]: self.on_tag_hover(b, t, True))
            btn.bind("<Leave>", lambda e, b=btn, t=tag["id"]: self.on_tag_hover(b, t, False))
            self.tag_buttons[tag["id"]] = btn

        self.update_tag_styles()

        # -------------------------------------------------------------
        # 4. Multi-line Note Input Area with Interactive Placeholder
        # -------------------------------------------------------------
        self.text_container = tk.Frame(self.card, bg=COLORS["border_subtle"], padx=1, pady=1)
        self.text_container.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.text_area = tk.Text(
            self.text_container,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            fg=COLORS["text_muted"],
            bg=COLORS["bg_input"],
            insertbackground=COLORS["accent_cyan"],
            relief=tk.FLAT,
            padx=10,
            pady=8,
            height=6
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)
        self.text_area.insert("1.0", self.placeholder_text)
        self.text_area.bind("<FocusIn>", self.on_text_focus_in)
        self.text_area.bind("<FocusOut>", self.on_text_focus_out)
        self.text_area.bind("<Key>", self.on_typing)
        self.text_area.bind("<Control-v>", self.on_paste_shortcut)
        self.text_area.bind("<Control-V>", self.on_paste_shortcut)

        # -------------------------------------------------------------
        # 5. Screenshot Thumbnail Preview Bar (Hidden initially)
        # -------------------------------------------------------------
        self.preview_bar = tk.Frame(self.card, bg=COLORS["bg_input"], padx=8, pady=6)
        
        self.thumbnail_label = tk.Label(self.preview_bar, bg=COLORS["bg_input"], cursor="hand2")
        self.thumbnail_label.pack(side=tk.LEFT, padx=(0, 10))
        self.thumbnail_label.bind("<Button-1>", lambda e: self.open_attached_image())

        preview_text_frame = tk.Frame(self.preview_bar, bg=COLORS["bg_input"])
        preview_text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.preview_info = tk.Label(
            preview_text_frame,
            text="📸 Screenshot Attached",
            font=("Segoe UI", 9, "bold"),
            fg=COLORS["accent_green"],
            bg=COLORS["bg_input"],
            anchor="w"
        )
        self.preview_info.pack(anchor="w")

        self.preview_hint = tk.Label(
            preview_text_frame,
            text="Click thumbnail to preview in full resolution",
            font=("Segoe UI", 7),
            fg=COLORS["text_muted"],
            bg=COLORS["bg_input"],
            anchor="w"
        )
        self.preview_hint.pack(anchor="w")

        remove_thumb_btn = tk.Label(
            self.preview_bar,
            text="✕ Remove",
            font=("Segoe UI", 8, "bold"),
            fg=COLORS["accent_rose"],
            bg=COLORS["bg_input"],
            padx=8,
            pady=4,
            cursor="hand2"
        )
        remove_thumb_btn.pack(side=tk.RIGHT)
        remove_thumb_btn.bind("<Button-1>", lambda e: self.remove_screenshot())
        remove_thumb_btn.bind("<Enter>", lambda e: remove_thumb_btn.config(fg="#FFFFFF", bg=COLORS["accent_rose"]))
        remove_thumb_btn.bind("<Leave>", lambda e: remove_thumb_btn.config(fg=COLORS["accent_rose"], bg=COLORS["bg_input"]))

        # -------------------------------------------------------------
        # 6. Action Toolbar (Window, Full, Crop, Paste, History)
        # -------------------------------------------------------------
        action_bar = tk.Frame(self.card, bg=COLORS["bg_card"])
        action_bar.pack(fill=tk.X, pady=(2, 10))

        # Snip Active Window button (Alt+W)
        self.snip_win_btn = self._create_action_btn(
            action_bar, "📸 Window", "Alt+W", lambda e: self.do_snip_window()
        )
        self.snip_win_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Full Screen Snip button (Alt+F)
        self.snip_full_btn = self._create_action_btn(
            action_bar, "🖥️ Full", "Alt+F", lambda e: self.do_snip_fullscreen()
        )
        self.snip_full_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Drag Region Snip button (Alt+C)
        self.snip_crop_btn = self._create_action_btn(
            action_bar, "✂ Crop", "Alt+C", lambda e: self.do_drag_crop()
        )
        self.snip_crop_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Paste Image from Clipboard button (Ctrl+V)
        self.paste_img_btn = self._create_action_btn(
            action_bar, "📋 Paste", "Ctrl+V", lambda e: self.do_paste_image()
        )
        self.paste_img_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Open Archive Button (Ctrl+H)
        self.archive_btn = self._create_action_btn(
            action_bar, "📚 History", "Ctrl+H", lambda e: self.open_archive(), is_accent=False
        )
        self.archive_btn.pack(side=tk.RIGHT)

        # -------------------------------------------------------------
        # 7. Real-Time Visual Progress Bar (Cyberpunk Game HUD Style)
        # -------------------------------------------------------------
        self.progress_canvas = tk.Canvas(
            self.card,
            height=4,
            bg=COLORS["bg_input"],
            highlightthickness=0
        )
        self.progress_canvas.pack(fill=tk.X, pady=(0, 8))

        # -------------------------------------------------------------
        # 8. Bottom Bar: Save Button + Countdown Status Label
        # -------------------------------------------------------------
        bottom_bar = tk.Frame(self.card, bg=COLORS["bg_card"])
        bottom_bar.pack(fill=tk.X)

        self.save_btn = tk.Label(
            bottom_bar,
            text="💾 Save Note  Ctrl+Enter",
            font=("Segoe UI", 9, "bold"),
            fg="#FFFFFF",
            bg=COLORS["btn_primary"],
            padx=16,
            pady=7,
            cursor="hand2"
        )
        self.save_btn.pack(side=tk.RIGHT)
        self.save_btn.bind("<Button-1>", lambda e: self.save_current_note())
        self.save_btn.bind("<Enter>", lambda e: self.save_btn.config(bg=COLORS["btn_primary_hover"]))
        self.save_btn.bind("<Leave>", lambda e: self.save_btn.config(bg=COLORS["btn_primary"]))

        # Status text below timer
        self.countdown_label = tk.Label(
            bottom_bar,
            text=f"Auto-closing in {int(self.countdown_remaining)}s (Type to keep)",
            font=("Segoe UI", 8),
            fg=COLORS["text_muted"],
            bg=COLORS["bg_card"]
        )
        self.countdown_label.pack(side=tk.LEFT, anchor="w")

    def _create_action_btn(self, parent, text, shortcut, command, is_accent=False):
        """Creates a styled action button with subtle hover elevation."""
        btn = tk.Label(
            parent,
            text=f"{text}",
            font=("Segoe UI", 8),
            fg=COLORS["text_main"],
            bg=COLORS["btn_secondary"],
            padx=8,
            pady=5,
            cursor="hand2"
        )
        btn.bind("<Button-1>", command)
        btn.bind("<Enter>", lambda e: btn.config(bg=COLORS["btn_secondary_hover"], fg="#FFFFFF"))
        btn.bind("<Leave>", lambda e: btn.config(bg=COLORS["btn_secondary"], fg=COLORS["text_main"]))
        return btn

    def bind_shortcuts(self):
        """Binds keyboard shortcuts within the HUD."""
        self.win.bind("<Escape>", lambda e: self.hide())
        self.win.bind("<Control-Return>", lambda e: self.save_current_note())
        self.win.bind("<Control-h>", lambda e: self.open_archive())
        self.win.bind("<Control-H>", lambda e: self.open_archive())
        
        # Tag shortcuts (Alt+1..4)
        self.win.bind("<Alt-Key-1>", lambda e: self.select_tag("bug"))
        self.win.bind("<Alt-Key-2>", lambda e: self.select_tag("idea"))
        self.win.bind("<Alt-Key-3>", lambda e: self.select_tag("todo"))
        self.win.bind("<Alt-Key-4>", lambda e: self.select_tag("note"))

        # Snip shortcuts (Alt+W, Alt+F, Alt+C)
        self.win.bind("<Alt-w>", lambda e: self.do_snip_window())
        self.win.bind("<Alt-W>", lambda e: self.do_snip_window())
        self.win.bind("<Alt-f>", lambda e: self.do_snip_fullscreen())
        self.win.bind("<Alt-F>", lambda e: self.do_snip_fullscreen())
        self.win.bind("<Alt-c>", lambda e: self.do_drag_crop())
        self.win.bind("<Alt-C>", lambda e: self.do_drag_crop())

    def start_drag(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def do_drag(self, event):
        x = self.win.winfo_x() + (event.x - self.drag_x)
        y = self.win.winfo_y() + (event.y - self.drag_y)
        self.win.geometry(f"+{x}+{y}")
        self.freeze_timer()

    def select_tag(self, tag_id: str):
        self.selected_tag = tag_id
        self.update_tag_styles()
        self.freeze_timer()

    def update_tag_styles(self):
        tag_map = {t["id"]: t for t in TAGS}
        for tid, btn in self.tag_buttons.items():
            if tid == self.selected_tag:
                active_color = tag_map[tid]["color"]
                btn.config(bg=active_color, fg="#FFFFFF")
            else:
                btn.config(bg=COLORS["bg_input"], fg=COLORS["text_dim"])

    def on_tag_hover(self, btn, tag_id, is_hover):
        if tag_id != self.selected_tag:
            if is_hover:
                btn.config(bg=COLORS["bg_hover"], fg="#FFFFFF")
            else:
                btn.config(bg=COLORS["bg_input"], fg=COLORS["text_dim"])

    def on_text_focus_in(self, event=None):
        self.text_container.config(bg=COLORS["border_active"])
        if self.has_placeholder:
            self.text_area.delete("1.0", tk.END)
            self.text_area.config(fg=COLORS["text_main"])
            self.has_placeholder = False
        self.freeze_timer()

    def on_text_focus_out(self, event=None):
        self.text_container.config(bg=COLORS["border_subtle"])
        content = self.text_area.get("1.0", tk.END).strip()
        if not content:
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert("1.0", self.placeholder_text)
            self.text_area.config(fg=COLORS["text_muted"])
            self.has_placeholder = True

    def on_typing(self, event=None):
        """Called whenever the user types; freezes auto-dismiss and focuses mascot."""
        self.freeze_timer()
        self.robot.set_mood("TYPING")
        self.speech_label.config(text="✍️ Recording symptoms & notes...", fg=COLORS["accent_cyan"])

    def on_paste_shortcut(self, event=None):
        """Smart paste: if clipboard contains an image, attach screenshot; else let default paste handle."""
        img_path = capture_clipboard_image()
        if img_path:
            self.freeze_timer()
            self.set_screenshot(img_path)
            return "break"
        return None

    def freeze_timer(self):
        """Freezes the auto-dismiss timer so notes are never lost."""
        if not self.is_timer_frozen:
            self.is_timer_frozen = True
            if self._countdown_job:
                self.win.after_cancel(self._countdown_job)
                self._countdown_job = None
            self.countdown_label.config(text="⚡ Timer Paused (Esc to close • Ctrl+Enter to save)", fg=COLORS["accent_amber"])
            self.draw_progress_bar(fraction=1.0, color=COLORS["accent_amber"])

    def draw_progress_bar(self, fraction: float, color: str = COLORS["accent_cyan"]):
        """Draws smooth shrinking countdown bar on bottom canvas."""
        self.progress_canvas.delete("all")
        w = self.progress_canvas.winfo_width()
        if w <= 1:
            w = HUD_WIDTH - 40
        fill_w = max(0, int(w * fraction))
        if fill_w > 0:
            self.progress_canvas.create_rectangle(0, 0, fill_w, 4, fill=color, outline="")

    def start_countdown(self):
        """Ticks down auto-dismiss timer every 100ms when untouched."""
        if self.is_timer_frozen or not self.is_visible:
            return

        self.countdown_remaining -= 0.1
        fraction = max(0.0, self.countdown_remaining / float(AUTO_DISMISS_SECONDS))
        self.draw_progress_bar(fraction)

        if self.countdown_remaining <= 2.2:
            self.robot.set_mood("SLEEPY")
            self.speech_label.config(text="Zzz... going to sleep!", fg=COLORS["text_muted"])

        if self.countdown_remaining <= 0:
            self.hide()
            return

        self.countdown_label.config(
            text=f"Auto-closing in {max(0, int(self.countdown_remaining))}s (Type to keep)"
        )
        self._countdown_job = self.win.after(100, self.start_countdown)

    def summon(self):
        """Summons DeskRobo to front, captures foreground context, starts countdown."""
        # 1. Capture context BEFORE bringing HUD to front
        self.active_context = get_foreground_window_info()

        # 2. Reset state
        self.attached_screenshot = None
        self.preview_bar.pack_forget()
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", self.placeholder_text)
        self.text_area.config(fg=COLORS["text_muted"])
        self.has_placeholder = True
        self.selected_tag = "note"
        self.update_tag_styles()
        self.countdown_remaining = float(AUTO_DISMISS_SECONDS)
        self.is_timer_frozen = False
        self.is_saving = False

        # 3. Position window near bottom right above taskbar
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = screen_w - HUD_WIDTH - 24
        pos_y = screen_h - HUD_HEIGHT - 80
        self.win.geometry(f"{HUD_WIDTH}x{HUD_HEIGHT}+{pos_x}+{pos_y}")

        # 4. Update UI labels
        app_name = self.active_context.get("app_name", "Desktop")
        title = self.active_context.get("title", "")
        is_desktop = self.active_context.get("is_desktop", False)

        if is_desktop:
            self.context_badge.config(text="Target: Desktop / Full Screen")
            self.context_icon.config(text="🖥️")
        else:
            short_title = (title[:38] + "...") if len(title) > 40 else title
            self.context_badge.config(text=f"{app_name}  •  {short_title}")
            self.context_icon.config(text="🎯")

        self.robot.set_mood("NORMAL")
        self.speech_label.config(text="Bleep! Ready to capture your thoughts or bugs...", fg=COLORS["text_dim"])

        # 5. Display & Focus
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()
        self.text_area.focus_set()
        self.is_visible = True

        # 6. Start countdown
        if self._countdown_job:
            self.win.after_cancel(self._countdown_job)
        self.draw_progress_bar(1.0)
        self.start_countdown()

    def hide(self):
        """Hides the HUD."""
        if self._countdown_job:
            self.win.after_cancel(self._countdown_job)
            self._countdown_job = None
        self.is_visible = False
        self.win.withdraw()

    def do_snip_window(self):
        """Snips the active application window or falls back to full screen if on desktop."""
        self.freeze_timer()
        self.robot.set_mood("CAMERA")

        is_desktop = self.active_context.get("is_desktop", False)
        app_name = self.active_context.get("app_name", "Desktop")
        hwnd = self.active_context.get("hwnd", 0)
        rect = self.active_context.get("rect", (0, 0, 800, 600))

        if is_desktop:
            self.speech_label.config(text="Desktop active: capturing full screen...", fg=COLORS["accent_cyan"])
        else:
            self.speech_label.config(text=f"Capturing {app_name} window...", fg=COLORS["accent_cyan"])

        # Briefly minimize HUD to capture clean underlying screen
        self.win.withdraw()
        self.root.update()

        path = capture_active_window(rect=rect, hwnd=hwnd, is_desktop=is_desktop)

        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()

        if path:
            self.set_screenshot(path)
            if is_desktop:
                self.speech_label.config(text="Full screen screenshot attached!", fg=COLORS["accent_green"])
            else:
                self.speech_label.config(text=f"Attached {app_name} window!", fg=COLORS["accent_green"])
        else:
            self.speech_label.config(text="Could not snip window.", fg=COLORS["accent_rose"])

    def do_snip_fullscreen(self):
        """Captures entire screen directly."""
        self.freeze_timer()
        self.robot.set_mood("CAMERA")
        self.speech_label.config(text="Capturing full screen...", fg=COLORS["accent_cyan"])

        self.win.withdraw()
        self.root.update()

        path = capture_fullscreen()

        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()

        if path:
            self.set_screenshot(path)
            self.speech_label.config(text="Full screen screenshot attached!", fg=COLORS["accent_green"])
        else:
            self.speech_label.config(text="Could not capture screen.", fg=COLORS["accent_rose"])

    def do_drag_crop(self):
        """Opens interactive rubber-band drag crop."""
        self.freeze_timer()
        self.robot.set_mood("CAMERA")
        self.speech_label.config(text="Drag a rectangular box to crop...", fg=COLORS["accent_cyan"])

        self.win.withdraw()
        self.root.update()

        def on_crop_done(path):
            self.win.deiconify()
            self.win.lift()
            self.win.focus_force()
            if path:
                self.set_screenshot(path)
                self.speech_label.config(text="Crop region attached!", fg=COLORS["accent_green"])
            else:
                self.speech_label.config(text="Crop cancelled.", fg=COLORS["text_dim"])

        InteractiveRegionSnipper(on_crop_done)

    def do_paste_image(self):
        """Checks clipboard for image and attaches it."""
        self.freeze_timer()
        path = capture_clipboard_image()
        if path:
            self.set_screenshot(path)
            self.speech_label.config(text="Pasted image from clipboard!", fg=COLORS["accent_green"])
        else:
            self.speech_label.config(text="No image found in clipboard.", fg=COLORS["accent_amber"])

    def set_screenshot(self, filepath: str):
        """Displays screenshot thumbnail inside the card."""
        self.attached_screenshot = filepath
        self.thumbnail_photo = get_thumbnail_photo(filepath, max_size=(120, 60))
        if self.thumbnail_photo:
            self.thumbnail_label.config(image=self.thumbnail_photo)
            
            # Show resolution info
            try:
                with Image.open(filepath) as img:
                    w, h = img.size
                    self.preview_info.config(text=f"📸 {w}×{h} PNG Attached")
            except Exception:
                self.preview_info.config(text="📸 Screenshot Attached")

            # Pack preview bar right above action bar
            self.preview_bar.pack(fill=tk.X, pady=(0, 8), before=self.snip_win_btn.master)
            self.robot.set_mood("HAPPY")

    def open_attached_image(self):
        """Opens the attached image in full resolution using Windows viewer."""
        if self.attached_screenshot and Path(self.attached_screenshot).exists():
            os.startfile(self.attached_screenshot)

    def remove_screenshot(self):
        """Removes attached screenshot from current draft."""
        self.attached_screenshot = None
        self.preview_bar.pack_forget()
        self.robot.set_mood("NORMAL")
        self.speech_label.config(text="Screenshot removed.", fg=COLORS["text_dim"])

    def save_current_note(self):
        """Saves note + screenshot to SQLite & daily Markdown file, then dismisses."""
        if self.is_saving:
            return

        content = ""
        if not self.has_placeholder:
            content = self.text_area.get("1.0", tk.END).strip()

        if not content and not self.attached_screenshot:
            self.robot.set_mood("SLEEPY")
            self.speech_label.config(text="Please type a note or take a screenshot first!", fg=COLORS["accent_amber"])
            return

        self.is_saving = True
        self.robot.set_mood("HAPPY")
        self.speech_label.config(text="✨ Saving note...", fg=COLORS["accent_green"])

        title = self.active_context.get("title", "")
        app_name = self.active_context.get("app_name", "Desktop")

        if not title:
            title = content.split("\n")[0][:45] if content else "Screenshot Note"

        # Persist via storage manager
        try:
            note_id = self.storage.save_note(
                content=content or "[Screenshot only]",
                tag=self.selected_tag,
                title=title,
                app_name=app_name,
                screenshot_path=self.attached_screenshot
            )
            self.speech_label.config(text="✨ Saved to daily notes dossier!", fg=COLORS["accent_green"])
            # Smooth celebratory dismissal
            self.win.after(450, self.hide)
        except Exception as e:
            self.speech_label.config(text=f"Error saving: {e}", fg=COLORS["accent_rose"])
            self.is_saving = False

    def open_archive(self):
        """Opens the searchable history viewer."""
        self.hide()
        self.on_open_archive()
