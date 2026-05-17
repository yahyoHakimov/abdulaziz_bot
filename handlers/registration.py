from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from config import INTERVALS, ADMIN_CHAT_ID, ADMIN_NAME
from database.queries import create_client

NAME, PHONE, INTERVAL = range(3)


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.effective_user.id == ADMIN_CHAT_ID:
        await update.message.reply_text(
            f"Xush kelibsiz, {ADMIN_NAME}! 👋\n\n"
            "Admin buyruqlari:\n"
            "/clients — Mijozlar ro'yxati\n"
            "/reset — Mijoz hisoblagichini tiklash\n"
            "/remove — Mijozni o'chirish",
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Xush kelibsiz! Ismingizni kiriting:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()
    keyboard = [[KeyboardButton("📱 Telefon raqamini ulashish", request_contact=True)]]
    await update.message.reply_text(
        "Telefon raqamingizni ulashing:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return PHONE


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    if not contact:
        await update.message.reply_text("Iltimos, tugmani bosib telefon raqamingizni ulashing.")
        return PHONE

    context.user_data["phone"] = contact.phone_number
    keyboard = [[KeyboardButton(f"{d} kun")] for d in INTERVALS]
    await update.message.reply_text(
        "Qancha kundan keyin sartaroshga borishingizni eslataylik?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return INTERVAL


async def receive_interval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        days = int(text.split()[0])
        if days not in INTERVALS:
            raise ValueError
    except (ValueError, IndexError):
        keyboard = [[KeyboardButton(f"{d} kun")] for d in INTERVALS]
        await update.message.reply_text(
            "Iltimos, variantlardan birini tanlang.",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        )
        return INTERVAL

    chat_id = update.effective_chat.id
    name = context.user_data["name"]
    phone = context.user_data["phone"]

    create_client(chat_id, name, phone, days)

    await update.message.reply_text(
        f"Hammasi tayyor, {name}! Har {days} kunda sartaroshga borishingizni eslatib turamiz. ✂️",
        reply_markup=ReplyKeyboardRemove(),
    )

    from handlers.admin import notify_admin
    await notify_admin(context, name, phone, days)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def build_registration_handler() -> ConversationHandler:
    from telegram.ext import CommandHandler

    return ConversationHandler(
        entry_points=[CommandHandler("start", ask_name)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            PHONE: [MessageHandler(filters.CONTACT, receive_phone)],
            INTERVAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_interval)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
