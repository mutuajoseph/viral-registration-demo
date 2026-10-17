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

-- "Have I already handled this exact request?" -> return the same answer.
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key         TEXT PRIMARY KEY,
    response    TEXT,                          -- JSON returned the first time
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
