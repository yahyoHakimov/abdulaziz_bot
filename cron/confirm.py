import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import BOT_TOKEN
except KeyError as e:
    print(f"FATAL: missing env var {e} in .env, aborting confirm")
    sys.exit(1)

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from database.schema import init_db
from database.queries import get_clients_awaiting_confirmation
from logger import get_logger

log = get_logger("confirm")


async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    clients = get_clients_awaiting_confirmation()
    log.info(f"Confirmation job started — {len(clients)} client(s) awaiting")
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Ha, bordim!", callback_data="confirm_yes"),
        InlineKeyboardButton("❌ Yo'q, hali emas", callback_data="confirm_no"),
    ]])
    async with bot:
        for client in clients:
            await bot.send_message(
                chat_id=client.chat_id,
                text="Bugun sartaroshga bordingizmi?",
                reply_markup=keyboard,
            )
            log.info(f"Confirmation sent: {client.name} (chat_id={client.chat_id})")
    log.info("Confirmation job finished")


asyncio.run(main())
