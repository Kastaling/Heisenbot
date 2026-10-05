import pytest

from heisenbot.config import env_bool, env_float, env_int


def test_environment_parsers(monkeypatch):
    monkeypatch.setenv("BOOL_VALUE", "yes")
    monkeypatch.setenv("INT_VALUE", "12")
    monkeypatch.setenv("FLOAT_VALUE", "0.25")

    assert env_bool("BOOL_VALUE", False) is True
    assert env_int("INT_VALUE", 1, minimum=1, maximum=20) == 12
    assert env_float("FLOAT_VALUE", 1.0, minimum=0.0, maximum=1.0) == 0.25


@pytest.mark.parametrize("value", ["maybe", "enabled", "2"])
def test_invalid_boolean_is_rejected(monkeypatch, value):
    monkeypatch.setenv("BOOL_VALUE", value)
    with pytest.raises(ValueError, match="BOOL_VALUE"):
        env_bool("BOOL_VALUE", False)


def test_out_of_range_number_is_rejected(monkeypatch):
    monkeypatch.setenv("INT_VALUE", "0")
    with pytest.raises(ValueError, match="at least 1"):
        env_int("INT_VALUE", 5, minimum=1)
