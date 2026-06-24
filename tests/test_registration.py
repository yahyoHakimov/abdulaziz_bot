from handlers.registration import _DEV_DAY_LABEL, _TEST_LABEL, _interval_keyboard

# conftest sets ADMIN_IDS=1, DEVELOPER_ID=999
DEVELOPER = 999
ADMIN = 1
NORMAL_USER = 555


def _labels(user_id: int) -> list[str]:
    kb = _interval_keyboard(user_id)
    return [btn.text for row in kb.keyboard for btn in row]


def test_normal_user_sees_only_standard_intervals():
    labels = _labels(NORMAL_USER)
    assert _DEV_DAY_LABEL not in labels
    assert _TEST_LABEL not in labels
    assert "15 kun" in labels


def test_admin_sees_test_mode_but_not_dev_day():
    labels = _labels(ADMIN)
    assert _TEST_LABEL in labels
    assert _DEV_DAY_LABEL not in labels  # 1-day is developer-only


def test_developer_sees_dev_day_option():
    labels = _labels(DEVELOPER)
    assert _DEV_DAY_LABEL in labels
    assert _TEST_LABEL in labels


def test_register_entry_point_exists():
    # /register must be wired so the developer can bypass the admin menu.
    from handlers.registration import build_registration_handler

    handler = build_registration_handler()
    commands = set().union(*(ep.commands for ep in handler.entry_points if hasattr(ep, "commands")))
    assert "register" in commands
    assert "start" in commands
