import html
import json
import logging
import os
import queue
import threading
import urllib.request
from logging.handlers import RotatingFileHandler

_LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
_telegram_handler: "TelegramLogHandler | None" = None


class TelegramLogHandler(logging.Handler):
    """Sends WARNING+ log records to a Telegram chat via a background thread."""

    def __init__(self, bot_token: str, chat_id: int):
        super().__init__(level=logging.WARNING)
        self._url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self._chat_id = chat_id
        self._queue: queue.Queue = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _worker(self) -> None:
        while True:
            record = self._queue.get()
            if record is None:
                break
            try:
                msg = self.format(record)
                text = f"<pre>{html.escape(msg[:3900])}</pre>"
                data = json.dumps({
                    "chat_id": self._chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                }).encode("utf-8")
                req = urllib.request.Request(
                    self._url, data=data,
                    headers={"Content-Type": "application/json"},
                )
                urllib.request.urlopen(req, timeout=5)
            except Exception:
                pass  # never raise inside a log handler

    def emit(self, record: logging.LogRecord) -> None:
        self._queue.put_nowait(record)


def init_telegram_logging(bot_token: str, chat_id: int) -> None:
    """Call once at startup to enable real-time Telegram log forwarding."""
    global _telegram_handler
    if _telegram_handler is not None:
        return
    _telegram_handler = TelegramLogHandler(bot_token, chat_id)
    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    _telegram_handler.setFormatter(fmt)
    logging.root.addHandler(_telegram_handler)


def get_logger(name: str) -> logging.Logger:
    os.makedirs(_LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    file_handler = RotatingFileHandler(
        os.path.join(_LOG_DIR, "bot.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
