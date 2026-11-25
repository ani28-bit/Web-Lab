import pytest

from app import create_app
from app.config import Config, ConfigError


def test_defaults(monkeypatch):
    for name in ("APP_ENV", "LOG_LEVEL", "MAX_SEATS", "MAX_BODY_BYTES"):
        monkeypatch.delenv(name, raising=False)
    c = Config()
    assert (c.APP_ENV, c.LOG_LEVEL, c.MAX_SEATS) == ("development", "INFO", 200)


def test_environment_variables_are_read(monkeypatch):
    monkeypatch.setenv("MAX_SEATS", "75")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    c = Config()
    assert c.MAX_SEATS == 75 and c.LOG_LEVEL == "DEBUG"


def test_overrides_beat_environment(monkeypatch):
    monkeypatch.setenv("MAX_SEATS", "75")
    assert Config({"MAX_SEATS": 5}).MAX_SEATS == 5


@pytest.mark.parametrize("overrides", [
    {"APP_ENV": "staging"}, {"LOG_LEVEL": "LOUD"}, {"MAX_SEATS": "many"},
    {"MAX_SEATS": "0"}, {"MAX_BODY_BYTES": "-1"},
])
def test_bad_settings_fail_fast_at_startup(overrides):
    with pytest.raises(ConfigError):
        create_app(overrides)
