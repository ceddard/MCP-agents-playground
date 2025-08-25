import os
from typing import Any

from app.storage.redis_storage import _client as _redis

# Circuit breaker config via environment
MAX_FAILURES = int(os.getenv("CB_MAX_FAILURES", "3"))
OPEN_TTL = int(os.getenv("CB_RESET_TTL", "60"))  # seconds circuit stays open


def _failure_key(agent: str) -> str:
    return f"circuit:{agent}:failures"


def _open_key(agent: str) -> str:
    return f"circuit:{agent}:open"


def is_open(agent: str) -> bool:
    """Return True if circuit is open for the agent."""
    try:
        return bool(int(_redis.exists(_open_key(agent))))
    except Exception:
        # If redis is down, be conservative and return False (allow calls)
        return False


def record_failure(agent: str) -> None:
    """Increment failure counter; open circuit if threshold reached."""
    try:
        count = int(_redis.incr(_failure_key(agent)))
        # keep counter with some expiry so transient errors clear
        _redis.expire(_failure_key(agent), OPEN_TTL * 2)
        if count >= MAX_FAILURES:
            _redis.set(_open_key(agent), "1", ex=OPEN_TTL)
            # reset counter
            _redis.delete(_failure_key(agent))
    except Exception:
        # best-effort; don't raise
        return None


def record_success(agent: str) -> None:
    """Reset counters/open flags on successful call."""
    try:
        _redis.delete(_failure_key(agent))
        _redis.delete(_open_key(agent))
    except Exception:
        return None
