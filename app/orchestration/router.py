"""Router helper: central synonyms map and resolution logic for agent names.

This module is the single source of truth for canonical agent names and their
accepted synonyms. It also logs and increments a Redis counter when a raw
manager output cannot be resolved (fallback), so you can monitor and tune
the mapping over time.
"""
from typing import Dict, List
import logging

from app.storage.redis_storage import _client as _redis


ROUTER_MAP: Dict[str, List[str]] = {
    "assessoria": ["assessoria", "assessor", "agente de assessoria"],
    "consulta_financeira": [
        "consulta_financeira",
        "consulta-financeira",
        "financeiro",
        "finance",
        "financ",
        "invest",
        "investimentos",
        "agente de financeiro",
        "agente financeiro",
    ],
}


def resolve_agent_name(raw: str) -> str:
    """Resolve a raw manager output to a canonical agent name.

    Returns one of the keys of `ROUTER_MAP`, or the string "unknown" if no
    mapping matches. On fallback, logs a warning and increments a Redis
    counter for monitoring.
    """
    s = (raw or "").lower().strip()
    if not s:
        return "unknown"

    # exact canonical name
    if s in ROUTER_MAP:
        return s

    # exact synonym match
    for canonical, syns in ROUTER_MAP.items():
        if s in syns:
            return canonical

    # substring heuristics: if any synonym appears in the text
    for canonical, syns in ROUTER_MAP.items():
        for syn in syns:
            if syn in s or s in syn:
                return canonical

    # fallback: log and increment Redis counters (best-effort)
    logger = logging.getLogger("mcp_router")
    logger.warning("router_fallback: could not resolve agent for raw=%s", raw)
    try:
        _redis.incr("router:fallback_count")
        # store simplified key for common analysis
        _redis.incr(f"router:fallback:raw:{s}")
    except Exception:
        # best-effort metric; do not crash application
        pass
    return "unknown"
