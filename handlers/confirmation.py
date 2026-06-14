from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from services.reminder import confirm_visit, skip_visit
from database.queries import get_client_by_chat_id
from logger import get_logger

log = get_logger("confirmation")

CONFIRM_YES = "confirm_yes"
CONFIRM_NO = "confirm_no"


def _btn(text: str, callback_data: str, style: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback_data, api_kwargs={"style": style})


def build_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            _btn("✅ Ha, bordim!", CONFIRM_YES, style="success"),
            _btn("❌ Yo'q, hali emas", CONFIRM_NO, style="danger"),
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
        log.info(f"Visit confirmed: {client.name if client else 'unknown'} (chat_id={chat_id}), next in {days}d")
        await query.edit_message_text(f"Ajoyib! Ko'rishguncha. {days} kundan keyin yana eslatamiz. ✂️")
    elif query.data == CONFIRM_NO:
        skip_visit(chat_id)
        client = get_client_by_chat_id(chat_id)
        log.info(f"Visit skipped: {client.name if client else 'unknown'} (chat_id={chat_id}), will retry tomorrow")
        await query.edit_message_text("Xavotir olmang! Ertaga ertalab yana eslatamiz. 🕐")


def build_confirmation_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(handle_confirmation, pattern=f"^({CONFIRM_YES}|{CONFIRM_NO})$")
