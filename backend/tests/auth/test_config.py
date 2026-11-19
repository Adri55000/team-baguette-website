from dataclasses import replace

import pytest

from app.core.config import settings, parse_bool_env

@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("true", True),
        ("false", False),
        ("TRUE", True),
        (" FALSE ", False),
    ],
)
def test_parse_bool_env_valid(monkeypatch, value, expected):
    monkeypatch.setenv("TEST_BOOL", value)

    assert parse_bool_env("TEST_BOOL") is expected

@pytest.mark.parametrize(
    "value",
    ["tru", "0", "yes", ""],
)
def test_parse_bool_env_invalid(monkeypatch, value):
    monkeypatch.setenv("TEST_BOOL", value)

    with pytest.raises(ValueError, match="TEST_BOOL"):
        parse_bool_env("TEST_BOOL")


def test_parse_bool_env_default(monkeypatch):
    monkeypatch.delenv("TEST_BOOL", raising=False)

    assert parse_bool_env("TEST_BOOL") is True
    
def test_session_duration_must_be_positive():
    with pytest.raises(ValueError):
        replace(settings, session_duration_days=0)


def test_negative_session_duration_is_rejected():
    with pytest.raises(ValueError):
        replace(settings, session_duration_days=-5)


def test_valid_session_duration_is_accepted():
    valid_settings = replace(settings, session_duration_days=30)

    assert valid_settings.session_duration_days == 30
