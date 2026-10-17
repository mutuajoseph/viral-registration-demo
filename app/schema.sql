CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY,
    title       TEXT    NOT NULL,
    venue       TEXT    NOT NULL,
    starts_at   TEXT    NOT NULL,
    capacity    INTEGER NOT NULL,
    seats_left  INTEGER NOT NULL CHECK (seats_left >= 0)
);

CREATE TABLE IF NOT EXISTS bookings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    INTEGER NOT NULL REFERENCES events(id),
    student_id  TEXT    NOT NULL,
    email       TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (event_id, student_id)              -- one booking per student per event
);

-- Transactional outbox: the "send email" task is saved in the SAME transaction
-- as the booking, so they can never disagree. A worker sends it later.
-- (Here the table is also the queue. Bigger systems relay rows to a real queue.)
CREATE TABLE IF NOT EXISTS outbox (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id       INTEGER NOT NULL UNIQUE REFERENCES bookings(id),
    to_email         TEXT    NOT NULL,
    subject          TEXT    NOT NULL,
    body             TEXT    NOT NULL,
    status           TEXT    NOT NULL DEFAULT 'pending',   -- pending | sent | failed
    attempts         INTEGER NOT NULL DEFAULT 0,
    next_attempt_at  REAL    NOT NULL DEFAULT 0,           -- unix time
    last_error       TEXT
);

-- "Have I already handled this exact request?" -> return the same answer.
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key         TEXT PRIMARY KEY,
    response    TEXT,                          -- JSON returned the first time
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
