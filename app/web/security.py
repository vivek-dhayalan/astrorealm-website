"""Abuse protection: per-IP rate limiting and Cloudflare Turnstile verification."""
from __future__ import annotations

import asyncio
import json
import threading
import time
import urllib.parse
import urllib.request
from collections import deque

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def client_ip(headers, fallback: str | None) -> str:
    # Behind Cloudflare the real client is in CF-Connecting-IP; never trust X-Forwarded-For blindly.
    return headers.get("cf-connecting-ip") or fallback or "unknown"


class RateLimiter:
    """Sliding-window limiter, in memory (one process). Behind Cloudflare, add a WAF rate rule too."""

    def __init__(self, per_minute: int, window: float = 60.0, max_keys: int = 50_000):
        self.limit = per_minute
        self.window = window
        self.max_keys = max_keys
        self._hits: dict[str, deque] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        with self._lock:
            if len(self._hits) > self.max_keys:
                self._hits.clear()
            q = self._hits.setdefault(key, deque())
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.limit:
                return False
            q.append(now)
            return True


def _verify_sync(secret: str, token: str, ip: str | None, timeout: float = 8.0) -> bool:
    data = {"secret": secret, "response": token}
    if ip:
        data["remoteip"] = ip
    req = urllib.request.Request(TURNSTILE_VERIFY_URL, data=urllib.parse.urlencode(data).encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return bool(json.loads(r.read().decode()).get("success"))
    except Exception:
        return False  # fail closed


async def verify_turnstile(secret: str, token: str | None, ip: str | None) -> bool:
    if not token or len(token) > 2048:
        return False
    return await asyncio.to_thread(_verify_sync, secret, token, ip)
