"""Structured JSON logging setup."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime

from app.utils.request_context import request_id_var


class JsonFormatter(logging.Formatter):
    """Minimal structured formatter suitable for container logs."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(level: str) -> None:
    """Configure root logger with JSON output."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.handlers = [handler]

