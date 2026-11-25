import logging
import sys

_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(level):
    """Log to stdout (the platform collects it). Safe to call many times."""
    logger = logging.getLogger("app")
    logger.setLevel(level)
    if not any(getattr(h, "_app_handler", False) for h in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler._app_handler = True
        handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(handler)
