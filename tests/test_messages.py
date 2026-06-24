import messages


def test_morning_reminder_includes_name():
    assert "Ali" in messages.morning_reminder("Ali")


def test_confirmation_keyboard_callback_data():
    kb = messages.confirmation_keyboard()
    buttons = kb.inline_keyboard[0]
    assert {b.callback_data for b in buttons} == {messages.CONFIRM_YES, messages.CONFIRM_NO}


def test_new_client_contains_details():
    text = messages.new_client("Ali", "+998901112233", 15)
    assert "Ali" in text and "+998901112233" in text and "15" in text
