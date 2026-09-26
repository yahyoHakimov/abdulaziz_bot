import asyncio

from telegram.error import NetworkError, TimedOut
from telegram.ext import ApplicationBuilder, ContextTypes

from config import BOT_TOKEN, DEVELOPER_ID
from database.schema import init_db
from handlers.admin import build_admin_handlers
from handlers.confirmation import build_confirmation_handler
from handlers.registration import build_registration_handler
from logger import get_logger, init_telegram_logging

log = get_logger("main")


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors so transient network blips don't alert the developer.

    NetworkError/TimedOut (e.g. httpcore.ReadError talking to Telegram) are
    logged at INFO — visible in the journal, below the WARNING threshold that
    forwards to Telegram — since python-telegram-bot retries automatically.
    Anything else is logged at ERROR and still reaches the Telegram log.
    """
    err = context.error
    if isinstance(err, NetworkError | TimedOut):
        log.info("Transient network error talking to Telegram: %r", err)
        return
    log.error("Unhandled exception while processing %s", update, exc_info=err)


def main() -> None:
    init_db()

    if DEVELOPER_ID:
        init_telegram_logging(BOT_TOKEN, DEVELOPER_ID)

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(build_registration_handler())
    app.add_handler(build_confirmation_handler())
    for handler in build_admin_handlers():
        app.add_handler(handler)

    app.add_error_handler(on_error)

    log.info("Bot is running...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app.run_polling()


if __name__ == "__main__":
    main()
