import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
DB_PATH: str = os.getenv("DB_PATH", "barber.db")
MORNING_HOUR: int = int(os.getenv("MORNING_HOUR", "8"))
EVENING_HOUR: int = int(os.getenv("EVENING_HOUR", "23"))

INTERVALS = [10, 15, 20]
ADMIN_CHAT_ID: int = int(os.environ["ADMIN_CHAT_ID"])
ADMIN_NAME: str = os.getenv("ADMIN_NAME", "Admin")
