from dataclasses import dataclass
from datetime import date

from database.connection import get_connection


@dataclass
class Client:
    id: int
    chat_id: int
    name: str
    phone: str
    interval_days: int
    last_visit: date
    needs_reminder: bool


def _row_to_client(row) -> Client:
    return Client(
        id=row["id"],
        chat_id=row["chat_id"],
        name=row["name"],
        phone=row["phone"],
        interval_days=row["interval_days"],
        last_visit=date.fromisoformat(row["last_visit"]),
        needs_reminder=bool(row["needs_reminder"]),
    )


def create_client(chat_id: int, name: str, phone: str, interval_days: int) -> Client:
    today = date.today().isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO clients (chat_id, name, phone, interval_days, last_visit, needs_reminder)
            VALUES (?, ?, ?, ?, ?, 0)
            ON CONFLICT(chat_id) DO UPDATE SET
                name=excluded.name,
                phone=excluded.phone,
                interval_days=excluded.interval_days,
                last_visit=excluded.last_visit,
                needs_reminder=0
            """,
            (chat_id, name, phone, interval_days, today),
        )
    return get_client_by_chat_id(chat_id)


def get_client_by_chat_id(chat_id: int) -> Client | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM clients WHERE chat_id = ?", (chat_id,)
        ).fetchone()
    return _row_to_client(row) if row else None


def get_clients_due_for_reminder() -> list[Client]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM clients
            WHERE needs_reminder = 1
               OR julianday('now') - julianday(last_visit) >= interval_days
            """
        ).fetchall()
    return [_row_to_client(r) for r in rows]


def get_clients_awaiting_confirmation() -> list[Client]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM clients WHERE needs_reminder = 1"
        ).fetchall()
    return [_row_to_client(r) for r in rows]


def mark_visited(chat_id: int) -> None:
    today = date.today().isoformat()
    with get_connection() as conn:
        conn.execute(
            "UPDATE clients SET last_visit = ?, needs_reminder = 0 WHERE chat_id = ?",
            (today, chat_id),
        )


def set_needs_reminder(chat_id: int, value: bool) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE clients SET needs_reminder = ? WHERE chat_id = ?",
            (int(value), chat_id),
        )


def get_all_clients() -> list[Client]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM clients ORDER BY name").fetchall()
    return [_row_to_client(r) for r in rows]


def delete_client(chat_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM clients WHERE chat_id = ?", (chat_id,))
