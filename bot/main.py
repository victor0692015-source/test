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

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is required")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def load_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


SYSTEM_PROMPT = load_text(PROMPT_PATH)
KNOWLEDGE_BASE = load_text(KB_PATH)

client = OpenAI(api_key=OPENAI_API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Здравствуйте! Я AI-ассистент Comoda IT Solution. "
        "Напишите ваш вопрос по услугам и сотрудничеству."
    )


async def ask_llm(user_message: str) -> str:
    response = client.responses.create(
        model=OPENAI_MODEL,
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
    try:
        answer = await ask_llm(user_text)
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
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
