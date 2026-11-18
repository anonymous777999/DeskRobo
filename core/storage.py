"""
DeskRobo Storage Manager
Dual persistence engine: Local SQLite database + Daily Markdown files.
"""

import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.config import DB_PATH, NOTES_DIR, SCREENSHOTS_DIR


class StorageManager:
    def __init__(self, db_path: Path = DB_PATH, notes_dir: Path = NOTES_DIR):
        self.db_path = db_path
        self.notes_dir = notes_dir
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes SQLite tables if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP NOT NULL,
                    tag TEXT NOT NULL DEFAULT 'note',
                    title TEXT NOT NULL,
                    app_name TEXT,
                    content TEXT NOT NULL,
                    screenshot_path TEXT,
                    is_archived INTEGER NOT NULL DEFAULT 0
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_created ON notes(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_tag ON notes(tag)")
            conn.commit()

    def save_note(
        self,
        content: str,
        tag: str = "note",
        title: str = "",
        app_name: str = "",
        screenshot_path: Optional[str] = None
    ) -> int:
        """
        Saves a note to SQLite database and appends to the daily Markdown file.
        """
        now = datetime.datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

        if not title:
            # First line of content or fallback
            lines = [l.strip() for l in content.splitlines() if l.strip()]
            title = lines[0][:60] if lines else "Quick Note"

        # 1. Save to SQLite
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO notes (created_at, tag, title, app_name, content, screenshot_path, is_archived)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (timestamp_str, tag, title, app_name, content, screenshot_path))
            note_id = cursor.lastrowid
            conn.commit()

        # 2. Append to Daily Markdown log
        self._append_to_daily_markdown(now, note_id, tag, title, app_name, content, screenshot_path)

        return note_id

    def _append_to_daily_markdown(
        self,
        now: datetime.datetime,
        note_id: int,
        tag: str,
        title: str,
        app_name: str,
        content: str,
        screenshot_path: Optional[str]
    ):
        """Appends formatted entry to notes/YYYY-MM-DD.md"""
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        daily_file = self.notes_dir / f"{date_str}.md"

        tag_badges = {
            "bug": "🔴 BUG",
            "idea": "💡 IDEA",
            "todo": "✅ TODO",
            "note": "📝 NOTE"
        }
        badge = tag_badges.get(tag.lower(), "📝 NOTE")

        header_needed = not daily_file.exists()

        with open(daily_file, "a", encoding="utf-8") as f:
            if header_needed:
                f.write(f"# DeskRobo Notes — {date_str}\n\n")
                f.write("> Automatically captured by DeskRobo desktop companion.\n\n---\n\n")

            f.write(f"### `[{time_str}]` {badge} — {title}\n")
            if app_name:
                f.write(f"- **Context**: `{app_name}`\n")
            f.write(f"- **ID**: #{note_id}\n\n")
            
            f.write(f"{content.strip()}\n\n")

            if screenshot_path and Path(screenshot_path).exists():
                # Relative link to screenshots directory
                rel_path = Path(screenshot_path).name
                f.write(f"**Screenshot**:\n\n![Screenshot](../data/screenshots/{rel_path})\n\n")

            f.write("---\n\n")

    def get_recent_notes(self, limit: int = 50, tag_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves recent non-archived notes."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM notes WHERE is_archived = 0"
            params = []

            if tag_filter and tag_filter != "all":
                query += " AND tag = ?"
                params.append(tag_filter)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def search_notes(self, query_text: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Searches notes by content, title, or app_name."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            pattern = f"%{query_text}%"
            cursor.execute("""
                SELECT * FROM notes 
                WHERE is_archived = 0 AND (content LIKE ? OR title LIKE ? OR app_name LIKE ?)
                ORDER BY created_at DESC LIMIT ?
            """, (pattern, pattern, pattern, limit))
            return [dict(row) for row in cursor.fetchall()]

    def delete_note(self, note_id: int):
        """Deletes a note from SQLite."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            conn.commit()
