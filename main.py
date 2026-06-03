import asyncio
from telegram.ext import ApplicationBuilder
from config import BOT_TOKEN, DEVELOPER_ID
from database.schema import init_db
from handlers.registration import build_registration_handler
from handlers.confirmation import build_confirmation_handler
from handlers.admin import build_admin_handlers
from logger import get_logger, init_telegram_logging

log = get_logger("main")


def main() -> None:
    init_db()

    if DEVELOPER_ID:
        init_telegram_logging(BOT_TOKEN, DEVELOPER_ID)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(build_registration_handler())
    app.add_handler(build_confirmation_handler())
    for handler in build_admin_handlers():
        app.add_handler(handler)

    log.info("Bot is running...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app.run_polling()


if __name__ == "__main__":
    main()
