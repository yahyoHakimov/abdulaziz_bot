from datetime import date, timedelta

from database.connection import get_connection
from database.queries import (
    create_client,
    delete_client,
    get_all_clients,
    get_client_by_chat_id,
    get_clients_awaiting_confirmation,
    get_clients_due_for_reminder,
    mark_visited,
    set_needs_reminder,
)


def _set_last_visit(chat_id: int, days_ago: int) -> None:
    when = (date.today() - timedelta(days=days_ago)).isoformat()
    with get_connection() as conn:
        conn.execute("UPDATE clients SET last_visit = ? WHERE chat_id = ?", (when, chat_id))


def test_create_and_fetch_client():
    c = create_client(100, "Ali", "+998901112233", 15)
    assert c.name == "Ali"
    assert c.interval_days == 15
    assert c.needs_reminder is False
    assert get_client_by_chat_id(100).phone == "+998901112233"


def test_create_is_upsert_and_resets_cycle():
    create_client(100, "Ali", "+998", 15)
    set_needs_reminder(100, True)
    # Re-registering the same chat_id updates fields and clears the reminder flag.
    c = create_client(100, "Ali Updated", "+998", 30)
    assert c.name == "Ali Updated"
    assert c.interval_days == 30
    assert c.needs_reminder is False


def test_due_when_interval_elapsed():
    create_client(100, "Ali", "+998", 15)
    _set_last_visit(100, 20)  # overdue
    due = {c.chat_id for c in get_clients_due_for_reminder()}
    assert 100 in due


def test_not_due_before_interval():
    create_client(100, "Ali", "+998", 15)
    _set_last_visit(100, 5)  # not yet due
    due = {c.chat_id for c in get_clients_due_for_reminder()}
    assert 100 not in due


def test_needs_reminder_flag_makes_client_due_and_awaiting():
    create_client(100, "Ali", "+998", 15)
    _set_last_visit(100, 1)  # not time-due
    set_needs_reminder(100, True)
    assert 100 in {c.chat_id for c in get_clients_due_for_reminder()}
    assert 100 in {c.chat_id for c in get_clients_awaiting_confirmation()}


def test_mark_visited_resets_cycle():
    create_client(100, "Ali", "+998", 15)
    _set_last_visit(100, 20)
    set_needs_reminder(100, True)
    mark_visited(100)
    c = get_client_by_chat_id(100)
    assert c.needs_reminder is False
    assert c.last_visit == date.today()
    assert 100 not in {x.chat_id for x in get_clients_awaiting_confirmation()}


def test_delete_client():
    create_client(100, "Ali", "+998", 15)
    delete_client(100)
    assert get_client_by_chat_id(100) is None


def test_all_clients_sorted_by_name():
    create_client(1, "Zafar", "+998", 15)
    create_client(2, "Ali", "+998", 15)
    names = [c.name for c in get_all_clients()]
    assert names == ["Ali", "Zafar"]
