import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import BOT_TOKEN
except KeyError as e:
    print(f"FATAL: missing env var {e} in .env, aborting remind")
    sys.exit(1)

from telegram import Bot
from database.schema import init_db
from database.queries import get_clients_due_for_reminder, set_needs_reminder
from logger import get_logger

log = get_logger("remind")


async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    clients = get_clients_due_for_reminder()
    log.info(f"Reminder job started — {len(clients)} client(s) due")
    async with bot:
        for client in clients:
            await bot.send_message(
                chat_id=client.chat_id,
                text=f"Xayrli tong, {client.name}! Sartaroshga borish vaqti keldi. ✂️",
            )
            set_needs_reminder(client.chat_id, True)
            log.info(f"Reminder sent: {client.name} (chat_id={client.chat_id}, interval={client.interval_days}d)")
    log.info("Reminder job finished")


asyncio.run(main())
