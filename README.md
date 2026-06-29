**English** | [Українська](README_UA.md)

# tg-autopost — Telegram Userbot

A Telethon userbot that relays posts from source Telegram channels into n8n in real time (classify + rewrite + deduplicate), then publishes the text and media to a target Telegram channel.

---

## Project structure

```
tg-autopost/
├── userbot/
│   ├── main.py        # Entry point
│   ├── client.py      # Telethon authentication
│   ├── handlers.py    # New post handlers (single + album)
│   ├── media.py       # Download media to disk
│   ├── dedup.py       # Semantic deduplication (OpenAI embeddings)
│   ├── publisher.py   # Publish text + media to the channel
│   └── webhook.py     # POST to n8n with retry
├── prompts/
│   ├── classifier.txt # Classifier prompt
│   └── rewriter.txt   # Rewriter prompt
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 1. Get api_id / api_hash

1. Go to **my.telegram.org** from the userbot account's SIM card
2. → "API development tools"
3. Fill in the form (any app name, e.g. `userbot_news`)
4. Copy `App api_id` (number) and `App api_hash` (string)

---

## 2. Get the Channel ID (private channel)

The publisher bot is already an admin in the channel. Then:
1. Send any message to your channel from the admin account
2. Forward that message to `@userinfobot`
3. You'll get `Forwarded from chat #XXXXXXXXXX` — that's the numeric ID
4. In `.env` use it with a minus sign: `CHANNEL_ID=-100XXXXXXXXXX`

---

## 3. Configure .env

```bash
cp .env.example .env
# Fill in all fields in .env
```

Never commit `.env` to git — it's already in `.gitignore`.

---

## 4. First run (locally, to authenticate)

```bash
pip install -r requirements.txt
cd userbot
python main.py
```

On the first run Telethon will ask for:
- phone number (format `+380...`)
- confirmation code from SMS/Telegram
- 2FA password (if set)

After login a `sessions/userbot.session` file is saved — it's needed for Docker.

---

## 5. Run with Docker (on a VPS)

### Option A — standalone container

```bash
# Copy .env and the sessions/ folder to the VPS
docker build -t tg-userbot .
docker run -d \
  --name tg-userbot \
  --env-file .env \
  -v $(pwd)/sessions:/app/sessions \
  -v $(pwd)/media:/app/media \
  --restart unless-stopped \
  tg-userbot
```

### Option B — add to the n8n docker-compose

Add to your existing `docker-compose.yml` (where n8n already runs):

```yaml
  tg-userbot:
    build: ./tg-autopost
    env_file: ./tg-autopost/.env
    volumes:
      - ./sessions:/app/sessions
      - ./media:/app/media      # Shared volume with n8n to pass files
    restart: unless-stopped
    networks:
      - n8n_network             # Same network as n8n
```

**Note:** with a shared `media` volume, n8n can read media files via a "Read Binary File" node at `/app/media/{message_id}.jpg`.

---

## 6. Payload sent to n8n

```json
{
  "source_channel": "source_channel_1",
  "message_id": 12345,
  "text": "Post text...",
  "has_media": true,
  "media_type": "photo",
  "local_path": "/app/media/12345.jpg",
  "is_album": false,
  "extra_media_paths": [],
  "date": "2026-06-22T17:56:00+00:00"
}
```

For albums: `is_album: true`, and `extra_media_paths` holds the paths to the remaining photos/videos.

---

## 7. Prompts for n8n

Paste `prompts/classifier.txt` and `prompts/rewriter.txt` into the matching nodes.

`rewriter.txt` has a `{style_examples}` placeholder — put 5–10 sample posts from the target channel there (to capture its style).

---

## 8. Environment variables — reference

| Variable | Description |
|----------|-------------|
| `TELEGRAM_API_ID` | From my.telegram.org |
| `TELEGRAM_API_HASH` | From my.telegram.org |
| `TELEGRAM_PHONE` | Userbot number `+380...` |
| `SOURCE_CHANNELS` | Source channels without @, comma-separated |
| `N8N_WEBHOOK_URL` | URL from the n8n Webhook node |
| `CHANNEL_ID` | Numeric ID of the target channel |
| `CHANNEL_LINK` | Link for the footer |
| `CHANNEL_NAME` | Name for the footer |
| `BOT_TOKEN` | Publisher bot token |
| `OPENAI_API_KEY` | OpenAI key |
| `MAX_DOWNLOAD_SIZE_MB` | Media download limit (default 50) |
| `POST_PROCESS_DELAY_SEC` | Delay between posts (default 1.5) |

---

> ⚠️ This is a depersonalized portfolio copy. Channel names, IDs and secrets are placeholders.
