"""Registration logic. AFTER: the database decides who gets a seat."""

import sqlite3
import time

from app.services.email import FakeEmailProvider


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


def register(
    conn: sqlite3.Connection,
    email_provider: FakeEmailProvider,
    event_id: int,
    student_id: str,
    email: str,
    work_seconds: float = 0.0,
) -> dict:
    time.sleep(work_seconds)  # same work as before, but no longer between check and act

    conn.execute("BEGIN")
    try:
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
        conn.execute("COMMIT")
    except sqlite3.IntegrityError:  # UNIQUE (event_id, student_id)
        conn.execute("ROLLBACK")
        raise AlreadyRegistered(_existing_booking_id(conn, event_id, student_id))
    except BaseException:
        conn.execute("ROLLBACK")
        raise

    # Still inside the request for now (fixed in a later commit).
    event = get_event(conn, event_id)
    email_provider.send(email, "You're in!", f"Booking #{booking_id}: {event['title']}")

    return {"status": "confirmed", "booking_id": booking_id}
