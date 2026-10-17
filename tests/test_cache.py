"""The cache is a fast hint. The database is the source of truth."""

from tests.conftest import register


def test_cached_seat_count_never_decides_a_booking(make_client):
    client = make_client(capacity=1)
    assert client.get("/events/1").json()["seats_left"] == 1   # cached: 1 left

    assert register(client, "S-1001").status_code == 200
    assert client.get("/events/1").json()["seats_left"] == 1   # stale hint, by design

    response = register(client, "S-1002")                       # the database decides
    assert response.status_code == 409
    assert response.json()["detail"]["status"] == "sold_out"
