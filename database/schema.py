from database.connection import get_connection

def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id        INTEGER UNIQUE NOT NULL,
                name           TEXT NOT NULL,
                phone          TEXT NOT NULL,
                interval_days  INTEGER NOT NULL,
                last_visit     DATE NOT NULL,
                needs_reminder INTEGER DEFAULT 0
            )
        """)
