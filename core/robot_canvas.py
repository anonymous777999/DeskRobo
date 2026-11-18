"""
DeskRobo Mascot Canvas
High-DPI vector-animated cute cyber-robot companion with expressive glowing eyes and reactive emotions.
"""

import math
import tkinter as tk
from typing import Literal

RobotMood = Literal["NORMAL", "LISTENING", "TYPING", "CAMERA", "HAPPY", "SLEEPY"]


class RobotCanvas(tk.Canvas):
    def __init__(self, parent, size: int = 70, **kwargs):
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=kwargs.get("bg", "#111827"),
            highlightthickness=0
        )
        self.size = size
        self.mood: RobotMood = "NORMAL"
        self.blink_state = False
        self.antenna_phase = 0.0
        self.is_hovered = False
        self._anim_job = None

        # Interactive hover triggers
        self.bind("<Enter>", self.on_hover_enter)
        self.bind("<Leave>", self.on_hover_leave)
        self.bind("<Button-1>", self.on_click_pet)

        self.draw_robot()
        self.start_animation_loop()

    def on_hover_enter(self, event=None):
        self.is_hovered = True
        if self.mood == "NORMAL":
            self.set_mood("HAPPY")

    def on_hover_leave(self, event=None):
        self.is_hovered = False
        if self.mood == "HAPPY":
            self.set_mood("NORMAL")

    def on_click_pet(self, event=None):
        """Clicking the robot makes it celebrate with a happy mood."""
        self.set_mood("HAPPY")
        # Reset back to normal after 1.5 seconds if mouse leaves
        self.after(1500, lambda: self.set_mood("NORMAL") if not self.is_hovered else None)

    def set_mood(self, mood: RobotMood):
        """Changes the robot's emotion and redraws."""
        if self.mood != mood:
            self.mood = mood
            self.draw_robot()

    def start_animation_loop(self):
        """Animates antenna breathing pulse and occasional natural eye blinking."""
        self.antenna_phase += 0.22

        # Natural blink every ~3.5 to 4 seconds in NORMAL mode
        step = int(self.antenna_phase * 2) % 36
        if self.mood in ("NORMAL", "LISTENING") and step in (0, 1):
            self.blink_state = True
        else:
            self.blink_state = False

        self.draw_robot()
        self._anim_job = self.after(100, self.start_animation_loop)

    def draw_robot(self):
        """Renders the cute high-DPI cyber robot avatar."""
        self.delete("all")
        s = self.size
        scale = s / 70.0

        # Cyber Colors
        head_color = "#1E293B"       # Metallic Slate
        head_highlight = "#334155"   # Top Specular Highlight
        screen_color = "#0B0F19"     # Deep Visor Glass
        screen_border = "#06B6D4"    # Neon Cyan Glow Outline
        eye_color = "#06B6D4"        # Cyber Cyan
        eye_glow = "#38BDF8"         # Electric Blue Glow
        antenna_stem = "#475569"     # Stem
        blush_color = "#FB7185"      # Cute Rosy Blush

        # 1. Cute Antenna
        # Stem
        ax = 35 * scale
        ay_base = 18 * scale
        ay_tip = 6 * scale
        self.create_line(ax, ay_base, ax, ay_tip, fill=antenna_stem, width=max(2, int(2.5 * scale)))

        # Breathing Tip Glow
        pulse = (math.sin(self.antenna_phase) + 1.0) / 2.0
        if self.mood == "HAPPY":
            tip_fill = "#10B981"  # Emerald
            glow_outline = "#34D399"
        elif self.mood == "CAMERA":
            tip_fill = "#F43F5E"  # Rose Red Camera REC
            glow_outline = "#FDA4AF"
        elif self.mood == "TYPING":
            tip_fill = "#F59E0B"  # Amber
            glow_outline = "#FDE68A"
        else:
            tip_fill = "#06B6D4"  # Cyan
            glow_outline = "#67E8F9"

        tip_r = (3.5 + pulse * 1.5) * scale
        # Outer soft aura
        self.create_oval(
            ax - tip_r - 2 * scale, ay_tip - tip_r - 2 * scale,
            ax + tip_r + 2 * scale, ay_tip + tip_r + 2 * scale,
            outline=glow_outline, width=1
        )
        # Inner sphere
        self.create_oval(
            ax - tip_r, ay_tip - tip_r,
            ax + tip_r, ay_tip + tip_r,
            fill=tip_fill, outline="#FFFFFF", width=1
        )

        # 2. Cute Ear Bolts / Side Headphone Pods
        ear_r = 4.0 * scale
        self.create_oval(8 * scale - ear_r, 38 * scale - ear_r, 8 * scale + ear_r, 38 * scale + ear_r, fill="#475569", outline=eye_glow, width=1)
        self.create_oval(62 * scale - ear_r, 38 * scale - ear_r, 62 * scale + ear_r, 38 * scale + ear_r, fill="#475569", outline=eye_glow, width=1)

        # 3. Main Head Chassis (Rounded Helmet)
        hx1, hy1 = 11 * scale, 17 * scale
        hx2, hy2 = 59 * scale, 60 * scale
        hr = 12 * scale
        self._draw_rounded_rect(hx1, hy1, hx2, hy2, hr, fill=head_color, outline="#475569", width=2)
        # Top metallic highlight strip
        self.create_line(hx1 + hr, hy1 + 2 * scale, hx2 - hr, hy1 + 2 * scale, fill=head_highlight, width=max(1, int(2 * scale)))

        # 4. Glass Visor Screen
        vx1, vy1 = 16 * scale, 24 * scale
        vx2, vy2 = 54 * scale, 53 * scale
        vr = 8 * scale
        self._draw_rounded_rect(vx1, vy1, vx2, vy2, vr, fill=screen_color, outline=screen_border, width=1)

        # 5. Eyes & Facial Expressions
        lx = 27 * scale
        rx = 43 * scale
        ey = 38 * scale

        if self.mood == "HAPPY":
            # Smiling crescent eyes: ^  ^
            self.create_line(lx - 5 * scale, ey + 2 * scale, lx, ey - 3 * scale, lx + 5 * scale, ey + 2 * scale, fill=eye_glow, width=max(2, int(2.5 * scale)), smooth=True)
            self.create_line(rx - 5 * scale, ey + 2 * scale, rx, ey - 3 * scale, rx + 5 * scale, ey + 2 * scale, fill=eye_glow, width=max(2, int(2.5 * scale)), smooth=True)
            # Cute pink rosy cheeks
            self.create_oval(lx - 4 * scale, ey + 5 * scale, lx + 4 * scale, ey + 9 * scale, fill=blush_color, outline="")
            self.create_oval(rx - 4 * scale, ey + 5 * scale, rx + 4 * scale, ey + 9 * scale, fill=blush_color, outline="")
            # Sweet smile mouth
            self.create_line(31 * scale, 47 * scale, 35 * scale, 49 * scale, 39 * scale, 47 * scale, fill=eye_color, width=max(1, int(1.5 * scale)), smooth=True)

        elif self.mood == "CAMERA":
            # Camera Aperture / Lens Focus
            for cx in [lx, rx]:
                self.create_oval(cx - 6 * scale, ey - 6 * scale, cx + 6 * scale, ey + 6 * scale, fill="", outline="#F43F5E", width=max(1, int(2 * scale)))
                self.create_oval(cx - 3 * scale, ey - 3 * scale, cx + 3 * scale, ey + 3 * scale, fill="#F43F5E", outline="")
                self.create_oval(cx - 1 * scale, ey - 1 * scale, cx + 1 * scale, ey + 1 * scale, fill="#FFFFFF", outline="")
            # Small "REC" text indicator
            self.create_text(35 * scale, 49 * scale, text="SNAP", fill="#F43F5E", font=("Segoe UI", max(6, int(6 * scale)), "bold"))

        elif self.mood == "TYPING":
            # Focused looking gaze down
            for cx in [lx, rx]:
                self.create_oval(cx - 4 * scale, ey - 2 * scale, cx + 4 * scale, ey + 4 * scale, fill=eye_color, outline=eye_glow, width=1)
                self.create_oval(cx - 1 * scale, ey + 1 * scale, cx + 2 * scale, ey + 3 * scale, fill="#FFFFFF", outline="")
            # Holographic dots below
            dot_color = "#38BDF8"
            for dx in [31, 35, 39]:
                self.create_oval(dx * scale - 1, 48 * scale - 1, dx * scale + 1, 48 * scale + 1, fill=dot_color, outline="")

        elif self.mood == "SLEEPY":
            # Drooping sleepy curved lines
            self.create_line(lx - 5 * scale, ey + 1 * scale, lx + 5 * scale, ey - 1 * scale, fill=eye_color, width=max(1, int(2 * scale)))
            self.create_line(rx - 5 * scale, ey - 1 * scale, rx + 5 * scale, ey + 1 * scale, fill=eye_color, width=max(1, int(2 * scale)))
            # Floating 'z'
            self.create_text(50 * scale, 22 * scale, text="z", fill=eye_glow, font=("Segoe UI", max(8, int(8 * scale)), "bold"))

        elif self.blink_state:
            # Cute blink lines
            self.create_line(lx - 5 * scale, ey, lx + 5 * scale, ey, fill=eye_color, width=max(1, int(2 * scale)))
            self.create_line(rx - 5 * scale, ey, rx + 5 * scale, ey, fill=eye_color, width=max(1, int(2 * scale)))

        else:
            # NORMAL: Big expressive sparkling anime cyber eyes
            er = 5.2 * scale
            for cx in [lx, rx]:
                # Outer glow
                self.create_oval(cx - er, ey - er, cx + er, ey + er, fill=eye_color, outline=eye_glow, width=1)
                # Primary sparkle reflection
                self.create_oval(cx - 2.5 * scale, ey - 3.2 * scale, cx + 0.5 * scale, ey - 0.2 * scale, fill="#FFFFFF", outline="")
                # Secondary micro reflection
                self.create_oval(cx + 1.0 * scale, ey + 1.2 * scale, cx + 2.5 * scale, ey + 2.7 * scale, fill="#FFFFFF", outline="")

    def _draw_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Helper to draw smooth rounded rectangle on Tkinter canvas."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, **kwargs, smooth=True)

    def destroy(self):
        if self._anim_job:
            self.after_cancel(self._anim_job)
        super().destroy()
