## Ядро бота
bot/main.py                    — Telegram-бот: aiogram 3.x, обработчики, клавиатуры, управление сессиями
  :cmd_start()                 — Приветствие /start со статусом голоса
  :cmd_menu()                  — Панель управления /menu
  :cmd_new()                   — /new принудительно новая сессия
  :cmd_sessions()              — /sessions список сессий
  :cmd_status()                — /status информация о системе
  :cmd_setup()                 — /setup настройка VOSK SERVER через чат
  :cmd_update()                — /update самообновление с GitHub + перезапуск
  :handle_message()            — Главный обработчик: извлечение текста -> маршрутизация -> запуск qwen
  :on_result()                 — Обратный вызов по завершении Qwen: отправка результата в Telegram
  :extract_text()              — Извлечение текста/голоса/подписи
  :build_main_menu()           — Встроенная клавиатура: сессии, новая, статус, закрыть все
  :build_sessions_keyboard()   — Постраничный список сессий с кнопками переключения/закрытия
  ПРИМЕЧАНИЕ: Кнопки на ответах используют edit_text, который заменяет ответ — требует исправления

bot/qwen_runner.py             — Запуск Qwen Code CLI как подпроцесс
  :run_qwen()                  — Публичный API: очередь или запуск qwen
  :_process_prompt()           — Выполнение + осушение очереди
  :_execute_qwen()             — Формирование команды, подпроцесс, парсинг JSON
  :_parse_output()             — Парсинг JSON-массива Qwen [{type:result}]
  ПРИМЕЧАНИЕ: Qwen выводит JSON-массив, НЕ построчно как Claude
  ПРИМЕЧАНИЕ: --max-turns НЕ поддерживается Qwen CLI
  ПРИМЕЧАНИЕ: --auth-type qwen-oauth требуется для каждого вызова

bot/config.py                  — Загрузчик .env + динамическое обновление конфига
  :set_env_var()               — Запись key=value в файл .env
  :reload_vosk_config()        — Горячая перезагрузка VOSK_SERVER config без перезапуска

bot/db.py                      — SQLite: сессии + история сообщений
  :init_db()                   — Версионирование схемы через PRAGMA user_version
  :create_session()            — INSERT OR IGNORE
  :get_active_sessions()       — Не завершённые, в пределах таймаута

bot/formatting.py              — Конвертер Markdown -> Telegram HTML
  :md_to_telegram_html()       — Сначала извлекает блоки кода, экранирует HTML, конвертирует жирный/курсив/ссылки
  :split_message()             — Разбиение сообщений >4000 символов по переводам строки
  ПРИМЕЧАНИЕ: При TelegramBadRequest возвращается plain text

bot/voice.py                   — Транскрипция через VOSK SERVER
  :transcribe_voice()          — Загрузка .ogg из TG, конвертация ffmpeg, POST в VOSK SERVER
  ПРИМЕЧАНИЕ: Требуется ffmpeg для конвертации OGG→WAV 16kHz

bot/scheduler.py               — Планировщик наподобие cron, читает workspace/schedules.json
  :run_scheduler()             — Цикл asyncio, проверка каждые 30с
  :_cron_matches()             — Парсер cron из 5 полей (минута час день месяц день_недели)
  :get_due_tasks()             — Поиск задач, совпадающих с текущим временем
  ПРИМЕЧАНИЕ: Qwen записывает schedules.json по инструкциям из QWEN.md

## Рабочая область
workspace/QWEN.md              — Идентичность + инструкции для Qwen Code (читается при каждом запуске)
workspace/.qwen/skills/schedule/SKILL.md — Навык планирования для cron на естественном языке

## Развёртывание
install.sh                     — Установщик одной командой для Ubuntu/Debian VPS
  ПРИМЕЧАНИЕ: Обнаруживает pipe (curl|bash) и просит пользователя сначала скачать
  ПРИМЕЧАНИЕ: Использует `qwen auth qwen-oauth` (не `auth login --auth-type`)
  ПРИМЕЧАНИЕ: .gitattributes принудительно LF для .sh файлов (Windows CRLF ломает bash)
qwenbot.service                — systemd unit с песочницей (ProtectSystem, ProtectHome)
  ПРИМЕЧАНИЕ: HOME=/opt/qwenbot установлен явно для доступа к учётным данным Qwen
.env.example                   — Шаблон

## Ключевые решения
- Qwen Code CLI как бэкенд (бесплатно 1000 запросов/день, headless через --auth-type qwen-oauth)
- VOSK SERVER для голоса (локальное распознавание речи через ffmpeg)
- Очередь сообщений в памяти (не SQLite — одно-пользовательский бот, макс 5 сообщ.)
- HTML parse_mode (не Markdown — меньше проблем с экранированием в Telegram)
- Планировщик читает schedules.json, который Qwen сам записывает (cron на естественном языке)
- Выделенный системный пользователь qwenbot (не root) с песочницей systemd
