import os
import logging
from telethon import TelegramClient

logger = logging.getLogger(__name__)

CHANNEL_ID = int(os.environ["CHANNEL_ID"])

# Telegram limits: caption max 1024 chars, plain message max 4096
CAPTION_LIMIT = 1024


async def publish_post(client: TelegramClient, text: str, media_paths: list[str]):
    """Publish the rewritten post (text + media) to the target channel."""
    paths = [p for p in media_paths if p]

    if not paths:
        await client.send_message(CHANNEL_ID, text, parse_mode="html", link_preview=False)
        logger.info("Published text-only post to %s", CHANNEL_ID)
        return

    if len(text) <= CAPTION_LIMIT:
        # Caption fits — send media with the text attached (single post / album)
        await client.send_file(CHANNEL_ID, paths, caption=text, parse_mode="html")
    else:
        # Too long for a caption — send media first, then the text as a reply
        sent = await client.send_file(CHANNEL_ID, paths)
        await client.send_message(
            CHANNEL_ID, text, parse_mode="html", link_preview=False, reply_to=sent[0] if isinstance(sent, list) else sent
        )
    logger.info("Published post with %d media file(s) to %s", len(paths), CHANNEL_ID)
