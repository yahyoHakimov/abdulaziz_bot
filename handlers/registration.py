from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from config import INTERVALS
from database.queries import create_client

NAME, PHONE, INTERVAL = range(3)


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Welcome! What is your name?",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()
    keyboard = [[KeyboardButton("Share phone number", request_contact=True)]]
    await update.message.reply_text(
        "Please share your phone number.",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return PHONE


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact = update.message.contact
    if not contact:
        await update.message.reply_text("Please use the button to share your phone number.")
        return PHONE

    context.user_data["phone"] = contact.phone_number
    keyboard = [[KeyboardButton(f"{d} days")] for d in INTERVALS]
    await update.message.reply_text(
        "How often should we remind you to visit the barber?",
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
        keyboard = [[KeyboardButton(f"{d} days")] for d in INTERVALS]
        await update.message.reply_text(
            "Please choose one of the options.",
            reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True),
        )
        return INTERVAL

    chat_id = update.effective_chat.id
    name = context.user_data["name"]
    phone = context.user_data["phone"]

    create_client(chat_id, name, phone, days)

    await update.message.reply_text(
        f"You're all set, {name}! We'll remind you every {days} days to visit the barber.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Registration cancelled.", reply_markup=ReplyKeyboardRemove())
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
