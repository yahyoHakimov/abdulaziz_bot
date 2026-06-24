import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import ADMIN_IDS, BOT_TOKEN
except KeyError as e:
    print(f"FATAL: missing env var {e} in .env, aborting confirm")
    sys.exit(1)

from telegram import Bot
from telegram.error import Forbidden

import messages
from database.queries import delete_client, get_clients_awaiting_confirmation
from database.schema import init_db
from logger import get_logger

log = get_logger("confirm")


async def notify_admins(bot: Bot, text: str) -> None:
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=text)
        except Exception:
            pass


async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    clients = get_clients_awaiting_confirmation()
    log.info(f"Confirmation job started — {len(clients)} client(s) awaiting")
    keyboard = messages.confirmation_keyboard()
    async with bot:
        for client in clients:
            try:
                await bot.send_message(
                    chat_id=client.chat_id,
                    text=messages.CONFIRM_QUESTION,
                    reply_markup=keyboard,
                )
                log.info(f"Confirmation sent: {client.name} (chat_id={client.chat_id})")
            except Forbidden:
                log.warning(f"Blocked by user: {client.name} (chat_id={client.chat_id}) — removing from DB")
                delete_client(client.chat_id)
                await notify_admins(bot, messages.client_blocked(client.name, client.phone))
            except Exception as e:
                log.error(f"Failed to send confirmation to {client.name} (chat_id={client.chat_id}): {e}")
    log.info("Confirmation job finished")


asyncio.run(main())
