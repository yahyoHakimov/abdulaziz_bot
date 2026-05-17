import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from config import BOT_TOKEN
from database.schema import init_db
from database.queries import get_clients_awaiting_confirmation


async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    clients = get_clients_awaiting_confirmation()
    print(f"Sending confirmation to {len(clients)} client(s)...")
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
            print(f"  Sent to {client.name} ({client.chat_id})")


asyncio.run(main())
