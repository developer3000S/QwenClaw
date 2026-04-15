# QwenClaw — Контекст проекта

## Обзор проекта

**QwenClaw** (aka **QwenBot**) — персональный AI-ассистент, работающий как Telegram-бот на базе **Qwen Code CLI**. Предоставляет бесплатную альтернативу платным AI-чатботам с до 1000 запросов/день через бесплатный тариф Qwen. Бот предназначен для работы на VPS Ubuntu/Debian как systemd-сервис от выделенного пользователя `qwenbot`.

### Ключевые возможности
- **Telegram-чат** с Qwen Code AI (текст, голос, фото)
- **Управление сессиями** — создание, переключение, закрытие, список активных сессий
- **Голосовые сообщения** через VOSK SERVER (опционально)
- **Планировщик задач** — cron-записи на естественном языке в `schedules.json`
- **Анализ фото** — загрузка и передача путей к изображениям в Qwen для зрения
- **Самообновление** — команда `/update` загружает с GitHub и перезапускает
- **Безопасность** — один пользователь (только админ), песочница systemd, запуск не от root

### Архитектура

```
/opt/qwenbot/                     (директория установки на VPS)
  bot/
    main.py          — Telegram-бот (aiogram 3.x), все обработчики и клавиатуры
    qwen_runner.py   — Запуск Qwen Code CLI как подпроцесс с очередью в памяти
    voice.py         — Транскрипция через VOSK SERVER
    formatting.py    — Конвертер Markdown в Telegram HTML
    config.py        — Загрузчик .env + динамическое обновление
    db.py            — SQLite: сессии и история сообщений
    scheduler.py     — Планировщик наподобие cron для schedules.json
  workspace/         — Рабочая директория Qwen Code (файлы, schedules.json)
  data/              — База данных SQLite (bot.db)
  .env               — конфигурация (TELEGRAM_BOT_TOKEN и т.д.)
  qwenbot.service    — Файл systemd unit
```

## Стек технологий

| Слой | Технология |
|---|---|
| Фреймворк бота | aiogram 3.x (async) |
| AI бэкенд | Qwen Code CLI (`@qwen-code/qwen-code` через npm) |
| Голос | VOSK SERVER (локальное распознавание) |
| Хранилище | SQLite (сессии + история) |
| Планировщик | Кастомный парсер cron, опрос каждые 30с |
| Развёртывание | systemd, Python venv, Node.js 20.x |
| Язык | Python 3.x |

## Сборка и запуск

### Требования
- VPS Ubuntu/Debian
- Токен бота Telegram от [@BotFather](https://t.me/BotFather)
- Chat ID Telegram от [@userinfobot](https://t.me/userinfobot)
- Node.js >= 18 (для Qwen Code CLI)

### Установка одной командой
```bash
curl -fsSL https://raw.githubusercontent.com/a-prs/QwenClaw/main/install.sh -o /tmp/install.sh && sudo bash /tmp/install.sh
```

Установщик обрабатывает: Node.js, Qwen Code CLI, Python venv, зависимости, OAuth auth, настройку systemd.

### Ручное управление
```bash
systemctl status qwenbot     # проверить статус
systemctl restart qwenbot    # перезапустить
journalctl -u qwenbot -f     # просмотр логов
```

### Обновление
```bash
cd /opt/qwenbot && git pull && systemctl restart qwenbot
# Или через Telegram: /update
```

### Запуск локально (разработка)
```bash
cd /opt/qwenbot
source .venv/bin/activate
cd bot && python main.py
```

## Конфигурация

Переменные окружения в `/opt/qwenbot/.env`:

| Переменная | Обязательная | По умолчанию | Описание |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | да | — | Токен бота от @BotFather |
| `TELEGRAM_CHAT_ID` | да | — | ID пользователя Telegram админа (только этот пользователь может взаимодействовать) |
| `VOSK_SERVER_HOST` | нет | `127.0.0.1` | Хост VOSK SERVER для транскрипции голоса |
| `VOSK_SERVER_PORT` | нет | `2700` | Порт VOSK SERVER |
| `QWEN_MAX_TURNS` | нет | 15 | Макс. итераций AI на запрос |
| `QWEN_TIMEOUT` | нет | 600 | Таймаут подпроцесса Qwen (секунды) |
| `QWEN_BIN` | нет | `qwen` | Путь к бинарнику Qwen Code CLI |
| `QWEN_WORK_DIR` | нет | `workspace/` | Рабочая директория для Qwen Code |

## Команды Telegram

| Команда | Описание |
|---|---|
| `/start` | Приветствие + главное меню |
| `/menu` | Панель управления |
| `/new` | Принудительно новая сессия |
| `/sessions` | Список активных сессий |
| `/status` | Статус системы |
| `/setup` | Настройка VOSK SERVER |
| `/update` | Самообновление с GitHub + перезапуск |

## Соглашения по разработке

### Стиль кода
- Python 3.x с аннотациями типов где уместно
- Async/await повсюду (aiogram 3.x полностью асинхронный)
- Логирование через `logging.getLogger("bot")`, `logging.getLogger("qwen_runner")` и т.д.
- Конфигурация централизована в `config.py`, загружается из `.env` через `python-dotenv`

### Интеграция с Qwen CLI
- Qwen Code CLI вызывается как подпроцесс с `--output-format json --yolo --auth-type qwen-oauth`
- Вывод — JSON-массив: `[{type:system}, {type:assistant}, ..., {type:result}]`
- Раннер парсит последний объект где `type=result` и `subtype=success`
- `--resume <session_id>` используется для непрерывности сессии
- Флаг `--yolo` пропускает подтверждение для автоматического выполнения

### Управление сессиями
- Сессии хранятся в SQLite (`data/bot.db`) со статусами: `idle`, `active`, `done`
- Таймаут неактивности: 48 часов (настраивается через `SESSION_IDLE_TIMEOUT_HOURS`)
- В памяти `user_focus` отслеживает, с какой сессией сейчас взаимодействует пользователь
- Сентинель `"__force_new__"` запускает создание новой сессии

### Очередь сообщений
- Очередь в памяти (макс. 5 сообщений) когда Qwen занят
- Без SQLite очереди — дизайн для одного пользователя, простой подход на основе списка
- Позиция в очереди показывается пользователю через индикатор набора

### Транскрипция голоса
- Используется VOSK SERVER через HTTP API
- Загружает `.ogg` из Telegram, конвертирует в WAV 16kHz через ffmpeg, отправляет на VOSK SERVER
- VOSK_SERVER_HOST и VOSK_SERVER_PORT загружаются из .env
- Возвращает дружественные сообщения об ошибках на русском при неудаче

### Форматирование
- Конвертация Markdown в Telegram HTML обрабатывает: блоки кода, встроенный код, жирный, курсив, зачёркнутый, ссылки, заголовки, цитаты
- HTML-сущности экранируются в тексте, но сохраняются внутри блоков кода
- Сообщения разбиваются по переводам строки если > 4000 символов (лимит Telegram: 4096)

## Справочник ключевых файлов

| Файл | Назначение |
|---|---|
| `bot/main.py` | Точка входа, все обработчики Telegram, встроенные клавиатуры, маршрутизация сообщений |
| `bot/qwen_runner.py` | Выполнение подпроцесса `qwen` CLI, парсинг JSON, управление очередью |
| `bot/config.py` | Загрузка `.env`, динамическая запись переменных, горячая перезагрузка |
| `bot/db.py` | Схема SQLite, CRUD сессий, история сообщений |
| `bot/formatting.py` | Markdown → Telegram HTML, разбиение сообщений |
| `bot/voice.py` | Интеграция с VOSK SERVER |
| `bot/scheduler.py` | Парсер cron, чтение schedules.json, цикл выполнения задач |
| `workspace/QWEN.md` | Системный промпт / идентичность для Qwen Code (читается при каждом запуске) |
| `install.sh` | Установщик одной командой для Ubuntu/Debian |
| `qwenbot.service` | Файл systemd unit с песочницей (ProtectSystem, ProtectHome) |
| `.env.example` | Шаблон конфигурации |
