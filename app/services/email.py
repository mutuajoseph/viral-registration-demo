"""A fake email provider: slow, and sometimes fails, like real ones on a busy day."""

import random
import threading
import time


class EmailProviderError(Exception):
    pass


class FakeEmailProvider:
    def __init__(self, latency_seconds: float = 0.5, failure_rate: float = 0.0):
        self.latency_seconds = latency_seconds
        self.failure_rate = failure_rate
        self.sent: list[tuple[str, str]] = []
        self._lock = threading.Lock()

    def send(self, to: str, subject: str, body: str) -> None:
        time.sleep(self.latency_seconds)
        if random.random() < self.failure_rate:
            raise EmailProviderError("email provider timed out")
        with self._lock:
            self.sent.append((to, subject))
