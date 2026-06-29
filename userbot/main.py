import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

from .client import create_client
from .handlers import register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    client = await create_client()
    register_handlers(client)
    logger.info("Userbot started. Listening for new posts...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
