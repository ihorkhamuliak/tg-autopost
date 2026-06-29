[English](README.md) | **Українська**

# tg-autopost — Userbot

Telethon-userbot для реалтайм-ретрансляції новин із каналів-джерел у n8n (класифікація + рерайт + дедуплікація), з публікацією тексту й медіа в цільовий Telegram-канал.

---

## Структура проєкту

```
tg-autopost/
├── userbot/
│   ├── main.py        # Точка входу
│   ├── client.py      # Авторизація Telethon
│   ├── handlers.py    # Обробники нових постів (single + album)
│   ├── media.py       # Завантаження медіа на диск
│   ├── dedup.py       # Смислова дедуплікація (OpenAI embeddings)
│   ├── publisher.py   # Публікація тексту + медіа в канал
│   └── webhook.py     # POST у n8n з retry
├── prompts/
│   ├── classifier.txt # Промпт-класифікатор
│   └── rewriter.txt   # Промпт-рерайтер
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## 1. Отримати api_id / api_hash

1. Зайди на **my.telegram.org** з SIM-картки userbot-акаунта
2. → "API development tools"
3. Заповни форму (назва довільна, наприклад `userbot_news`)
4. Скопіюй `App api_id` (число) і `App api_hash` (рядок)

---

## 2. Отримати Channel ID (приватний канал)

Бот-публікатор вже в каналі як адмін. Зроби так:
1. Напиши будь-яке повідомлення у свій канал через акаунт адміна
2. Перешли це повідомлення боту `@userinfobot`
3. Отримаєш `Forwarded from chat #XXXXXXXXXX` — це і є числовий ID
4. В .env пиши зі знаком мінус: `CHANNEL_ID=-100XXXXXXXXXX`

---

## 3. Налаштування .env

```bash
cp .env.example .env
# Заповни всі поля у .env
```

Ніколи не комить `.env` у git — він вже в `.gitignore`.

---

## 4. Перший запуск (локально для авторизації)

```bash
pip install -r requirements.txt
cd userbot
python main.py
```

При першому запуску Telethon попросить:
- номер телефону (в форматі `+380...`)
- код підтвердження із SMS/Telegram
- пароль 2FA (якщо є)

Після авторизації файл `sessions/userbot.session` збережеться — він потрібен для Docker.

---

## 5. Запуск через Docker (на VPS)

### Варіант A — окремий контейнер

```bash
# Скопіювати .env і папку sessions/ на VPS
docker build -t tg-userbot .
docker run -d \
  --name tg-userbot \
  --env-file .env \
  -v $(pwd)/sessions:/app/sessions \
  -v $(pwd)/media:/app/media \
  --restart unless-stopped \
  tg-userbot
```

### Варіант B — додати до docker-compose n8n

Додай у свій `docker-compose.yml` (де вже є n8n):

```yaml
  tg-userbot:
    build: ./tg-autopost
    env_file: ./tg-autopost/.env
    volumes:
      - ./sessions:/app/sessions
      - ./media:/app/media      # Спільний том з n8n для передачі файлів
    restart: unless-stopped
    networks:
      - n8n_network             # Та сама мережа що й n8n
```

**Важливо:** якщо використовуєш спільний том `media` — в n8n можна читати медіафайли через "Read Binary File" node за шляхом `/app/media/{message_id}.jpg`.

---

## 6. Payload що летить у n8n

```json
{
  "source_channel": "source_channel_1",
  "message_id": 12345,
  "text": "Текст посту...",
  "has_media": true,
  "media_type": "photo",
  "local_path": "/app/media/12345.jpg",
  "is_album": false,
  "extra_media_paths": [],
  "date": "2026-06-22T17:56:00+00:00"
}
```

Для альбомів: `is_album: true`, `extra_media_paths` містить шляхи до решти фото/відео.

---

## 7. Промпти для n8n

Файли `prompts/classifier.txt` і `prompts/rewriter.txt` — вставляй у відповідні ноди.

У `rewriter.txt` є плейсхолдер `{style_examples}` — сюди вставиш 5-10 прикладів постів цільового каналу (для стилю).

---

## 8. Змінні середовища — довідник

| Змінна | Опис |
|--------|------|
| `TELEGRAM_API_ID` | З my.telegram.org |
| `TELEGRAM_API_HASH` | З my.telegram.org |
| `TELEGRAM_PHONE` | Номер userbot `+380...` |
| `SOURCE_CHANNELS` | Канали-джерела без @, через кому |
| `N8N_WEBHOOK_URL` | URL з Webhook node в n8n |
| `CHANNEL_ID` | Числовий ID цільового каналу |
| `CHANNEL_LINK` | Посилання для футера |
| `CHANNEL_NAME` | Назва для футера |
| `BOT_TOKEN` | Токен бота-публікатора |
| `OPENAI_API_KEY` | Ключ OpenAI |
| `MAX_DOWNLOAD_SIZE_MB` | Ліміт завантаження медіа (default 50) |
| `POST_PROCESS_DELAY_SEC` | Пауза між постами (default 1.5) |
