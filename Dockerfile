FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY userbot/ ./userbot/

# Volumes: sessions (Telethon .session file) + media (downloaded files for n8n)
VOLUME ["/app/sessions", "/app/media"]

CMD ["python", "-m", "userbot.main"]
