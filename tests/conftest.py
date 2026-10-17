import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def make_client(tmp_path):
    """Build a test client with its own fresh database."""
    clients = []

    def _make(capacity: int = 200, **overrides) -> TestClient:
        settings = Settings(
            db_path=str(tmp_path / "test.db"),
            event_capacity=capacity,
            simulated_work_seconds=0.05,
            email_latency_seconds=0.0,
            **overrides,
        )
        client = TestClient(create_app(settings))
        client.__enter__()
        clients.append(client)
        return client

    yield _make
    for client in clients:
        client.__exit__(None, None, None)


def register(client: TestClient, student_id: str, key: str | None = None):
    headers = {"Idempotency-Key": key} if key else {}
    return client.post(
        "/events/1/register",
        json={"student_id": student_id, "email": f"{student_id}@example.com"},
        headers=headers,
    )
