"""Shared logging config — import `get_logger(__name__)` anywhere."""

import logging
import sys

from config import settings

_LEVEL = logging.DEBUG if settings.app_env == "development" else logging.INFO

logging.basicConfig(
    level=_LEVEL,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)