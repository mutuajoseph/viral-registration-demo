"""SQLite connection helpers. One connection per request."""

import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")


def connect(db_path: str) -> sqlite3.Connection:
    # isolation_level=None: autocommit. Transactions happen only where we write BEGIN.
    conn = sqlite3.connect(db_path, timeout=30, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(db_path: str, capacity: int) -> None:
    conn = connect(db_path)
    conn.executescript(SCHEMA.read_text())
    conn.execute(
        "INSERT OR IGNORE INTO events (id, title, venue, starts_at, capacity, seats_left) "
        "VALUES (1, 'Campus Tech Night', 'Hall 3', '2026-10-24T17:00', ?, ?)",
        (capacity, capacity),
    )
    conn.close()
