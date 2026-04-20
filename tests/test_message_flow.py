from finance_bot.validators import build_timestamps, is_allowed_chat


def test_build_timestamps_uses_message_date() -> None:
    timestamp_utc, timestamp_local = build_timestamps(1713567600, "America/Mexico_City")
    assert timestamp_utc.strftime("%Y-%m-%dT%H:%M:%SZ") == "2024-04-19T23:00:00Z"
    assert timestamp_local.strftime("%Y-%m-%d %H:%M:%S") == "2024-04-19 17:00:00"


def test_is_allowed_chat() -> None:
    assert is_allowed_chat(111, 111) is True
    assert is_allowed_chat(111, 222) is False
