import asyncio, os
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

SOURCE = [c.strip() for c in os.getenv("SOURCE_CHANNELS", "").split(",") if c.strip()]

async def main():
    client = TelegramClient(
        "/app/sessions/userbot",
        int(os.environ["TELEGRAM_API_ID"]),
        os.environ["TELEGRAM_API_HASH"],
    )
    await client.connect()

    print("=== Перевірка каналів зі SOURCE_CHANNELS ===\n")
    for username in SOURCE:
        try:
            ent = await client.get_entity(username)
            title = getattr(ent, "title", "?")
            real_username = getattr(ent, "username", None)
            print(f"[OK]   '{username}' -> {title} (@{real_username}, id={ent.id})")
        except Exception as e:
            print(f"[FAIL] '{username}' -> {type(e).__name__}: {e}")

    print("\n=== Канали на які реально підписаний акаунт ===\n")
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            uname = getattr(dialog.entity, "username", None)
            print(f"  {dialog.name}  (@{uname})")

    await client.disconnect()

asyncio.run(main())
