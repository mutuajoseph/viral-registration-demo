"""HTTP layer. Run with: uvicorn app.main:create_app --factory"""

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from app.config import Settings
from app.db import connect, init_db
from app.services import registration
from app.services.email import EmailProviderError, FakeEmailProvider


class RegisterRequest(BaseModel):
    student_id: str
    email: str


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    init_db(settings.db_path, settings.event_capacity)
    email_provider = FakeEmailProvider(settings.email_latency_seconds, settings.email_failure_rate)

    app = FastAPI(title="Campus Tech Night registration")
    app.state.email_provider = email_provider

    def get_conn():
        conn = connect(settings.db_path)
        try:
            yield conn
        finally:
            conn.close()

    @app.get("/events/{event_id}")
    def read_event(event_id: int, conn=Depends(get_conn)):
        try:
            return registration.get_event(conn, event_id)
        except registration.EventNotFound:
            raise HTTPException(404, "Event not found")

    @app.post("/events/{event_id}/register")
    def register(event_id: int, body: RegisterRequest, conn=Depends(get_conn)):
        try:
            return registration.register(
                conn, email_provider, event_id, body.student_id, body.email,
                work_seconds=settings.simulated_work_seconds,
            )
        except registration.EventNotFound:
            raise HTTPException(404, "Event not found")
        except registration.SoldOut:
            raise HTTPException(409, {"status": "sold_out"})
        except EmailProviderError:
            # The booking IS saved, but the student is told something went wrong.
            raise HTTPException(502, "Could not send confirmation email")

    @app.get("/stats")
    def stats(conn=Depends(get_conn)):
        event = registration.get_event(conn, 1)
        confirmed = conn.execute("SELECT COUNT(*) FROM bookings WHERE event_id = 1").fetchone()[0]
        return {
            "capacity": event["capacity"],
            "confirmed_bookings": confirmed,
            "seats_left": event["seats_left"],
            "emails_sent": len(email_provider.sent),
            "correct": confirmed <= event["capacity"],
        }

    return app
