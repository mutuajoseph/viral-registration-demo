"""Each test is one requirement from the talk.

On the `before` branch the known bugs are marked xfail (expected to fail).
On the `after` branch those markers are gone and every test passes.
"""

from concurrent.futures import ThreadPoolExecutor

import pytest

from tests.conftest import register


def test_student_can_register(make_client):
    client = make_client()
    response = register(client, "S-1001")
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


def test_sold_out_is_a_clear_answer(make_client):
    client = make_client(capacity=1)
    assert register(client, "S-1001").status_code == 200
    response = register(client, "S-1002")
    assert response.status_code == 409
    assert response.json()["detail"]["status"] == "sold_out"


def test_last_ticket_is_never_sold_twice(make_client):
    client = make_client(capacity=1)
    students = [f"S-{n}" for n in range(20)]
    with ThreadPoolExecutor(max_workers=20) as pool:
        list(pool.map(lambda s: register(client, s), students))
    assert client.get("/stats").json()["confirmed_bookings"] == 1


@pytest.mark.xfail(strict=True, reason="no idempotency: a double-click books twice")
def test_double_click_returns_the_same_booking(make_client):
    client = make_client()
    first = register(client, "S-1001", key="a1b2")
    second = register(client, "S-1001", key="a1b2")
    assert second.status_code == 200
    assert second.json()["booking_id"] == first.json()["booking_id"]
    assert client.get("/stats").json()["confirmed_bookings"] == 1


def test_one_booking_per_student(make_client):
    client = make_client()
    register(client, "S-1001", key="phone-1")
    second = register(client, "S-1001", key="phone-2")  # same student, second phone
    assert second.status_code == 409
    assert second.json()["detail"]["status"] == "already_registered"
    assert client.get("/stats").json()["confirmed_bookings"] == 1


@pytest.mark.xfail(strict=True, reason="email is sent inside the request")
def test_booking_survives_email_outage(make_client):
    client = make_client(email_failure_rate=1.0)
    response = register(client, "S-1001")
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"
