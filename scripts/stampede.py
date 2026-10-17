"""Noon, simulated: many students hit Register at once.

Usage (with the server running on :8000):
    python scripts/stampede.py --students 500 --clicks 2
"""

import argparse
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import httpx


def student_session(client: httpx.Client, url: str, n: int, clicks: int) -> list[str]:
    student_id = f"S-{n:05d}"
    key = uuid.uuid4().hex  # one key per registration attempt, reused on every click
    outcomes = []
    for _ in range(clicks):
        try:
            r = client.post(
                f"{url}/events/1/register",
                json={"student_id": student_id, "email": f"{student_id}@example.com"},
                headers={"Idempotency-Key": key},
            )
            outcomes.append(str(r.status_code))
        except httpx.HTTPError:
            outcomes.append("network error")
    return outcomes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--students", type=int, default=500)
    parser.add_argument("--clicks", type=int, default=1, help="how many times each student taps Register")
    parser.add_argument("--concurrency", type=int, default=100)
    args = parser.parse_args()

    with httpx.Client(timeout=60) as client, ThreadPoolExecutor(args.concurrency) as pool:
        results = pool.map(lambda n: student_session(client, args.url, n, args.clicks), range(args.students))
        counts = Counter(outcome for outcomes in results for outcome in outcomes)
        stats = client.get(f"{args.url}/stats").json()

    print("Responses:", dict(counts))
    print("Stats:    ", stats)
    verdict = "OK" if stats["correct"] else "OVERBOOKED"
    print(f"Verdict:   {verdict}: {stats['confirmed_bookings']} bookings for {stats['capacity']} seats")


if __name__ == "__main__":
    main()
