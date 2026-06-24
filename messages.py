"""Central place for all user-facing bot text (Uzbek) and shared keyboards.

Keeping these here avoids the message drift that happens when the same
string is copy-pasted across the cron jobs and the interactive handlers.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# --- Callback data ---------------------------------------------------------
CONFIRM_YES = "confirm_yes"
CONFIRM_NO = "confirm_no"

# --- Reminder / confirmation flow -----------------------------------------
def morning_reminder(name: str) -> str:
    return f"Xayrli tong, {name}! Sartaroshga borish vaqti keldi. ✂️"


CONFIRM_QUESTION = "Bugun sartaroshga bordingizmi?"

CONFIRM_YES_LABEL = "✅ Ha, bordim!"
CONFIRM_NO_LABEL = "❌ Yo'q, hali emas"


def confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(CONFIRM_YES_LABEL, callback_data=CONFIRM_YES, api_kwargs={"style": "success"}),
            InlineKeyboardButton(CONFIRM_NO_LABEL, callback_data=CONFIRM_NO, api_kwargs={"style": "danger"}),
        ]
    ])


def visit_confirmed(days) -> str:
    return f"Ajoyib! Ko'rishguncha. {days} kundan keyin yana eslatamiz. ✂️"


VISIT_SKIPPED = "Xavotir olmang! Ertaga ertalab yana eslatamiz. 🕐"


# --- Admin notifications ---------------------------------------------------
def new_client(name: str, phone: str, interval: int) -> str:
    return f"🆕 Yangi mijoz ro'yxatdan o'tdi:\n👤 *{name}*\n📞 {phone}\n🕐 Har {interval} kun"


def client_blocked(name: str, phone: str) -> str:
    return f"⚠️ {name} ({phone}) botni blokladi va ro'yxatdan o'chirildi."
