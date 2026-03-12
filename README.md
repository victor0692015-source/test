# Comoda IT Solution Telegram Assistant

Готовый минимальный проект, чтобы запустить Telegram-бота первой линии поддержки на Python.

## Что в репозитории

- `prompts/system_prompt_ru.md` — системный промпт ассистента.
- `knowledge_base/comoda_profile_ru.md` — база знаний по компании.
- `bot/main.py` — Telegram-бот, который передает вопросы в LLM и отвечает клиенту.
- `.env.example` — пример переменных окружения.
- `requirements.txt` — зависимости Python.
- `scripts/run.sh` — быстрый старт локально.

## 1) Как подключить к Telegram

1. Откройте **@BotFather** в Telegram.
2. Выполните `/newbot`, задайте имя и username.
3. Скопируйте токен бота (формат: `123456:ABC...`).
4. Вставьте токен в `.env` как `TELEGRAM_BOT_TOKEN`.

## 2) Как запустить локально

```bash
./scripts/run.sh
# затем заполните .env
source .venv/bin/activate
python bot/main.py
```

После запуска бот работает в режиме **long polling** (без webhook), этого достаточно для VPS/сервера.

## 3) Настройка `.env`

Создайте `.env` (можно скопировать из `.env.example`):

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

## 4) Деплой на сервер (Ubuntu)

### Установка

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

### Запуск проекта

```bash
git clone <ваш-репозиторий>
cd test
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# заполните .env
python bot/main.py
```

## 5) Автозапуск через systemd

Создайте `/etc/systemd/system/comoda-bot.service`:

```ini
[Unit]
Description=Comoda Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/test
ExecStart=/home/ubuntu/test/.venv/bin/python /home/ubuntu/test/bot/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Далее:

```bash
sudo systemctl daemon-reload
sudo systemctl enable comoda-bot
sudo systemctl start comoda-bot
sudo systemctl status comoda-bot
```

## Как это работает

- Бот читает системный промпт и базу знаний из файлов репозитория.
- На каждое сообщение клиента делает запрос к LLM.
- Ограничения и стиль ответа управляются содержимым `prompts/` и `knowledge_base/`.

> Важно: если вы обновляете правила общения или услуги компании, меняйте только файлы в `prompts/` и `knowledge_base/` — код бота обычно трогать не нужно.
