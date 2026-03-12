import argparse
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPT_PATH = BASE_DIR / "prompts" / "system_prompt_ru.md"
KB_PATH = BASE_DIR / "knowledge_base" / "comoda_profile_ru.md"
DEFAULT_ENV_PATH = BASE_DIR / ".env"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def load_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Comoda Telegram AI assistant")
    parser.add_argument(
        "--env-file",
        default=str(DEFAULT_ENV_PATH),
        help="Path to .env file (default: project-root/.env)",
    )
    parser.add_argument("--telegram-token", default=None, help="Telegram bot token")
    parser.add_argument("--openai-api-key", default=None, help="OpenAI API key")
    parser.add_argument("--openai-model", default=None, help="OpenAI model override")
    return parser


def get_required_value(name: str, cli_value: str | None, env_path: Path) -> str:
    if cli_value:
        return cli_value

    env_value = os.getenv(name)
    if env_value:
        return env_value

    raise RuntimeError(
        f"{name} is required.\n"
        f"Вариант 1: передайте через аргумент --{name.lower().replace('_', '-')}\n"
        f"Вариант 2: создайте файл {env_path} (можно скопировать из .env.example) и добавьте {name}=..."
    )


SYSTEM_PROMPT = load_text(PROMPT_PATH)
KNOWLEDGE_BASE = load_text(KB_PATH)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Здравствуйте! Я AI-ассистент Comoda IT Solution. "
        "Напишите ваш вопрос по услугам и сотрудничеству."
    )


async def ask_llm(user_message: str, client: OpenAI, model: str) -> str:
    response = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "system",
                "content": "Ниже база знаний. Используй только эту информацию.\n\n" + KNOWLEDGE_BASE,
            },
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
    )
    return response.output_text.strip()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip()
    client: OpenAI = context.bot_data["openai_client"]
    model: str = context.bot_data["openai_model"]

    try:
        answer = await ask_llm(user_text, client, model)
    except Exception:
        logger.exception("LLM request failed")
        answer = (
            "Сейчас не получилось обработать запрос. "
            "Чтобы дать точный ответ, лучше уточнить детали у специалиста. "
            "Я могу передать ваш запрос менеджеру."
        )

    await update.message.reply_text(answer)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Я могу ответить на вопросы о компании Comoda IT Solution, услугах и сотрудничестве."
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    env_path = Path(args.env_file).expanduser().resolve()
    load_dotenv(dotenv_path=env_path)

    telegram_token = get_required_value("TELEGRAM_BOT_TOKEN", args.telegram_token, env_path)
    openai_api_key = get_required_value("OPENAI_API_KEY", args.openai_api_key, env_path)
    openai_model = args.openai_model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    application = Application.builder().token(telegram_token).build()
    application.bot_data["openai_client"] = OpenAI(api_key=openai_api_key)
    application.bot_data["openai_model"] = openai_model

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
