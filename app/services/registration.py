"""Registration logic. BEFORE: works for 5 testers, breaks at noon."""

import sqlite3
import time

from app.services.email import FakeEmailProvider


class EventNotFound(Exception):
    pass


class SoldOut(Exception):
    pass


def get_event(conn: sqlite3.Connection, event_id: int) -> dict:
    row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if row is None:
        raise EventNotFound(event_id)
    return dict(row)


def register(
    conn: sqlite3.Connection,
    email_provider: FakeEmailProvider,
    event_id: int,
    student_id: str,
    email: str,
    work_seconds: float = 0.0,
) -> dict:
    # 1. CHECK: read how many seats are left.
    event = get_event(conn, event_id)
    if event["seats_left"] <= 0:
        raise SoldOut(event_id)

    time.sleep(work_seconds)  # time passes between check and act...

    # 2. ACT: write the new count and the booking.
    # BUG (race condition): another request may have read the same count meanwhile.
    # BUG (duplicates): nothing stops the same student booking twice.
    conn.execute(
        "UPDATE events SET seats_left = ? WHERE id = ?",
        (event["seats_left"] - 1, event_id),
    )
    cur = conn.execute(
        "INSERT INTO bookings (event_id, student_id, email) VALUES (?, ?, ?)",
        (event_id, student_id, email),
    )
    booking_id = cur.lastrowid

    # 3. BUG (slow + fragile): the student waits for someone else's server.
    # If it fails, the request fails, even though the booking was saved.
    email_provider.send(email, "You're in!", f"Booking #{booking_id}: {event['title']}")

    return {"status": "confirmed", "booking_id": booking_id}
