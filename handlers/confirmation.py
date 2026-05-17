from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from services.reminder import confirm_visit, skip_visit
from database.queries import get_client_by_chat_id

CONFIRM_YES = "confirm_yes"
CONFIRM_NO = "confirm_no"


def build_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Ha, bordim!", callback_data=CONFIRM_YES),
            InlineKeyboardButton("❌ Yo'q, hali emas", callback_data=CONFIRM_NO),
        ]
    ])


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    if query.data == CONFIRM_YES:
        confirm_visit(chat_id)
        client = get_client_by_chat_id(chat_id)
        days = client.interval_days if client else ""
        await query.edit_message_text(f"Ajoyib! Ko'rishguncha. {days} kundan keyin yana eslatamiz. ✂️")
    elif query.data == CONFIRM_NO:
        skip_visit(chat_id)
        await query.edit_message_text("Xavotir olmang! Ertaga ertalab yana eslatamiz. 🕐")


def build_confirmation_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(handle_confirmation, pattern=f"^({CONFIRM_YES}|{CONFIRM_NO})$")
