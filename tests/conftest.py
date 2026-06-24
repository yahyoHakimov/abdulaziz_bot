import os
import tempfile

# config.py reads these at import time, so they must be set before any app
# module is imported. A throwaway token/admin id is fine for non-network tests.
os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("ADMIN_IDS", "1")
os.environ.setdefault("DEVELOPER_ID", "999")
_DB_FD, _DB_PATH = tempfile.mkstemp(suffix=".db")
os.environ["DB_PATH"] = _DB_PATH

import pytest  # noqa: E402

from database.connection import get_connection  # noqa: E402
from database.schema import init_db  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    """Start every test with an empty, freshly-migrated database."""
    with get_connection() as conn:
        conn.execute("DROP TABLE IF EXISTS clients")
        conn.execute("PRAGMA user_version = 0")
    init_db()
    yield
