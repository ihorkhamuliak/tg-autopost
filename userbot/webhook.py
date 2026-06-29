import os
import asyncio
import logging
import aiohttp

logger = logging.getLogger(__name__)

N8N_WEBHOOK_URL = os.environ["N8N_WEBHOOK_URL"]
TIMEOUT_SEC = int(os.getenv("WEBHOOK_TIMEOUT_SEC", "15"))
MAX_RETRIES = int(os.getenv("WEBHOOK_MAX_RETRIES", "3"))


async def send_to_webhook(payload: dict) -> dict | None:
    """POST payload to n8n and return its JSON response (or None on failure)."""
    timeout = aiohttp.ClientTimeout(total=TIMEOUT_SEC)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(N8N_WEBHOOK_URL, json=payload) as resp:
                    if resp.status in (200, 201):
                        try:
                            return await resp.json(content_type=None)
                        except Exception:
                            return {}
                    body = await resp.text()
                    logger.warning(
                        "Webhook returned %s (attempt %d/%d): %s",
                        resp.status, attempt, MAX_RETRIES, body[:200],
                    )
        except aiohttp.ClientError as exc:
            logger.warning(
                "Webhook connection error (attempt %d/%d): %s",
                attempt, MAX_RETRIES, exc,
            )

        if attempt < MAX_RETRIES:
            await asyncio.sleep(2 ** attempt)  # 2s, 4s

    logger.error(
        "Failed to deliver payload for %s/%s after %d attempts",
        payload.get("source_channel"), payload.get("message_id"), MAX_RETRIES,
    )
    return None
