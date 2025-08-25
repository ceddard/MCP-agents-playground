import os
import json
import time
from typing import List, Dict, Any

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
_client = redis.from_url(REDIS_URL, decode_responses=True)

# Configuration
HISTORY_MAX = int(os.getenv("HISTORY_MAX", "200"))
SESSION_TTL = int(os.getenv("SESSION_TTL", str(60 * 60 * 24)))  # 24h


def _key(session_id: str) -> str:
    return f"session:{session_id}:history"


def append_turn(session_id: str, entry: Dict[str, Any]) -> None:
    """Append a turn (user or agent) to the session history and trim/expire."""
    if not session_id:
        return
    k = _key(session_id)
    payload = {**entry, "ts": int(time.time())}
    _client.rpush(k, json.dumps(payload))
    # keep only the last HISTORY_MAX items
    _client.ltrim(k, -HISTORY_MAX, -1)
    _client.expire(k, SESSION_TTL)


def get_history(session_id: str) -> List[Dict[str, Any]]:
    if not session_id:
        return []
    k = _key(session_id)
    # redis-py can return a list or an awaitable depending on client; cast to list for typing
    raw = list(_client.lrange(k, 0, -1))
    if not raw:
        return []
    out: List[Dict[str, Any]] = []
    for item in raw:
        try:
            out.append(json.loads(item))
        except Exception:
            # skip malformed
            continue
    return out


def clear_history(session_id: str) -> None:
    if not session_id:
        return
    _client.delete(_key(session_id))
