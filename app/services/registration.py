"""Registration logic. AFTER: the database decides who gets a seat."""

import json
import sqlite3
import time


class EventNotFound(Exception):
    pass


class SoldOut(Exception):
    pass


class AlreadyRegistered(Exception):
    def __init__(self, booking_id: int):
        super().__init__(booking_id)
        self.booking_id = booking_id


def get_event(conn: sqlite3.Connection, event_id: int) -> dict:
    row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if row is None:
        raise EventNotFound(event_id)
    return dict(row)


def _existing_booking_id(conn: sqlite3.Connection, event_id: int, student_id: str) -> int:
    return conn.execute(
        "SELECT id FROM bookings WHERE event_id = ? AND student_id = ?", (event_id, student_id)
    ).fetchone()[0]


def _stored_response(conn: sqlite3.Connection, key: str) -> dict:
    return json.loads(conn.execute("SELECT response FROM idempotency_keys WHERE key = ?", (key,)).fetchone()[0])


def register(
    conn: sqlite3.Connection,
    event_id: int,
    student_id: str,
    email: str,
    idempotency_key: str | None = None,
    work_seconds: float = 0.0,
) -> dict:
    time.sleep(work_seconds)  # same work as before, but no longer between check and act

    conn.execute("BEGIN")
    try:
        if idempotency_key:
            # Claim the key first. If it already exists, this is a repeat
            # (double-click, refresh, network retry): return the first answer.
            # (Production code would also check the key belongs to this student.)
            try:
                conn.execute("INSERT INTO idempotency_keys (key) VALUES (?)", (idempotency_key,))
            except sqlite3.IntegrityError:
                conn.execute("ROLLBACK")
                return _stored_response(conn, idempotency_key)

        # CHECK + ACT in one statement: take a seat only if one is still free.
        cur = conn.execute(
            "UPDATE events SET seats_left = seats_left - 1 WHERE id = ? AND seats_left > 0",
            (event_id,),
        )
        if cur.rowcount == 0:
            get_event(conn, event_id)  # raises EventNotFound if it doesn't exist
            raise SoldOut(event_id)

        # Same transaction: if this INSERT fails, the seat above is given back.
        cur = conn.execute(
            "INSERT INTO bookings (event_id, student_id, email) VALUES (?, ?, ?)",
            (event_id, student_id, email),
        )
        booking_id = cur.lastrowid

        # Outbox: the email task is saved together with the booking.
        # The worker sends it later; the student does not wait for it.
        title = get_event(conn, event_id)["title"]
        conn.execute(
            "INSERT INTO outbox (booking_id, to_email, subject, body) VALUES (?, ?, ?, ?)",
            (booking_id, email, "You're in!", f"Booking #{booking_id}: {title}"),
        )
        response = {
            "status": "confirmed",
            "booking_id": booking_id,
            "message": "You're in! Your email may take a few minutes.",
        }

        if idempotency_key:
            conn.execute(
                "UPDATE idempotency_keys SET response = ? WHERE key = ?",
                (json.dumps(response), idempotency_key),
            )
        conn.execute("COMMIT")
    except sqlite3.IntegrityError:  # UNIQUE (event_id, student_id)
        conn.execute("ROLLBACK")
        raise AlreadyRegistered(_existing_booking_id(conn, event_id, student_id))
    except BaseException:
        conn.execute("ROLLBACK")
        raise

    return response
