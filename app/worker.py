"""Background worker: sends confirmation emails from the outbox.

Run next to the API:  python -m app.worker
"""

import sqlite3
import time

from app.config import Settings
from app.db import connect, init_db
from app.services.email import EmailProviderError, FakeEmailProvider

MAX_ATTEMPTS = 5


def process_once(conn: sqlite3.Connection, provider: FakeEmailProvider, now: float | None = None) -> int:
    """Send every email that is due. Returns how many were sent."""
    now = time.time() if now is None else now
    due = conn.execute(
        "SELECT * FROM outbox WHERE status = 'pending' AND next_attempt_at <= ? ORDER BY id LIMIT 100",
        (now,),
    ).fetchall()
    # One worker keeps this simple. With several, each would first claim a row
    # (e.g. SELECT ... FOR UPDATE SKIP LOCKED in PostgreSQL).

    sent = 0
    for task in due:
        try:
            provider.send(
                task["to_email"], task["subject"], task["body"],
                idempotency_key=f"booking-{task['booking_id']}",  # a resend is harmless
            )
        except EmailProviderError as error:
            attempts = task["attempts"] + 1
            conn.execute(
                "UPDATE outbox SET attempts = ?, status = ?, next_attempt_at = ?, last_error = ? WHERE id = ?",
                (
                    attempts,
                    "failed" if attempts >= MAX_ATTEMPTS else "pending",
                    now + 2 ** attempts,  # back off: 2 s, 4 s, 8 s...
                    str(error),
                    task["id"],
                ),
            )
            continue
        # If we crash right here, the task is sent again later: at-least-once.
        conn.execute("UPDATE outbox SET status = 'sent' WHERE id = ?", (task["id"],))
        sent += 1
    return sent


def main() -> None:
    settings = Settings.from_env()
    init_db(settings.db_path, settings.event_capacity)
    provider = FakeEmailProvider(settings.email_latency_seconds, settings.email_failure_rate)
    conn = connect(settings.db_path)
    print("Worker started. Waiting for emails to send...")
    while True:
        sent = process_once(conn, provider)
        if sent:
            print(f"sent {sent} email(s)")
        time.sleep(1)


if __name__ == "__main__":
    main()
