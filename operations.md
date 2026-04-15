# QwenClaw — Журнал операций

## Что это
Персональный AI-ассистент в Telegram на базе Qwen Code CLI.
Установщик одной командой для Ubuntu/Debian VPS. Бесплатно (1000 запросов/день).
GitHub: https://github.com/a-prs/QwenClaw

## Текущее состояние (2026-04-13)
- Бот работает end-to-end: текстовые сообщения, голос (VOSK SERVER), сессии, встроенные кнопки
- Протестирован на чистом Ubuntu 24.04 VPS (1 vCPU, 1GB RAM)
- Установщик обрабатывает: Node.js 20, Qwen CLI, Python venv, systemd, OAuth
- Самообновление через команду /update (git pull + перезапуск из Telegram)
- Самонастройка голоса через команду /setup (VOSK SERVER через чат)

## Проблемы, решённые в ходе разработки

### Установщик
1. `curl|bash` ломает stdin → обнаружение pipe, просьба пользователю сначала скачать
2. NodeSource setup_20.x устарел на Ubuntu 24.04 → GPG-ключ + ручной репозиторий
3. Отсутствовали ca-certificates, gnupg → добавлены в apt install
4. `useradd -m` создаёт скелет → git clone падает → убран флаг -m
5. pip install слишком медленный, SSH обрывается → показ прогресса, проверка после установки
6. CRLF из Windows git → .gitattributes eol=lf + sed strip
7. npm global bin не в PATH → всегда symlink в /usr/local/bin/
8. .env читаем всеми → chmod 600
9. git pull от root в директории qwenbot → safe.directory

### Qwen CLI
1. Флаг `--max-turns` не существует → убран
2. `--auth-type qwen-oauth` требуется для неинтерактивного режима
3. `qwen auth qwen-oauth` (не `auth login --auth-type`)
4. JSON-вывод — массив `[{...}]`, не построчно → переписан парсер
5. OAuth на headless: работает через device flow (печатает URL, пользователь открывает в браузере)
6. OAuth требует 2 попытки: первая для регистрации, вторая для завершения OAuth

### Архитектура
1. Флаг is_busy теряет сообщения → очередь в памяти (5 сообщ.)
2. Root + --yolo опасно → выделенный пользователь qwenbot + песочница systemd
3. Markdown ломает Telegram HTML → md_to_telegram_html() + fallback

## Требования к серверу
- 1 vCPU, 512MB-1GB RAM, 5-10GB диск
- Ubuntu 22.04+ / Debian 11+
- GPU не нужен (весь AI — облачный)

## Команда установки
```
curl -fsSL https://raw.githubusercontent.com/a-prs/QwenClaw/main/install.sh -o /tmp/install.sh && sudo bash /tmp/install.sh
```
