from datetime import timedelta

from heisenbot.timeutils import parse_duration


def test_parse_duration_supports_combined_units():
    assert parse_duration("1h 30m") == timedelta(hours=1, minutes=30)


def test_minutes_are_minutes_not_months():
    assert parse_duration("5m") == timedelta(minutes=5)


def test_parse_duration_rejects_partial_or_unknown_input():
    assert parse_duration("7d please") is None
    assert parse_duration("10s") is None
    assert parse_duration("") is None
