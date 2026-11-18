"""
DeskRobo Archive & Search Viewer
Searchable note history, high-res screenshot viewer, and export tools.
"""

import os
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional

import pyperclip
from PIL import Image, ImageTk

from core.config import COLORS, NOTES_DIR, TAGS
from core.storage import StorageManager


class ArchiveViewer:
    def __init__(self, root: tk.Tk, storage: StorageManager):
        self.root = root
        self.storage = storage

        self.win = tk.Toplevel(self.root)
        self.win.withdraw()
        self.win.title("DeskRobo — Notes Archive")
        self.win.geometry("880x560")
        self.win.configure(bg=COLORS["bg_dark"])

        self.current_notes = []
        self.selected_note = None
        self.screenshot_photo = None
        self.active_tag_filter = "all"

        self.setup_ui()
        self.win.protocol("WM_DELETE_WINDOW", self.hide)
        self.win.bind("<Escape>", lambda e: self.hide())

    def setup_ui(self):
        # Top Search & Filter Bar
        top_bar = tk.Frame(self.win, bg=COLORS["bg_card"], padx=14, pady=10)
        top_bar.pack(fill=tk.X)

        tk.Label(
            top_bar,
            text="🔍 Search:",
            font=("Segoe UI", 9, "bold"),
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"]
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.search_entry = tk.Entry(
            top_bar,
            font=("Segoe UI", 9),
            bg=COLORS["bg_input"],
            fg=COLORS["text_main"],
            insertbackground=COLORS["accent_cyan"],
            relief=tk.FLAT,
            width=28
        )
        self.search_entry.pack(side=tk.LEFT, padx=(0, 14), ipady=3)
        self.search_entry.bind("<KeyRelease>", self.on_search)

        # Tag Filter Pills
        tk.Label(
            top_bar,
            text="Filter:",
            font=("Segoe UI", 9, "bold"),
            fg=COLORS["text_dim"],
            bg=COLORS["bg_card"]
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.filter_buttons = {}
        all_tags = [{"id": "all", "label": "All"}] + TAGS
        for t in all_tags:
            btn = tk.Label(
                top_bar,
                text=t["label"],
                font=("Segoe UI", 8, "bold"),
                fg=COLORS["text_dim"],
                bg=COLORS["bg_input"],
                padx=8,
                pady=3,
                cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=(0, 4))
            btn.bind("<Button-1>", lambda e, tid=t["id"]: self.set_tag_filter(tid))
            self.filter_buttons[t["id"]] = btn

        self.update_filter_styles()

        # Open Notes Folder Button
        folder_btn = tk.Label(
            top_bar,
            text="📁 Notes Folder",
            font=("Segoe UI", 8),
            fg=COLORS["accent_cyan"],
            bg=COLORS["btn_secondary"],
            padx=10,
            pady=4,
            cursor="hand2"
        )
        folder_btn.pack(side=tk.RIGHT)
        folder_btn.bind("<Button-1>", lambda e: self.open_notes_folder())

        # Main Split Content Area
        split_pane = tk.PanedWindow(self.win, orient=tk.HORIZONTAL, bg=COLORS["border_glow"], bd=1)
        split_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left: Note List
        left_frame = tk.Frame(split_pane, bg=COLORS["bg_card"], width=320)
        split_pane.add(left_frame, minsize=260)

        self.note_listbox = tk.Listbox(
            left_frame,
            font=("Segoe UI", 9),
            bg=COLORS["bg_card"],
            fg=COLORS["text_main"],
            selectbackground=COLORS["border_glow"],
            selectforeground="#FFFFFF",
            relief=tk.FLAT,
            highlightthickness=0,
            activestyle="none"
        )
        self.note_listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.note_listbox.bind("<<ListboxSelect>>", self.on_select_note)

        # Right: Note Details & Screenshot Viewer
        right_frame = tk.Frame(split_pane, bg=COLORS["bg_dark"], padx=14, pady=12)
        split_pane.add(right_frame, minsize=400)

        # Detail Header
        self.detail_title = tk.Label(
            right_frame,
            text="Select a note from the left to view details",
            font=("Segoe UI", 12, "bold"),
            fg=COLORS["text_main"],
            bg=COLORS["bg_dark"],
            anchor="w",
            wraplength=480
        )
        self.detail_title.pack(fill=tk.X, pady=(0, 4))

        self.detail_meta = tk.Label(
            right_frame,
            text="",
            font=("Segoe UI", 8),
            fg=COLORS["accent_cyan"],
            bg=COLORS["bg_dark"],
            anchor="w"
        )
        self.detail_meta.pack(fill=tk.X, pady=(0, 8))

        # Detail Content Text Area
        self.detail_content = tk.Text(
            right_frame,
            font=("Segoe UI", 9),
            bg=COLORS["bg_input"],
            fg=COLORS["text_main"],
            relief=tk.FLAT,
            height=7,
            wrap=tk.WORD,
            padx=8,
            pady=6
        )
        self.detail_content.pack(fill=tk.X, pady=(0, 10))

        # Detail Screenshot Label
        self.detail_image_label = tk.Label(
            right_frame,
            bg=COLORS["bg_dark"],
            cursor="hand2"
        )
        self.detail_image_label.pack(fill=tk.BOTH, expand=True)
        self.detail_image_label.bind("<Button-1>", lambda e: self.open_full_image())

        # Detail Bottom Action Buttons
        btn_bar = tk.Frame(right_frame, bg=COLORS["bg_dark"])
        btn_bar.pack(fill=tk.X, pady=(8, 0))

        copy_btn = tk.Label(
            btn_bar,
            text="📋 Copy as Markdown",
            font=("Segoe UI", 8, "bold"),
            fg="#FFFFFF",
            bg=COLORS["btn_primary"],
            padx=10,
            pady=4,
            cursor="hand2"
        )
        copy_btn.pack(side=tk.LEFT, padx=(0, 8))
        copy_btn.bind("<Button-1>", lambda e: self.copy_as_markdown())

        del_btn = tk.Label(
            btn_bar,
            text="🗑 Delete",
            font=("Segoe UI", 8),
            fg="#F43F5E",
            bg=COLORS["btn_secondary"],
            padx=10,
            pady=4,
            cursor="hand2"
        )
        del_btn.pack(side=tk.RIGHT)
        del_btn.bind("<Button-1>", lambda e: self.delete_current_note())

    def update_filter_styles(self):
        for fid, btn in self.filter_buttons.items():
            if fid == self.active_tag_filter:
                btn.config(bg=COLORS["border_glow"], fg="#FFFFFF")
            else:
                btn.config(bg=COLORS["bg_input"], fg=COLORS["text_dim"])

    def set_tag_filter(self, tag_id: str):
        self.active_tag_filter = tag_id
        self.update_filter_styles()
        self.reload_notes()

    def on_search(self, event=None):
        query = self.search_entry.get().strip()
        if query:
            self.current_notes = self.storage.search_notes(query)
        else:
            self.current_notes = self.storage.get_recent_notes(tag_filter=self.active_tag_filter)
        self.populate_listbox()

    def reload_notes(self):
        query = self.search_entry.get().strip()
        if query:
            self.current_notes = self.storage.search_notes(query)
        else:
            self.current_notes = self.storage.get_recent_notes(tag_filter=self.active_tag_filter)
        self.populate_listbox()

    def populate_listbox(self):
        self.note_listbox.delete(0, tk.END)
        for n in self.current_notes:
            tag_badge = f"[{n['tag'].upper()}]"
            time_part = n['created_at'][11:16]
            title = n['title']
            self.note_listbox.insert(tk.END, f"{tag_badge} {time_part} — {title}")

        if self.current_notes:
            self.note_listbox.selection_set(0)
            self.display_note_details(self.current_notes[0])
        else:
            self.clear_details()

    def on_select_note(self, event):
        sel = self.note_listbox.curselection()
        if sel and sel[0] < len(self.current_notes):
            self.display_note_details(self.current_notes[sel[0]])

    def display_note_details(self, note: dict):
        self.selected_note = note
        self.detail_title.config(text=f"[{note['tag'].upper()}] {note['title']}")
        self.detail_meta.config(text=f"📅 {note['created_at']} | 🖥 {note.get('app_name', 'Unknown')}")

        self.detail_content.delete("1.0", tk.END)
        self.detail_content.insert("1.0", note["content"])

        # Display screenshot preview
        path = note.get("screenshot_path")
        if path and Path(path).exists():
            try:
                with Image.open(path) as img:
                    img.thumbnail((440, 220), Image.Resampling.LANCZOS)
                    self.screenshot_photo = ImageTk.PhotoImage(img)
                    self.detail_image_label.config(image=self.screenshot_photo, text="")
            except Exception:
                self.detail_image_label.config(image="", text="[Error loading image preview]", fg=COLORS["text_muted"])
        else:
            self.screenshot_photo = None
            self.detail_image_label.config(image="", text="[No screenshot attached]", fg=COLORS["text_muted"])

    def clear_details(self):
        self.selected_note = None
        self.detail_title.config(text="No notes found")
        self.detail_meta.config(text="")
        self.detail_content.delete("1.0", tk.END)
        self.detail_image_label.config(image="", text="")

    def copy_as_markdown(self):
        if not self.selected_note:
            return
        n = self.selected_note
        md = f"### [{n['tag'].upper()}] {n['title']}\n"
        md += f"- **Timestamp**: `{n['created_at']}`\n"
        md += f"- **App Context**: `{n.get('app_name', 'Unknown')}`\n\n"
        md += f"{n['content']}\n"
        if n.get("screenshot_path"):
            md += f"\n- **Screenshot File**: `{n['screenshot_path']}`\n"

        pyperclip.copy(md)
        messagebox.showinfo("Copied", "Note copied to clipboard as Markdown!")

    def open_full_image(self):
        if self.selected_note and self.selected_note.get("screenshot_path"):
            path = self.selected_note["screenshot_path"]
            if Path(path).exists():
                os.startfile(path)

    def open_notes_folder(self):
        os.startfile(str(NOTES_DIR))

    def delete_current_note(self):
        if not self.selected_note:
            return
        if messagebox.askyesno("Delete", "Are you sure you want to delete this note?"):
            self.storage.delete_note(self.selected_note["id"])
            self.reload_notes()

    def show(self):
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()
        self.reload_notes()

    def hide(self):
        self.win.withdraw()
