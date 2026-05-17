from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from services.reminder import confirm_visit, skip_visit

CONFIRM_YES = "confirm_yes"
CONFIRM_NO = "confirm_no"


def build_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Yes, I visited!", callback_data=CONFIRM_YES),
            InlineKeyboardButton("No, not yet", callback_data=CONFIRM_NO),
        ]
    ])


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    if query.data == CONFIRM_YES:
        confirm_visit(chat_id)
        await query.edit_message_text("Great! See you next time. Your reminder cycle has been reset.")
    elif query.data == CONFIRM_NO:
        skip_visit(chat_id)
        await query.edit_message_text("No worries! We'll remind you again tomorrow morning.")


def build_confirmation_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(handle_confirmation, pattern=f"^({CONFIRM_YES}|{CONFIRM_NO})$")
