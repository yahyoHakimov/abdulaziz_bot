from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

import messages
from database.queries import get_client_by_chat_id, mark_visited, set_needs_reminder
from logger import get_logger

log = get_logger("confirmation")


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    if query.data == messages.CONFIRM_YES:
        mark_visited(chat_id)
        client = get_client_by_chat_id(chat_id)
        days = client.interval_days if client else ""
        log.info(f"Visit confirmed: {client.name if client else 'unknown'} (chat_id={chat_id}), next in {days}d")
        await query.edit_message_text(messages.visit_confirmed(days))
    elif query.data == messages.CONFIRM_NO:
        set_needs_reminder(chat_id, True)
        client = get_client_by_chat_id(chat_id)
        log.info(f"Visit skipped: {client.name if client else 'unknown'} (chat_id={chat_id}), will retry tomorrow")
        await query.edit_message_text(messages.VISIT_SKIPPED)


def build_confirmation_handler() -> CallbackQueryHandler:
    return CallbackQueryHandler(
        handle_confirmation,
        pattern=f"^({messages.CONFIRM_YES}|{messages.CONFIRM_NO})$",
    )
