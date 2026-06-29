import os
import asyncio
import logging
from telethon import events
from telethon.errors import FloodWaitError

from .media import extract_media_info
from .webhook import send_to_webhook
from .publisher import publish_post
from .dedup import is_duplicate

logger = logging.getLogger(__name__)

# Comma-separated list of source channel usernames (without @)
SOURCE_CHANNELS = [
    c.strip() for c in os.getenv("SOURCE_CHANNELS", "").split(",") if c.strip()
]

# Small courtesy delay between processed messages (fresh account)
POST_PROCESS_DELAY = float(os.getenv("POST_PROCESS_DELAY_SEC", "1.5"))


def register_handlers(client):
    if not SOURCE_CHANNELS:
        logger.warning("SOURCE_CHANNELS is empty — userbot will not listen to anything!")

    @client.on(events.NewMessage(chats=SOURCE_CHANNELS))
    async def handle_single(event):
        # Messages that belong to an album are handled by handle_album below —
        # skip them here to avoid publishing the post twice.
        if event.message.grouped_id:
            return
        await _process_message(event.message, client)

    @client.on(events.Album(chats=SOURCE_CHANNELS))
    async def handle_album(event):
        # First message in album usually carries the caption
        first = event.messages[0]
        media_info = await extract_media_info(first)
        # Collect all local paths so n8n can attach them
        extra_paths = []
        for msg in event.messages[1:]:
            info = await extract_media_info(msg)
            if info.get("local_path"):
                extra_paths.append(info["local_path"])

        chat = await event.get_chat()
        source_channel = getattr(chat, "username", None) or str(chat.id)

        payload = _build_payload(first, source_channel, media_info)
        payload["extra_media_paths"] = extra_paths
        payload["is_album"] = True

        await _send(payload, client)

    logger.info("Handlers registered for channels: %s", SOURCE_CHANNELS)


async def _process_message(message, client):
    try:
        chat = await client.get_entity(message.peer_id)
        source_channel = getattr(chat, "username", None) or str(chat.id)
        media_info = await extract_media_info(message)
        payload = _build_payload(message, source_channel, media_info)
        await _send(payload, client)
    except FloodWaitError as e:
        logger.warning("FloodWaitError: sleeping %ds", e.seconds)
        await asyncio.sleep(e.seconds)
    except Exception:
        logger.exception("Error processing message %s", message.id)
    finally:
        await asyncio.sleep(POST_PROCESS_DELAY)


def _build_payload(message, source_channel: str, media_info: dict) -> dict:
    return {
        "source_channel": source_channel,
        "message_id": message.id,
        "text": message.text or "",
        "has_media": message.media is not None,
        "media_type": media_info.get("type"),
        "local_path": media_info.get("local_path"),
        "is_album": False,
        "extra_media_paths": [],
        "date": message.date.isoformat(),
    }


async def _send(payload: dict, client):
    # Cross-channel dedup — skip a story already published recently (before the costly rewrite).
    if await is_duplicate(payload.get("text", "")):
        logger.info(
            "Skipped duplicate %s/%s",
            payload["source_channel"], payload["message_id"],
        )
        return

    response = await send_to_webhook(payload)
    if response is None:
        return  # delivery failed, already logged

    text = (response.get("text") or "").strip()
    if not text:
        # n8n classified it as ad/skip — nothing to publish
        logger.info(
            "Skipped %s/%s (%s)",
            payload["source_channel"], payload["message_id"],
            payload.get("media_type") or "text",
        )
        return

    media_paths = [payload.get("local_path")] + payload.get("extra_media_paths", [])
    await publish_post(client, text, media_paths)
    logger.info(
        "Published %s/%s (%s)",
        payload["source_channel"], payload["message_id"],
        payload.get("media_type") or "text",
    )
