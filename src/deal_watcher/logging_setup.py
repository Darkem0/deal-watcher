from __future__ import annotations

import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path


class SecretRedactionFilter(logging.Filter):
    _patterns = (
        re.compile(r"(bot)[^\s/]{10,}", re.IGNORECASE),
        re.compile(r"(authorization|cookie|token|password|secret)[=: ]+[^\s,;]+", re.IGNORECASE),
    )

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in self._patterns:
            message = pattern.sub(r"\1=[REDACTED]", message)
        record.msg = message
        record.args = ()
        return True


def redact_secrets(value: str) -> str:
    """Remove credentials before errors reach a log or persistent delivery record."""
    result = value
    for pattern in SecretRedactionFilter._patterns:
        result = pattern.sub(r"\1=[REDACTED]", result)
    # Telegram bot URLs do not necessarily include a named query parameter.
    return re.sub(r"(api\.telegram\.org/bot)[^/\s]+", r"\1[REDACTED]", result, flags=re.IGNORECASE)


def configure_logging(directory: Path, level: str = "INFO") -> logging.Logger:
    directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("deal_watcher")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    redactor = SecretRedactionFilter()
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.addFilter(redactor)
    file_handler = RotatingFileHandler(
        directory / "deal-watcher.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(redactor)
    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger
