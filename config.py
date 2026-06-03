import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
DB_PATH: str = os.getenv("DB_PATH", "barber.db")
MORNING_HOUR: int = int(os.getenv("MORNING_HOUR", "8"))
EVENING_HOUR: int = int(os.getenv("EVENING_HOUR", "23"))

INTERVALS = [10, 15, 20, 25, 30]
ADMIN_IDS: set[int] = {int(i.strip()) for i in os.environ["ADMIN_IDS"].split(",")}
ADMIN_NAME: str = os.getenv("ADMIN_NAME", "Admin")

_dev = os.getenv("DEVELOPER_ID")
DEVELOPER_ID: int | None = int(_dev) if _dev else None
