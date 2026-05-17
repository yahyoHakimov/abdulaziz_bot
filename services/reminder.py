from database.queries import (
    get_clients_due_for_reminder,
    get_clients_awaiting_confirmation,
    mark_visited,
    set_needs_reminder,
)


def get_clients_to_remind():
    return get_clients_due_for_reminder()


def get_clients_to_confirm():
    return get_clients_awaiting_confirmation()


def confirm_visit(chat_id: int) -> None:
    mark_visited(chat_id)


def skip_visit(chat_id: int) -> None:
    set_needs_reminder(chat_id, True)
