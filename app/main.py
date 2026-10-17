"""HTTP layer. Run with: uvicorn app.main:create_app --factory"""

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.cache import TTLCache
from app.config import Settings
from app.db import connect, init_db
from app.services import registration


class RegisterRequest(BaseModel):
    student_id: str
    email: str


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    init_db(settings.db_path, settings.event_capacity)

    app = FastAPI(title="Campus Tech Night registration")
    app.state.settings = settings
    event_cache = TTLCache(settings.cache_ttl_seconds)

    def get_conn():
        conn = connect(settings.db_path)
        try:
            yield conn
        finally:
            conn.close()

    @app.get("/events/{event_id}")
    def read_event(event_id: int, conn=Depends(get_conn)):
        # Thousands of students read the same event page: serve a cached copy.
        # seats_left here is only a hint ("about 40 left"); Register asks the DB.
        try:
            return event_cache.get_or_load(event_id, lambda: registration.get_event(conn, event_id))
        except registration.EventNotFound:
            raise HTTPException(404, "Event not found")

    @app.post("/events/{event_id}/register")
    def register(
        event_id: int,
        body: RegisterRequest,
        idempotency_key: str | None = Header(default=None),
        conn=Depends(get_conn),
    ):
        try:
            return registration.register(
                conn, event_id, body.student_id, body.email,
                idempotency_key=idempotency_key,
                work_seconds=settings.simulated_work_seconds,
            )
        except registration.EventNotFound:
            raise HTTPException(404, "Event not found")
        except registration.SoldOut:
            raise HTTPException(409, {"status": "sold_out"})
        except registration.AlreadyRegistered as e:
            raise HTTPException(409, {"status": "already_registered", "booking_id": e.booking_id})

    @app.get("/stats")
    def stats(conn=Depends(get_conn)):
        event = registration.get_event(conn, 1)
        confirmed = conn.execute("SELECT COUNT(*) FROM bookings WHERE event_id = 1").fetchone()[0]
        emails = dict(conn.execute("SELECT status, COUNT(*) FROM outbox GROUP BY status").fetchall())
        return {
            "capacity": event["capacity"],
            "confirmed_bookings": confirmed,
            "seats_left": event["seats_left"],
            "emails_sent": emails.get("sent", 0),
            "emails_waiting": emails.get("pending", 0),
            "correct": confirmed <= event["capacity"],
        }

    return app
