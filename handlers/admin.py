import html
import os
from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from config import ADMIN_IDS, DEVELOPER_ID
from database.queries import get_all_clients, delete_client, mark_visited, get_clients_due_for_reminder, set_needs_reminder
from logger import get_logger, _LOG_DIR
import messages

log = get_logger("admin")

_LOG_FILE = os.path.join(_LOG_DIR, "bot.log")


def is_admin(update: Update) -> bool:
    return update.effective_user.id in ADMIN_IDS


def _client_status(client) -> str:
    days_since = (date.today() - client.last_visit).days
    days_left = client.interval_days - days_since
    if client.needs_reminder:
        status = "⏰ Tasdiqlash kutilmoqda"
    elif days_left <= 0:
        status = "🔔 Bugun eslatma"
    else:
        status = f"🕐 {days_left} kun qoldi"
    return status


async def cmd_clients(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return

    log.info(f"Admin {update.effective_user.id} viewed client list")
    clients = get_all_clients()
    if not clients:
        await update.message.reply_text("Hozircha mijozlar yo'q.")
        return

    lines = ["*Mijozlar ro'yxati:*\n"]
    for i, c in enumerate(clients, start=1):
        status = _client_status(c)
        lines.append(f"{i}. 👤 *{c.name}* | {c.phone} | har {c.interval_days} kun | {status}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return

    clients = get_all_clients()
    if not clients:
        await update.message.reply_text("Hozircha mijozlar yo'q.")
        return

    keyboard = [
        [InlineKeyboardButton(f"🔄 {c.name} ({c.phone})", callback_data=f"admin_reset_{c.chat_id}")]
        for c in clients
    ]
    await update.message.reply_text(
        "Hisoblagichni tiklash uchun mijozni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def cmd_remove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(update):
        return

    clients = get_all_clients()
    if not clients:
        await update.message.reply_text("Hozircha mijozlar yo'q.")
        return

    keyboard = [
        [InlineKeyboardButton(f"❌ {c.name} ({c.phone})", callback_data=f"admin_remove_{c.chat_id}")]
        for c in clients
    ]
    await update.message.reply_text(
        "O'chirish uchun mijozni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not is_admin(update):
        return

    data = query.data
    if data.startswith("admin_reset_"):
        chat_id = int(data.split("_")[2])
        mark_visited(chat_id)
        clients = get_all_clients()
        client = next((c for c in clients if c.chat_id == chat_id), None)
        name = client.name if client else str(chat_id)
        log.info(f"Admin {update.effective_user.id} reset counter for {name} (chat_id={chat_id})")
        await query.edit_message_text(f"✅ {name} uchun hisoblagich tiklandi. Siklı bugundan boshlanadi.")

    elif data.startswith("admin_remove_"):
        chat_id = int(data.split("_")[2])
        clients = get_all_clients()
        client = next((c for c in clients if c.chat_id == chat_id), None)
        name = client.name if client else str(chat_id)
        delete_client(chat_id)
        log.info(f"Admin {update.effective_user.id} removed client {name} (chat_id={chat_id})")
        await query.edit_message_text(f"🗑 {name} o'chirildi.")


async def notify_admin(context, name: str, phone: str, interval: int) -> None:
    for admin_id in ADMIN_IDS:
        await context.bot.send_message(
            chat_id=admin_id,
            text=messages.new_client(name, phone, interval),
            parse_mode="Markdown",
        )


async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != DEVELOPER_ID:
        return

    try:
        n = int(context.args[0]) if context.args else 50
        n = min(n, 200)
    except (ValueError, IndexError):
        n = 50

    log.info(f"Developer {update.effective_user.id} fetched last {n} log lines")

    try:
        with open(_LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        tail = "".join(lines[-n:]) or "(log fayli bo'sh)"
    except FileNotFoundError:
        tail = "(log fayli topilmadi)"

    for i in range(0, len(tail), 4000):
        await update.message.reply_text(f"<pre>{html.escape(tail[i:i+4000])}</pre>", parse_mode="HTML")


async def cmd_testflow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id != DEVELOPER_ID:
        return

    log.info(f"Test flow triggered by user_id={user_id}")

    await context.bot.send_message(
        chat_id=user_id,
        text=messages.morning_reminder("Developer"),
    )
    await context.bot.send_message(
        chat_id=user_id,
        text=messages.CONFIRM_QUESTION,
        reply_markup=messages.confirmation_keyboard(),
    )


async def cmd_testremind(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS and user_id != DEVELOPER_ID:
        return

    test_clients = [c for c in get_clients_due_for_reminder() if c.interval_days == 0]
    if not test_clients:
        await update.message.reply_text("Test mijozi topilmadi. Avval /start orqali '🧪 1 daqiqa (test)' intervalini tanlang.")
        return

    log.info(f"Test remind triggered by user_id={user_id} for {len(test_clients)} test client(s)")
    sent, failed = [], []
    for client in test_clients:
        try:
            await context.bot.send_message(
                chat_id=client.chat_id,
                text=messages.morning_reminder(client.name),
            )
            set_needs_reminder(client.chat_id, True)
            sent.append(client.name)
        except Forbidden:
            failed.append(client.name)

    lines = ["✅ Test reminder yuborildi:"] + [f"  • {n}" for n in sent]
    if failed:
        lines += ["❌ Yuborilmadi (bloklangan):"] + [f"  • {n}" for n in failed]
    await update.message.reply_text("\n".join(lines))


def build_admin_handlers() -> list:
    handlers = [
        CommandHandler("clients", cmd_clients),
        CommandHandler("reset", cmd_reset),
        CommandHandler("remove", cmd_remove),
        CommandHandler("testremind", cmd_testremind),
        CommandHandler("testflow", cmd_testflow),
        CallbackQueryHandler(handle_admin_action, pattern=r"^admin_(reset|remove)_\d+$"),
    ]
    if DEVELOPER_ID:
        handlers.append(CommandHandler("logs", cmd_logs))
    return handlers
