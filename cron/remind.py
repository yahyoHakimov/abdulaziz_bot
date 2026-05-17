import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Bot
from config import BOT_TOKEN
from database.schema import init_db
from database.queries import get_clients_due_for_reminder, set_needs_reminder


async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    clients = get_clients_due_for_reminder()
    print(f"Reminding {len(clients)} client(s)...")
    async with bot:
        for client in clients:
            await bot.send_message(
                chat_id=client.chat_id,
                text=f"Xayrli tong, {client.name}! Sartaroshga borish vaqti keldi. ✂️",
            )
            set_needs_reminder(client.chat_id, True)
            print(f"  Sent to {client.name} ({client.chat_id})")


asyncio.run(main())
