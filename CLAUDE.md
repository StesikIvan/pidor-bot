# Pidor Bot

Telegram-бот "пидор дня" для группового чата. Всегда выбирает Максима (@Gutter999).

## Стек
- Python 3.11
- python-telegram-bot 22.7+ (async, polling)
- SQLite (через database.py)
- Docker + docker-compose для деплоя

## Структура
- `bot.py` — основной файл бота
- `database.py` — работа с SQLite (DB_PATH из env, по умолчанию pidor.db)
- `docker-compose.yml` — запуск через Docker с автоперезапуском
- `Dockerfile` — образ на python:3.11-slim
- `.env` — BOT_TOKEN и OWNER_ID (не в репо)
- `data/pidor.db` — база данных (создаётся автоматически, не в репо)

## Переменные окружения (.env)
```
BOT_TOKEN=<токен бота>
OWNER_ID=<telegram id владельца>
DB_PATH=/app/data/pidor.db
```

## Запуск через Docker (основной способ)
```bash
# Первый запуск
docker compose up -d --build

# Посмотреть логи
docker compose logs -f

# Остановить
docker compose down

# Перезапустить
docker compose restart
```

## Запуск локально (без Docker)
```bash
pip install -r requirements.txt
python bot.py
```

## Деплой на Render (резервный, не основной)
- Сервис: pidor-bot-9qmz.onrender.com
- ID: srv-d88ct87avr4c73e8e7o0
- Keepalive через GitHub Actions (.github/workflows/keepalive.yml)

## Команды бота
- `/pidor` — выбрать пидора дня (всегда Максим @Gutter999)
- `/pidorstats` — статистика за текущий год
- `/pidoralltimestats` — статистика за всё время

## Команды владельца (только в личке)
- `/chats` — список групп
- `/listusers <chat_id>` — участники группы
- `/setchoice <chat_id> <user_id>` — назначить следующего пидора
- `/clearchoice <chat_id>` — сбросить назначение
- `/whosnext <chat_id>` — кто назначен следующим

## Важные детали
- Privacy mode у бота отключён (через BotFather → /setprivacy → Disable)
- Бот всегда выбирает user_id=0 с username="Gutter999" (не реальный user_id)
- Сброс пидора дня в 00:00 по московскому времени
- Команда /pidor удаляет исходное сообщение
