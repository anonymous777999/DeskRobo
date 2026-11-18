# 🤖 DeskRobo — The Cute Desktop Bug & Note Companion

> **Always present, instant capture, zero friction.**  
> Built for fast-paced developers who spot a problem while working and need to capture symptoms + screenshots in 2 seconds without context-switching to Notepad.

---

## ✨ Features

- **⚡ Lightning Fast Global Hotkeys (`Alt + Q` or `Alt + N`):** Summon DeskRobo with a fast 1-hand combo from any screen or game in an instant. (Classic `Ctrl + Alt + N` also works!)
- **🤖 Cute Animated Robot Mascot:** High-DPI vector avatar with expressive glowing eyes (blinking, typing focus, camera shutter, celebration).
- **⏳ Smart Auto-Dismiss:** Stays up for **8 seconds** when summoned. If untouched, smoothly vanishes into the background. The instant you touch a key or click, the timer freezes so your notes are never lost!
- **📸 1-Click Screen Snips:**
  - `📸 Window`: Automatically snaps the exact bounding box of the active window using DWM physical frame bounds (accurate across all Windows DPI scale factors).
  - `🖥️ Full`: Instantly snaps the entire screen with one click.
  - `✂ Crop`: Interactive rubber-band selector to crop any specific UI error or button.
  - `📋 Paste`: Instantly extracts and previews images copied in your clipboard.
- **🖥 Automatic Context Grabber:** Automatically captures active app name (e.g. `chrome.exe`, `Code.exe`), window title, and exact timestamp.
- **🏷 Quick Tag Pills:** 1-click categorizers (`🐛 Bug`, `💡 Idea`, `✅ Todo`, `📝 Note`).
- **💾 Dual Persistence:**
  - **Daily Markdown Dossier:** Appends structured, beautiful entries with screenshot embeds directly to `D:\DeskRobo\notes\YYYY-MM-DD.md` (ready for Obsidian, Notion, or Git).
  - **SQLite Full-Text DB:** Indexed in `D:\DeskRobo\data\deskrobo.db` for instant relational search.
- **📚 Searchable Notes Archive (`Ctrl + H`):** Integrated viewer with live keyword search, tag filtering, full-res screenshot viewing, and 1-click "Copy as Markdown".
- **🪶 Ultra-Lean Footprint:** Consumes only ~**25MB–35MB RAM**, running natively without heavy Electron overhead.

---

## ⌨ Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| **`Alt + Q`** or **`Alt + N`** | **Summon DeskRobo** (lightning fast 1-hand global trigger) |
| **`Ctrl + Enter`** | **Save Note + Screenshot** (celebrates and auto-dismisses) |
| **`Escape`** | **Dismiss / Hide DeskRobo** |
| **`Alt + 1` .. `Alt + 4`** | **Quick Switch Tag** (1: Bug, 2: Idea, 3: Todo, 4: Note) |
| **`Alt + W`** | **Snip Active Window** |
| **`Alt + F`** | **Snip Full Screen** |
| **`Alt + C`** | **Drag-Crop Selection Box** |
| **`Ctrl + V`** | **Smart Paste** (automatically attaches image if in clipboard) |
| **`Ctrl + H`** | **Open Notes Archive & Search Viewer** |

---

## 🚀 How to Run & Keep Always Running

### ⚡ 1-Click Install Auto-Start (Recommended)
Double-click **`D:\DeskRobo\install_autostart.bat`**.
- It creates a Windows Startup shortcut so DeskRobo boots invisibly in the background on startup.
- Starts it silently right now.
- To remove autostart anytime, double-click **`D:\DeskRobo\uninstall_autostart.bat`**.

### 🥷 1-Click Silent Background Mode
Double-click **`D:\DeskRobo\start_silent.bat`** (or `launch_silent.vbs`).
- Runs as an invisible background daemon (0 console windows, 0 taskbar clutter).
- Sleeps quietly consuming only ~**25MB RAM** until summoned with `Alt + Q` or `Alt + N`!

### 🖱️ System Tray Toggle
Right-click the cute robot icon in the Windows taskbar notification tray:
- Check or uncheck **`🚀 Run on Windows Startup`** anytime!
- **`🤖 Summon DeskRobo (Alt+Q / Alt+N)`**
- **`📚 View Notes Archive (Ctrl+H)`**
- **`📁 Open Notes Folder`**
- **`❌ Exit DeskRobo`**

---

## 📂 Directory Structure

```
D:\DeskRobo\
├── core\
│   ├── config.py             # Colors, hotkey, and geometry constants
│   ├── window_tracker.py     # Win32 foreground window & process tracker
│   ├── storage.py            # SQLite + Daily Markdown persistence
│   ├── snipper.py            # Active window snip, drag-crop & clipboard
│   ├── robot_canvas.py       # Vector-animated cute robot mascot
│   ├── robot_hud.py          # Frameless floating HUD card
│   ├── archive_viewer.py     # Searchable note history & full-res viewer
│   └── tray.py               # Windows system tray daemon
├── data\
│   ├── deskrobo.db           # SQLite database
│   └── screenshots\          # High-res PNG snips
├── notes\
│   └── YYYY-MM-DD.md         # Daily organized markdown logs
├── launch.bat                # 1-click console launcher
├── launch_silent.vbs         # Silent background launcher
└── main.py                   # Main daemon entry point
```
