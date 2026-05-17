from telegram.ext import Application
from services.reminder import get_clients_to_remind, get_clients_to_confirm
from handlers.confirmation import build_confirmation_keyboard


async def send_morning_reminders(app: Application) -> None:
    clients = get_clients_to_remind()
    for client in clients:
        await app.bot.send_message(
            chat_id=client.chat_id,
            text=f"Xayrli tong, {client.name}! Sartaroshga borish vaqti keldi. ✂️",
        )
        from database.queries import set_needs_reminder
        set_needs_reminder(client.chat_id, True)


async def send_evening_confirmations(app: Application) -> None:
    clients = get_clients_to_confirm()
    for client in clients:
        await app.bot.send_message(
            chat_id=client.chat_id,
            text="Bugun sartaroshga bordingizmi?",
            reply_markup=build_confirmation_keyboard(),
        )


def register_jobs(app: Application, morning_hour: int, evening_hour: int) -> None:
    job_queue = app.job_queue

    job_queue.run_daily(
        lambda context: send_morning_reminders(app),
        time=__import__("datetime").time(hour=morning_hour, minute=0),
        name="morning_reminder",
    )

    job_queue.run_daily(
        lambda context: send_evening_confirmations(app),
        time=__import__("datetime").time(hour=evening_hour, minute=0),
        name="evening_confirmation",
    )
