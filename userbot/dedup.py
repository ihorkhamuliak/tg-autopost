import os
import time
import math
import asyncio
import logging
import aiohttp

logger = logging.getLogger(__name__)

# Optional — if no key, dedup is disabled and everything is published as usual.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = os.getenv("DEDUP_EMBED_MODEL", "text-embedding-3-small")

WINDOW_SEC = int(os.getenv("DEDUP_WINDOW_MIN", "60")) * 60   # how long a story blocks duplicates
THRESHOLD = float(os.getenv("DEDUP_THRESHOLD", "0.84"))      # cosine similarity to call it a duplicate
MIN_CHARS = int(os.getenv("DEDUP_MIN_CHARS", "200"))         # shorter posts (alerts) are never deduped
MAX_KEEP = int(os.getenv("DEDUP_MAX_KEEP", "120"))           # cap on remembered embeddings

# Recent posts: list of (timestamp, embedding). In-memory — resets on restart (fine, window is short).
_recent: list[tuple[float, list[float]]] = []
_lock = asyncio.Lock()


async def _embed(text: str) -> list[float]:
    url = "https://api.openai.com/v1/embeddings"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    body = {"model": EMBED_MODEL, "input": text[:8000]}
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        async with s.post(url, headers=headers, json=body) as r:
            data = await r.json()
            return data["data"][0]["embedding"]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _prune(now: float):
    global _recent
    _recent = [(ts, e) for ts, e in _recent if now - ts <= WINDOW_SEC][-MAX_KEEP:]


async def is_duplicate(text: str) -> bool:
    """True if this story was already published recently. Fails open (returns False) on any error."""
    text = (text or "").strip()
    if not OPENAI_API_KEY or len(text) < MIN_CHARS:
        return False

    async with _lock:
        now = time.time()
        _prune(now)
        try:
            emb = await _embed(text)
        except Exception:
            logger.exception("Dedup embed failed — publishing anyway")
            return False

        best = max((_cosine(emb, e) for _, e in _recent), default=0.0)
        if best >= THRESHOLD:
            logger.info("Duplicate story detected (sim=%.3f) — skipping", best)
            return True

        _recent.append((now, emb))
        logger.info("New story stored (max sim=%.3f, cache=%d)", best, len(_recent))
        return False
