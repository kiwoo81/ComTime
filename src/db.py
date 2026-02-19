import sqlite3
from datetime import datetime, date, timedelta
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
        cur.execute("""
        CREATE TABLE IF NOT EXISTS app_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            app_name TEXT NOT NULL,
            started_at TEXT NOT NULL,
            duration_seconds INTEGER DEFAULT 0,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
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
        day_start = datetime.combine(d, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        now_iso = datetime.now().isoformat()
        cur.execute(
            """
        SELECT * FROM sessions
        WHERE start_ts < ? AND COALESCE(end_ts, ?) > ?
        ORDER BY start_ts DESC
        """,
            (day_end.isoformat(), now_iso, day_start.isoformat()),
        )
        return [dict(r) for r in cur.fetchall()]

    def get_total_seconds_for_date(self, d: date) -> int:
        cur = self.conn.cursor()
        day_start = datetime.combine(d, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        now = datetime.now()
        cur.execute(
            """
        SELECT start_ts, end_ts FROM sessions
        WHERE start_ts < ? AND COALESCE(end_ts, ?) > ?
        """,
            (day_end.isoformat(), now.isoformat(), day_start.isoformat()),
        )
        total = 0
        for row in cur.fetchall():
            try:
                start = datetime.fromisoformat(row["start_ts"])
            except Exception:
                continue
            if row["end_ts"]:
                try:
                    end = datetime.fromisoformat(row["end_ts"])
                except Exception:
                    continue
            else:
                end = now
            overlap_start = max(start, day_start)
            overlap_end = min(end, day_end)
            if overlap_end > overlap_start:
                total += int((overlap_end - overlap_start).total_seconds())
        return total

    def get_open_session(self):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM sessions WHERE end_ts IS NULL ORDER BY start_ts DESC LIMIT 1"
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def delete_session(self, session_id: int):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM app_usage WHERE session_id=?", (session_id,))
        cur.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        self.conn.commit()

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

    # App usage tracking
    def record_app_usage(self, session_id: int, app_name: str, interval: int = 5):
        """포그라운드 앱 기록. 같은 세션/앱이면 interval초만큼 누적, 아니면 새 레코드."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, duration_seconds FROM app_usage "
            "WHERE session_id=? AND app_name=? "
            "ORDER BY id DESC LIMIT 1",
            (session_id, app_name),
        )
        row = cur.fetchone()
        if row:
            new_dur = (row["duration_seconds"] or 0) + interval
            cur.execute(
                "UPDATE app_usage SET duration_seconds=? WHERE id=?",
                (new_dur, row["id"]),
            )
        else:
            cur.execute(
                "INSERT INTO app_usage (session_id, app_name, started_at, duration_seconds) VALUES (?,?,?,?)",
                (session_id, app_name, datetime.now().isoformat(), interval),
            )
        self.conn.commit()

    def get_app_usage_for_date(self, d: date):
        """날짜별 앱 사용 요약 (앱별 총 사용시간, 내림차순)."""
        cur = self.conn.cursor()
        day_start = datetime.combine(d, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        now_iso = datetime.now().isoformat()
        cur.execute(
            """
            SELECT au.app_name, SUM(au.duration_seconds) as total_seconds
            FROM app_usage au
            JOIN sessions s ON au.session_id = s.id
            WHERE s.start_ts < ? AND COALESCE(s.end_ts, ?) > ?
            GROUP BY au.app_name
            ORDER BY total_seconds DESC
            """,
            (day_end.isoformat(), now_iso, day_start.isoformat()),
        )
        return [dict(r) for r in cur.fetchall()]

    def delete_app_usage_by_name_and_date(self, app_name: str, d: date):
        """특정 날짜의 특정 앱 사용 기록 전체 삭제."""
        cur = self.conn.cursor()
        day_start = datetime.combine(d, datetime.min.time())
        day_end = day_start + timedelta(days=1)
        now_iso = datetime.now().isoformat()
        cur.execute(
            """
            DELETE FROM app_usage WHERE id IN (
                SELECT au.id FROM app_usage au
                JOIN sessions s ON au.session_id = s.id
                WHERE au.app_name=? AND s.start_ts < ? AND COALESCE(s.end_ts, ?) > ?
            )
            """,
            (app_name, day_end.isoformat(), now_iso, day_start.isoformat()),
        )
        self.conn.commit()


if __name__ == "__main__":
    # 간단한 로컬 테스트
    db = Database(':memory:')
    now = datetime.now().isoformat()
    sid = db.start_session(now)
    db.end_session(sid, datetime.fromisoformat(now).isoformat())
    print(db.get_sessions_for_date(date.today()))
