"""Settings come from environment variables. Bad values fail at startup."""
import logging
import os


class ConfigError(Exception):
    pass


def _positive_int(source, name, default):
    raw = source.get(name, str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from None
    if value < 1:
        raise ConfigError(f"{name} must be at least 1, got {value}")
    return value


class Config:
    ENVIRONMENTS = ("development", "test", "production")

    def __init__(self, overrides=None):
        source = dict(os.environ)
        source.update({k: str(v) for k, v in (overrides or {}).items()})

        self.APP_ENV = source.get("APP_ENV", "development")
        if self.APP_ENV not in self.ENVIRONMENTS:
            raise ConfigError(f"APP_ENV must be one of {self.ENVIRONMENTS}")

        self.LOG_LEVEL = source.get("LOG_LEVEL", "INFO").upper()
        if self.LOG_LEVEL not in logging.getLevelNamesMapping():
            raise ConfigError(f"LOG_LEVEL {self.LOG_LEVEL!r} is not a valid level")

        self.MAX_SEATS = _positive_int(source, "MAX_SEATS", 200)
        self.MAX_BODY_BYTES = _positive_int(source, "MAX_BODY_BYTES", 16384)
