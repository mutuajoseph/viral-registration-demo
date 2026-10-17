# Campus Tech Night registration: before

Companion code for the talk **“Your App Just Went Viral. Now What?”**
(JKUAT GDG × Moringa School, 17 October 2026).

200 free tickets. Registration opens at noon. This is the app the club built.
It works for 5 testers and breaks when thousands of students arrive at once.

| Branch   | What it shows |
|----------|---------------|
| `before` | The naive app (you are here) |
| `after`  | The same app with the fixes from the talk, one commit per idea |

```bash
git diff before after          # everything that changed
git log --oneline before..after  # one commit per fix
```

## Layout

```
app/
  main.py                  HTTP routes (FastAPI)
  config.py                settings from environment variables
  db.py                    SQLite connection + setup
  schema.sql               tables
  services/
    registration.py        booking logic
    email.py               fake email provider (slow, can fail)
scripts/stampede.py        simulate noon: many students at once
tests/                     one test per requirement
```

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

pytest -rx                                     # 2 pass, 4 known bugs (xfail)
uvicorn app.main:create_app --factory          # terminal 1
python scripts/stampede.py --students 500 --clicks 2   # terminal 2
```

Typical stampede result on this branch: **far more than 200 bookings**, duplicate
bookings per student, and slow responses while every request waits for email.

## Known bugs (each is an `xfail` test)

| Bug | Talk slide |
|-----|-----------|
| Read seats, then write: two requests both see “1 left” | 11 · One ticket, two students |
| Same student can book twice | 12 · Protect the last ticket |
| Double-click creates a second booking | 13 · “I clicked twice” |
| Email is sent inside the request; if it fails, the student sees an error | 14 · The email didn’t |

Settings (environment variables): `EVENT_CAPACITY`, `SIMULATED_WORK_SECONDS`,
`EMAIL_LATENCY_SECONDS`, `EMAIL_FAILURE_RATE`, `DB_PATH`. Delete `registration.db`
to start fresh.
