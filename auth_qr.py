import asyncio, os
from pathlib import Path
from dotenv import load_dotenv
from telethon import TelegramClient
import qrcode

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

SESSION_PATH = "/app/sessions/userbot"

async def main():
    client = TelegramClient(
        SESSION_PATH,
        int(os.environ["TELEGRAM_API_ID"]),
        os.environ["TELEGRAM_API_HASH"]
    )
    await client.connect()

    if await client.is_user_authorized():
        me = await client.get_me()
        print(f"Вже авторизовано як: {me.username or me.first_name}")
        await client.disconnect()
        return

    print("Скануй QR-код у Telegram: Налаштування → Пристрої → Підключити пристрій")
    print()

    qr_login = await client.qr_login()

    qr = qrcode.QRCode()
    qr.add_data(qr_login.url)
    qr.print_ascii(invert=True)

    try:
        await qr_login.wait(timeout=60)
        me = await client.get_me()
        print(f"\nУспішно! Авторизовано як: {me.username or me.first_name} (id={me.id})")
        print("Сесія збережена. Тепер можна запускати userbot.main")
    except Exception as e:
        print(f"Помилка або час вийшов: {e}")
        print("Спробуй ще раз")

    await client.disconnect()

asyncio.run(main())
