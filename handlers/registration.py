from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import ADMIN_IDS, ADMIN_NAME, DEVELOPER_ID, INTERVALS
from database.queries import create_client
from logger import get_logger

log = get_logger("registration")

NAME, PHONE, INTERVAL = range(3)

_TEST_LABEL = "🧪 1 daqiqa (test)"
_DEV_DAY_LABEL = "📅 1 kun (dev)"


def _is_privileged(user_id: int) -> bool:
    return user_id in ADMIN_IDS or user_id == DEVELOPER_ID


def _is_developer(user_id: int) -> bool:
    return DEVELOPER_ID is not None and user_id == DEVELOPER_ID


def _interval_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    keys = [[KeyboardButton(f"{d} kun")] for d in INTERVALS]
    if _is_developer(user_id):
        keys.append([KeyboardButton(_DEV_DAY_LABEL)])
    if _is_privileged(user_id):
        keys.append([KeyboardButton(_TEST_LABEL)])
    return ReplyKeyboardMarkup(keys, one_time_keyboard=True, resize_keyboard=True)


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    if user.id in ADMIN_IDS:
        log.info(f"Admin /start: user_id={user.id} username={user.username}")
        menu = (
            f"Xush kelibsiz, {ADMIN_NAME}! 👋\n\n"
            "Admin buyruqlari:\n"
            "/clients — Mijozlar ro'yxati\n"
            "/reset — Mijoz hisoblagichini tiklash\n"
            "/remove — Mijozni o'chirish"
        )
        if _is_developer(user.id):
            menu += "\n/register — Mijoz sifatida test ro'yxatdan o'tish (dev)"
        await update.message.reply_text(menu, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    log.info(f"Registration started: user_id={user.id} username={user.username}")
    await update.message.reply_text(
        "Xush kelibsiz! Ismingizni kiriting:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NAME


async def start_test_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Force the client registration flow for the developer.

    The developer's id is also in ADMIN_IDS, so /start would show the admin menu
    and never reach the interval keyboard. /register lets the developer register
    as a client to exercise the reminder flow (incl. the dev-only '1 kun' option).
    """
    user = update.effective_user
    if not _is_developer(user.id):
        return ConversationHandler.END

    log.info(f"Developer test registration started: user_id={user.id}")
    await update.message.reply_text(
        "Test ro'yxatdan o'tish. Ismingizni kiriting:",
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
    await update.message.reply_text(
        "Qancha kundan keyin sartaroshga borishingizni eslataylik?",
        reply_markup=_interval_keyboard(update.effective_user.id),
    )
    return INTERVAL


async def receive_interval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    user_id = update.effective_user.id

    if text == _TEST_LABEL and _is_privileged(user_id):
        days = 0
    elif text == _DEV_DAY_LABEL and _is_developer(user_id):
        days = 1
    else:
        try:
            days = int(text.split()[0])
            if days not in INTERVALS:
                raise ValueError
        except (ValueError, IndexError):
            await update.message.reply_text(
                "Iltimos, variantlardan birini tanlang.",
                reply_markup=_interval_keyboard(user_id),
            )
            return INTERVAL

    chat_id = update.effective_chat.id
    name = context.user_data["name"]
    phone = context.user_data["phone"]

    create_client(chat_id, name, phone, days)
    label = "test (1 daqiqa)" if days == 0 else f"{days}d"
    log.info(f"New client registered: name={name} phone={phone} interval={label} chat_id={chat_id}")

    msg = (
        "Test rejimi yoqildi! /testremind buyrug'i bilan reminder sinab ko'ring."
        if days == 0
        else f"Hammasi tayyor, {name}! Har {days} kunda sartaroshga borishingizni eslatib turamiz. ✂️"
    )
    await update.message.reply_text(msg, reply_markup=ReplyKeyboardRemove())

    from handlers.admin import notify_admin
    await notify_admin(context, name, phone, days)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def build_registration_handler() -> ConversationHandler:
    from telegram.ext import CommandHandler

    return ConversationHandler(
        entry_points=[
            CommandHandler("start", ask_name),
            CommandHandler("register", start_test_registration),
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            PHONE: [MessageHandler(filters.CONTACT, receive_phone)],
            INTERVAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_interval)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
