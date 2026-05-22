import sqlite3
import os
from datetime import date
from contextlib import contextmanager

DB_PATH = os.environ.get("DB_PATH", "pidor.db")



@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                full_name TEXT NOT NULL,
                PRIMARY KEY (chat_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS daily_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                result_date TEXT NOT NULL,
                preset INTEGER DEFAULT 0,
                UNIQUE (chat_id, result_date)
            );

            CREATE TABLE IF NOT EXISTS preset_choice (
                chat_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL
            );
        """)


def upsert_user(chat_id: int, user_id: int, username: str | None, full_name: str):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (chat_id, user_id, username, full_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET
                username = excluded.username,
                full_name = excluded.full_name
            """,
            (chat_id, user_id, username, full_name),
        )


def get_users(chat_id: int) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE chat_id = ?", (chat_id,)
        ).fetchall()


def get_today_result(chat_id: int) -> sqlite3.Row | None:
    today = date.today().isoformat()
    with get_conn() as conn:
        return conn.execute(
            """
            SELECT dr.*, u.full_name, u.username
            FROM daily_results dr
            JOIN users u ON dr.user_id = u.user_id AND dr.chat_id = u.chat_id
            WHERE dr.chat_id = ? AND dr.result_date = ?
            """,
            (chat_id, today),
        ).fetchone()


def save_result(chat_id: int, user_id: int, preset: bool = False):
    today = date.today().isoformat()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO daily_results (chat_id, user_id, result_date, preset)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, user_id, today, int(preset)),
        )


def get_preset(chat_id: int) -> int | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT user_id FROM preset_choice WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        return row["user_id"] if row else None


def set_preset(chat_id: int, user_id: int):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO preset_choice (chat_id, user_id) VALUES (?, ?)",
            (chat_id, user_id),
        )


def clear_preset(chat_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM preset_choice WHERE chat_id = ?", (chat_id,))


def get_stats(chat_id: int, year: int | None = None) -> list[sqlite3.Row]:
    with get_conn() as conn:
        if year:
            return conn.execute(
                """
                SELECT u.full_name, u.username, COUNT(*) as cnt
                FROM daily_results dr
                JOIN users u ON dr.user_id = u.user_id AND dr.chat_id = u.chat_id
                WHERE dr.chat_id = ? AND strftime('%Y', dr.result_date) = ?
                GROUP BY dr.user_id
                ORDER BY cnt DESC
                """,
                (chat_id, str(year)),
            ).fetchall()
        else:
            return conn.execute(
                """
                SELECT u.full_name, u.username, COUNT(*) as cnt
                FROM daily_results dr
                JOIN users u ON dr.user_id = u.user_id AND dr.chat_id = u.chat_id
                WHERE dr.chat_id = ?
                GROUP BY dr.user_id
                ORDER BY cnt DESC
                """,
                (chat_id,),
            ).fetchall()


def clear_today_results():
    today = date.today().isoformat()
    with get_conn() as conn:
        conn.execute("DELETE FROM daily_results WHERE result_date = ?", (today,))


def get_chats_with_users() -> list[int]:
    with get_conn() as conn:
        rows = conn.execute("SELECT DISTINCT chat_id FROM users").fetchall()
        return [r["chat_id"] for r in rows]
