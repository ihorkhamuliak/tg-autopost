import os
import logging
from telethon import TelegramClient

logger = logging.getLogger(__name__)

SESSION_PATH = os.getenv("SESSION_PATH", "/app/sessions/userbot")
API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
PHONE = os.environ["TELEGRAM_PHONE"]


async def create_client() -> TelegramClient:
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start(phone=PHONE)
    me = await client.get_me()
    logger.info("Logged in as %s (id=%s)", me.username or me.first_name, me.id)

    # Load dialogs so Telethon caches channel entities — without this the client
    # does not reliably receive new-post updates from broadcast channels.
    dialogs = await client.get_dialogs()
    logger.info("Loaded %d dialogs — update stream ready", len(dialogs))
    return client
