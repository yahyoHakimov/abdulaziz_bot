from datetime import date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from config import ADMIN_CHAT_ID
from database.queries import get_all_clients, delete_client, mark_visited


def is_admin(update: Update) -> bool:
    return update.effective_user.id == ADMIN_CHAT_ID


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

    clients = get_all_clients()
    if not clients:
        await update.message.reply_text("Hozircha mijozlar yo'q.")
        return

    lines = ["*Mijozlar ro'yxati:*\n"]
    for c in clients:
        status = _client_status(c)
        lines.append(f"👤 *{c.name}* | {c.phone} | har {c.interval_days} kun | {status}")

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
        await query.edit_message_text(f"✅ {name} uchun hisoblagich tiklandi. Siklı bugundan boshlanadi.")

    elif data.startswith("admin_remove_"):
        chat_id = int(data.split("_")[2])
        clients = get_all_clients()
        client = next((c for c in clients if c.chat_id == chat_id), None)
        name = client.name if client else str(chat_id)
        delete_client(chat_id)
        await query.edit_message_text(f"🗑 {name} o'chirildi.")


async def notify_admin(context, name: str, phone: str, interval: int) -> None:
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"🆕 Yangi mijoz ro'yxatdan o'tdi:\n👤 *{name}*\n📞 {phone}\n🕐 Har {interval} kun",
        parse_mode="Markdown",
    )


def build_admin_handlers() -> list:
    return [
        CommandHandler("clients", cmd_clients),
        CommandHandler("reset", cmd_reset),
        CommandHandler("remove", cmd_remove),
        CallbackQueryHandler(handle_admin_action, pattern=r"^admin_(reset|remove)_\d+$"),
    ]
