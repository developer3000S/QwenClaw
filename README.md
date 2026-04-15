# QwenBot

Персональный AI-ассистент в Telegram на базе Qwen Code.

**Бесплатно**: 1000 запросов/день, без подписок.

## Что умеет

- Общение с Qwen Code AI через Telegram
- Управление сессиями (создание, переключение, закрытие)
- Голосовые сообщения (через VOSK SERVER, опционально)
- HTML-форматирование для блоков кода и структурированных ответов
- Автозапуск через systemd

## Установка (3 шага)

### Требования
- VPS на Ubuntu/Debian
- Токен бота Telegram от [@BotFather](https://t.me/BotFather)
- Ваш Chat ID от [@userinfobot](https://t.me/userinfobot)

### Установка одной командой

```bash
curl -fsSL https://raw.githubusercontent.com/a-prs/QwenClaw/main/install.sh -o /tmp/install.sh && sudo bash /tmp/install.sh
```

Установщик:
1. Установит Node.js, Python, Qwen Code CLI
2. Запросит токен бота Telegram и Chat ID
3. (Опционально) Настроит VOSK SERVER для голосовых сообщений
4. Авторизует Qwen Code
5. Настроит и запустит бота

### Голосовые сообщения (опционально)

Для локального распознавания речи используется VOSK SERVER.

Убедитесь что VOSK SERVER запущен на вашем сервере (по умолчанию на `127.0.0.1:2700`),
или настройте через `/setup` в боте:

```
VOSK_SERVER_HOST=127.0.0.1
VOSK_SERVER_PORT=2700
```

Затем перезапустите: `systemctl restart qwenbot`

## Использование

Просто отправьте сообщение вашему боту в Telegram.

**Команды:**
- `/menu` — панель управления
- `/new` — начать новую сессию
- `/sessions` — список сессий
- `/status` — статус системы

**Встроенные кнопки** для переключения сессий, закрытия и навигации.

## Обновление

```bash
cd /opt/qwenbot && git pull && systemctl restart qwenbot
```

## Управление

```bash
systemctl status qwenbot     # проверить статус
systemctl restart qwenbot    # перезапустить
journalctl -u qwenbot -f     # просмотр логов
```

## Конфигурация

Отредактируйте `/opt/qwenbot/.env`:

| Переменная | Обязательная | Описание |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | да | Токен бота от @BotFather |
| `TELEGRAM_CHAT_ID` | да | ID вашего пользователя Telegram |
| `VOSK_SERVER_HOST` | нет | Хост VOSK SERVER для голосовых |
| `VOSK_SERVER_PORT` | нет | Порт VOSK SERVER (по умолчанию: 2700) |
| `QWEN_MAX_TURNS` | нет | Макс. итераций AI (по умолчанию: 15) |
| `QWEN_TIMEOUT` | нет | Таймаут в секундах (по умолчанию: 600) |

## Архитектура

```
GitHub: https://github.com/a-prs/QwenClaw

/opt/qwenbot/
  bot/
    main.py          — Telegram-бот (aiogram 3.x)
    qwen_runner.py   — Запуск Qwen Code CLI как подпроцесс
    voice.py         — VOSK SERVER для голоса
    formatting.py    — Markdown в Telegram HTML
    config.py        — загрузчик .env
    db.py            — SQLite: сессии и история
  workspace/         — Рабочая директория Qwen Code
  data/              — База данных SQLite
  .env               — конфигурация
```

## Безопасность

- Один пользователь: только ваш Chat ID может взаимодействовать
- Работает от системного пользователя `qwenbot` (не root)
- Песочница systemd: ProtectSystem, ProtectHome, NoNewPrivileges

## Лицензия

MIT
