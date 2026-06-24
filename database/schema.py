"""Schema bootstrap + lightweight forward-only migrations.

Versioning uses SQLite's built-in `PRAGMA user_version`. To change the schema,
append a new statement to MIGRATIONS — never edit an existing one. On startup
init_db() applies every migration whose index is beyond the DB's current
version, so existing production databases upgrade in place.
"""
from database.connection import get_connection

# Index in this list == target user_version. Append-only.
MIGRATIONS = [
    # v1 — initial clients table
    """
    CREATE TABLE IF NOT EXISTS clients (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id        INTEGER UNIQUE NOT NULL,
        name           TEXT NOT NULL,
        phone          TEXT NOT NULL,
        interval_days  INTEGER NOT NULL,
        last_visit     DATE NOT NULL,
        needs_reminder INTEGER DEFAULT 0
    )
    """,
]


def init_db() -> None:
    with get_connection() as conn:
        current = conn.execute("PRAGMA user_version").fetchone()[0]
        for version in range(current, len(MIGRATIONS)):
            conn.executescript(MIGRATIONS[version])
            conn.execute(f"PRAGMA user_version = {version + 1}")
