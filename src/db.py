import sqlite3
from datetime import datetime, date
import hashlib


class Database:
    def __init__(self, path="timelimiter.db"):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_ts TEXT NOT NULL,
            end_ts TEXT,
            duration_seconds INTEGER
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        self.conn.commit()

    def start_session(self, start_ts_iso: str) -> int:
        cur = self.conn.cursor()
        cur.execute("INSERT INTO sessions (start_ts) VALUES (?)", (start_ts_iso,))
        self.conn.commit()
        return cur.lastrowid

    def end_session(self, session_id: int, end_ts_iso: str):
        cur = self.conn.cursor()
        cur.execute("SELECT start_ts FROM sessions WHERE id=?", (session_id,))
        row = cur.fetchone()
        duration = None
        if row and row["start_ts"]:
            try:
                start = datetime.fromisoformat(row["start_ts"])
                end = datetime.fromisoformat(end_ts_iso)
                duration = int((end - start).total_seconds())
            except Exception:
                duration = None
        cur.execute(
            "UPDATE sessions SET end_ts=?, duration_seconds=? WHERE id=?",
            (end_ts_iso, duration, session_id),
        )
        self.conn.commit()

    def get_sessions_for_date(self, d: date):
        cur = self.conn.cursor()
        date_str = d.isoformat()
        cur.execute(
            """
        SELECT * FROM sessions
        WHERE date(start_ts)=? OR date(end_ts)=?
        ORDER BY start_ts DESC
        """,
            (date_str, date_str),
        )
        return [dict(r) for r in cur.fetchall()]

    def get_total_seconds_for_date(self, d: date) -> int:
        cur = self.conn.cursor()
        date_str = d.isoformat()
        cur.execute(
            """
        SELECT SUM(duration_seconds) as total FROM sessions
        WHERE date(start_ts)=? OR date(end_ts)=?
        """,
            (date_str, date_str),
        )
        row = cur.fetchone()
        return int(row[0] or 0)

    def get_open_session(self):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM sessions WHERE end_ts IS NULL ORDER BY start_ts DESC LIMIT 1"
        )
        row = cur.fetchone()
        return dict(row) if row else None

    # Settings helpers (simple key/value). PIN is stored as sha256(hex).
    def set_setting(self, key: str, value: str):
        cur = self.conn.cursor()
        cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
        self.conn.commit()

    def get_setting(self, key: str):
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cur.fetchone()
        return row[0] if row else None

    def set_pin(self, pin_plain: str):
        h = hashlib.sha256(pin_plain.encode("utf-8")).hexdigest()
        self.set_setting("pin_sha256", h)

    def verify_pin(self, pin_plain: str) -> bool:
        stored = self.get_setting("pin_sha256")
        if not stored:
            return False
        return stored == hashlib.sha256(pin_plain.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    # 간단한 로컬 테스트
    db = Database(':memory:')
    now = datetime.now().isoformat()
    sid = db.start_session(now)
    db.end_session(sid, datetime.fromisoformat(now).isoformat())
    print(db.get_sessions_for_date(date.today()))
