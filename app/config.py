"""Settings, read from environment variables so the demo can be tuned live."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_path: str = "registration.db"
    event_capacity: int = 200
    # Time that passes between "check seats" and "save booking"
    # (validation, a slow network...). Widens the race window for the demo.
    simulated_work_seconds: float = 0.05
    email_latency_seconds: float = 0.5
    email_failure_rate: float = 0.0
    cache_ttl_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            db_path=os.getenv("DB_PATH", cls.db_path),
            event_capacity=int(os.getenv("EVENT_CAPACITY", cls.event_capacity)),
            simulated_work_seconds=float(os.getenv("SIMULATED_WORK_SECONDS", cls.simulated_work_seconds)),
            email_latency_seconds=float(os.getenv("EMAIL_LATENCY_SECONDS", cls.email_latency_seconds)),
            email_failure_rate=float(os.getenv("EMAIL_FAILURE_RATE", cls.email_failure_rate)),
            cache_ttl_seconds=float(os.getenv("CACHE_TTL_SECONDS", cls.cache_ttl_seconds)),
        )
