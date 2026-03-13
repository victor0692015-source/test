from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, time, timedelta

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from storage import TaskStorage

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN", "")
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Europe/Moscow")

ASK_TITLE, PICK_DAY, PICK_TIME, CUSTOM_DATE, CUSTOM_TIME = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Привет! Я твой Task Manager Bot 🧠\n\n"
        "Я помогу хранить задачи и напомню точно по времени.\n"
        "Команды:\n"
        "/new — добавить задачу\n"
        "/list — показать активные задачи\n"
        "/done <id> — отметить задачу выполненной\n"
        "/delete <id> — удалить задачу\n"
        "/timezone <Zone> — сменить таймзону (например Europe/Moscow)\n"
        "/help — подсказка"
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


def user_tz(context: ContextTypes.DEFAULT_TYPE) -> pytz.BaseTzInfo:
    tz_name = context.user_data.get("timezone") or DEFAULT_TIMEZONE
    try:
        return pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        context.user_data["timezone"] = DEFAULT_TIMEZONE
        return pytz.timezone(DEFAULT_TIMEZONE)


async def set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Использование: /timezone Europe/Moscow")
        return

    candidate = context.args[0]
    try:
        pytz.timezone(candidate)
    except pytz.UnknownTimeZoneError:
        await update.message.reply_text("Неизвестная таймзона. Проверь формат, например: Europe/Moscow")
        return

    context.user_data["timezone"] = candidate
    await update.message.reply_text(f"Таймзона обновлена: {candidate} ✅")


async def new_task_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Напиши задачу одним сообщением.\nПример: Подготовить презентацию по квартальным итогам")
    return ASK_TITLE


async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    title = update.message.text.strip()
    if len(title) < 3:
        await update.message.reply_text("Слишком коротко. Напиши задачу подробнее (минимум 3 символа).")
        return ASK_TITLE

    context.user_data["draft_title"] = title
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Сегодня", callback_data="day:today")],
            [InlineKeyboardButton("Завтра", callback_data="day:tomorrow")],
            [InlineKeyboardButton("Послезавтра", callback_data="day:after_tomorrow")],
            [InlineKeyboardButton("Ввести дату вручную", callback_data="day:custom")],
        ]
    )
    await update.message.reply_text("Отлично. Теперь выбери день задачи:", reply_markup=keyboard)
    return PICK_DAY


async def pick_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    payload = query.data.split(":", maxsplit=1)[1]

    tz = user_tz(context)
    now_local = datetime.now(tz)

    if payload == "today":
        date_val = now_local.date()
    elif payload == "tomorrow":
        date_val = now_local.date() + timedelta(days=1)
    elif payload == "after_tomorrow":
        date_val = now_local.date() + timedelta(days=2)
    else:
        await query.edit_message_text("Введи дату в формате ДД.ММ.ГГГГ, например 25.12.2026")
        return CUSTOM_DATE

    context.user_data["draft_date"] = date_val.isoformat()
    return await ask_time_keyboard(query, context)


async def ask_time_keyboard(query, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("09:00", callback_data="time:09:00"), InlineKeyboardButton("12:00", callback_data="time:12:00")],
            [InlineKeyboardButton("15:00", callback_data="time:15:00"), InlineKeyboardButton("18:00", callback_data="time:18:00")],
            [InlineKeyboardButton("21:00", callback_data="time:21:00")],
            [InlineKeyboardButton("Ввести вручную", callback_data="time:custom")],
        ]
    )
    await query.edit_message_text("Теперь выбери время:", reply_markup=keyboard)
    return PICK_TIME


async def receive_custom_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    raw = update.message.text.strip()
    try:
        parsed = datetime.strptime(raw, "%d.%m.%Y").date()
    except ValueError:
        await update.message.reply_text("Неверный формат. Используй ДД.ММ.ГГГГ")
        return CUSTOM_DATE

    context.user_data["draft_date"] = parsed.isoformat()
    await update.message.reply_text("Дата принята ✅\nТеперь введи время в формате ЧЧ:ММ, например 18:30")
    return CUSTOM_TIME


async def pick_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    payload = query.data.split(":", maxsplit=1)[1]

    if payload == "custom":
        await query.edit_message_text("Введи время в формате ЧЧ:ММ, например 18:30")
        return CUSTOM_TIME

    context.user_data["draft_time"] = payload
    await save_task(update, context, edit_message=True)
    return ConversationHandler.END


async def receive_custom_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    raw = update.message.text.strip()
    try:
        datetime.strptime(raw, "%H:%M")
    except ValueError:
        await update.message.reply_text("Неверное время. Используй формат ЧЧ:ММ")
        return CUSTOM_TIME

    context.user_data["draft_time"] = raw
    await save_task(update, context)
    return ConversationHandler.END


async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE, edit_message: bool = False) -> None:
    title = context.user_data.get("draft_title")
    date_raw = context.user_data.get("draft_date")
    time_raw = context.user_data.get("draft_time")

    if not (title and date_raw and time_raw):
        if update.effective_message:
            await update.effective_message.reply_text("Не получилось собрать данные задачи. Попробуй /new снова.")
        return

    tz = user_tz(context)
    naive_dt = datetime.combine(datetime.fromisoformat(date_raw).date(), time.fromisoformat(time_raw))
    local_dt = tz.localize(naive_dt)
    due_utc = local_dt.astimezone(pytz.utc).replace(tzinfo=None)

    if due_utc <= datetime.utcnow():
        text = "Указанное время уже прошло. Выбери будущую дату/время через /new"
        if update.callback_query and edit_message:
            await update.callback_query.edit_message_text(text)
        else:
            await update.effective_message.reply_text(text)
        return

    storage: TaskStorage = context.application.bot_data["storage"]
    user_id = update.effective_user.id
    task_id = storage.add_task(user_id=user_id, title=title, due_at_utc=due_utc, timezone=tz.zone)

    response = (
        f"Задача сохранена ✅\n"
        f"ID: {task_id}\n"
        f"Задача: {title}\n"
        f"Когда: {local_dt.strftime('%d.%m.%Y %H:%M')} ({tz.zone})"
    )

    if update.callback_query and edit_message:
        await update.callback_query.edit_message_text(response)
    else:
        await update.effective_message.reply_text(response)

    for key in ("draft_title", "draft_date", "draft_time"):
        context.user_data.pop(key, None)


async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    storage: TaskStorage = context.application.bot_data["storage"]
    tasks = storage.list_tasks(update.effective_user.id, limit=15)
    tz = user_tz(context)

    if not tasks:
        await update.message.reply_text("Активных задач пока нет. Добавь через /new")
        return

    lines = ["Твои ближайшие задачи:\n"]
    for task in tasks:
        local_due = pytz.utc.localize(task.due_at_utc).astimezone(tz)
        lines.append(f"#{task.id} • {task.title}")
        lines.append(f"   ⏰ {local_due.strftime('%d.%m.%Y %H:%M')} ({tz.zone})")

    await update.message.reply_text("\n".join(lines))


async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Использование: /done <id>")
        return

    task_id = int(context.args[0])
    storage: TaskStorage = context.application.bot_data["storage"]
    ok = storage.set_done(task_id, update.effective_user.id)
    await update.message.reply_text("Отмечено как выполнено ✅" if ok else "Задача не найдена.")


async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Использование: /delete <id>")
        return

    task_id = int(context.args[0])
    storage: TaskStorage = context.application.bot_data["storage"]
    ok = storage.delete_task(task_id, update.effective_user.id)
    await update.message.reply_text("Задача удалена 🗑️" if ok else "Задача не найдена.")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    for key in ("draft_title", "draft_date", "draft_time"):
        context.user_data.pop(key, None)
    await update.effective_message.reply_text("Окей, создание задачи отменено.")
    return ConversationHandler.END


async def reminder_job(app: Application) -> None:
    storage: TaskStorage = app.bot_data["storage"]
    due_tasks = storage.pending_due_tasks(datetime.utcnow())

    for task in due_tasks:
        try:
            await app.bot.send_message(
                chat_id=task.user_id,
                text=(
                    "⏰ Напоминание о задаче\n"
                    f"#{task.id}: {task.title}\n"
                    "Когда: прямо сейчас"
                ),
            )
            storage.mark_reminded(task.id)
        except Exception:
            logger.exception("Не удалось отправить напоминание по задаче %s", task.id)


def build_app() -> Application:
    if not TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN в .env")

    app = Application.builder().token(TOKEN).build()
    app.bot_data["storage"] = TaskStorage(db_path=os.getenv("DB_PATH", "tasks.db"))

    conv = ConversationHandler(
        entry_points=[CommandHandler("new", new_task_start)],
        states={
            ASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title)],
            PICK_DAY: [CallbackQueryHandler(pick_day, pattern=r"^day:")],
            PICK_TIME: [CallbackQueryHandler(pick_time, pattern=r"^time:")],
            CUSTOM_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_date)],
            CUSTOM_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("timezone", set_timezone))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("done", done_task))
    app.add_handler(CommandHandler("delete", delete_task))
    app.add_handler(conv)

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(lambda: asyncio.create_task(reminder_job(app)), "interval", seconds=30)
    scheduler.start()

    return app


def main() -> None:
    app = build_app()
    logger.info("Bot is running...")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
