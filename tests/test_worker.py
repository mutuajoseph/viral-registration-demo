"""The email worker: sends from the outbox, retries, and tolerates duplicates."""

from app.db import connect
from app.services.email import FakeEmailProvider
from app.worker import process_once
from tests.conftest import register


def test_worker_sends_the_confirmation_email(make_client):
    client = make_client()
    register(client, "S-1001")
    provider = FakeEmailProvider(latency_seconds=0)

    conn = connect(client.app.state.settings.db_path)
    assert process_once(conn, provider) == 1
    assert provider.sent == [("S-1001@example.com", "You're in!")]
    assert client.get("/stats").json()["emails_sent"] == 1


def test_worker_retries_when_the_provider_is_down(make_client):
    client = make_client()
    register(client, "S-1001")
    provider = FakeEmailProvider(latency_seconds=0, failure_rate=1.0)
    conn = connect(client.app.state.settings.db_path)

    assert process_once(conn, provider, now=1000) == 0       # provider down: try later
    assert client.get("/stats").json()["emails_waiting"] == 1

    provider.failure_rate = 0.0                               # provider recovers
    assert process_once(conn, provider, now=1001) == 0       # not due yet (backoff)
    assert process_once(conn, provider, now=1010) == 1       # due: sent
    assert client.get("/stats").json()["emails_sent"] == 1


def test_duplicate_delivery_sends_one_email():
    provider = FakeEmailProvider(latency_seconds=0)
    provider.send("a@example.com", "You're in!", "...", idempotency_key="booking-1")
    provider.send("a@example.com", "You're in!", "...", idempotency_key="booking-1")
    assert len(provider.sent) == 1
