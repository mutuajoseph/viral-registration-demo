CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY,
    title       TEXT    NOT NULL,
    venue       TEXT    NOT NULL,
    starts_at   TEXT    NOT NULL,
    capacity    INTEGER NOT NULL,
    seats_left  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS bookings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    INTEGER NOT NULL REFERENCES events(id),
    student_id  TEXT    NOT NULL,
    email       TEXT    NOT NULL,
    created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
