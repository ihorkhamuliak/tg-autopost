import os
import logging
from telethon.tl.types import (
    MessageMediaPhoto,
    MessageMediaDocument,
    DocumentAttributeVideo,
    DocumentAttributeAnimated,
    DocumentAttributeAudio,
    DocumentAttributeSticker,
)

logger = logging.getLogger(__name__)

MEDIA_DIR = os.getenv("MEDIA_DIR", "/app/media")
MAX_DOWNLOAD_BYTES = int(os.getenv("MAX_DOWNLOAD_SIZE_MB", "50")) * 1024 * 1024

os.makedirs(MEDIA_DIR, exist_ok=True)


async def extract_media_info(message) -> dict:
    if not message.media:
        return {}

    try:
        if isinstance(message.media, MessageMediaPhoto):
            path = await message.download_media(
                file=os.path.join(MEDIA_DIR, f"{message.id}.jpg")
            )
            return {"type": "photo", "local_path": path}

        if isinstance(message.media, MessageMediaDocument):
            doc = message.media.document
            media_type, ext = _classify_document(doc)

            if doc.size > MAX_DOWNLOAD_BYTES:
                logger.info(
                    "Skipping download for %s: %s bytes > limit", message.id, doc.size
                )
                return {"type": media_type, "local_path": None, "size": doc.size}

            path = await message.download_media(
                file=os.path.join(MEDIA_DIR, f"{message.id}.{ext}")
            )
            return {"type": media_type, "local_path": path, "size": doc.size}

    except Exception:
        logger.exception("Failed to extract media for message %s", message.id)

    return {"type": "unknown", "local_path": None}


def _classify_document(doc) -> tuple[str, str]:
    for attr in doc.attributes:
        if isinstance(attr, DocumentAttributeSticker):
            return "sticker", "webp"
        if isinstance(attr, DocumentAttributeAnimated):
            return "animation", "gif"
        if isinstance(attr, DocumentAttributeVideo):
            return "video", "mp4"
        if isinstance(attr, DocumentAttributeAudio):
            return ("voice", "ogg") if attr.voice else ("audio", "mp3")
    return "document", "bin"
