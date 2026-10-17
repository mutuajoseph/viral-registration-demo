# Campus Tech Night registration: after

Companion code for the talk **“Your App Just Went Viral. Now What?”**
(JKUAT GDG × Moringa School, 17 October 2026).

200 free tickets. Registration opens at noon. This branch is the club’s app
after the fixes from the talk. Compare it with the naive version:

| Branch   | What it shows |
|----------|---------------|
| `before` | The naive app: overbooks, double-books, waits for email |
| `after`  | The fixes, one commit per idea (you are here) |

```bash
git diff before after            # everything that changed
git log --oneline before..after  # one commit per fix
```

## What changed

| Commit | Idea | Talk slide |
|--------|------|-----------|
| 1 | Conditional `UPDATE … WHERE seats_left > 0` + booking in one transaction; `UNIQUE (event_id, student_id)` | 11–12 |
| 2 | `Idempotency-Key` header: a repeated request gets the first answer | 13 |
| 3 | Transactional outbox + background worker: retries, backoff, duplicate-safe sends | 14 |
| 4 | Cache for event details; never used to confirm a booking | 10 |

Deliberately **not** added: microservices, Kubernetes, sharding, extra regions.
No requirement in this scenario needs them.

## Layout

```
app/
  main.py                  HTTP routes (FastAPI)
  config.py                settings from environment variables
  db.py                    SQLite connection + setup
  schema.sql               tables, constraints, outbox, idempotency keys
  cache.py                 tiny TTL cache                      (new)
  worker.py                email worker                        (new)
  services/
    registration.py        booking logic: one transaction
    email.py               fake email provider (slow, can fail)
scripts/stampede.py        simulate noon: many students at once
tests/                     one test per requirement
```

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

pytest                                         # all green
uvicorn app.main:create_app --factory          # terminal 1: API
python -m app.worker                           # terminal 2: email worker
python scripts/stampede.py --students 500 --clicks 2   # terminal 3
```

Expected stampede result: **exactly 200 bookings**, one per student,
fast responses, and emails catching up in the worker terminal.
Try `EMAIL_FAILURE_RATE=0.5 python -m app.worker`: bookings stay correct,
emails retry.

## Notes

- SQLite lets one writer at a time; PostgreSQL would lock just the event row.
  The conditional update is the same idea in both.
- Rate limiting and a fair allocation policy (lottery, waiting room) are
  natural next steps; see slide 15.

Settings (environment variables): `EVENT_CAPACITY`, `SIMULATED_WORK_SECONDS`,
`EMAIL_LATENCY_SECONDS`, `EMAIL_FAILURE_RATE`, `CACHE_TTL_SECONDS`, `DB_PATH`.
Delete `registration.db` to start fresh.
