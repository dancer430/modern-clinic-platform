"""Structured logging primitives for production.

A minimal JSON formatter that emits one record per line. Suitable for
container log drivers that ingest stdout into a structured backend
(Loki, Vector, Cloudwatch, etc).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Include any extra fields the caller passed via ``extra={...}``.
        reserved = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "taskName",
            "message",
        }
        for key, value in record.__dict__.items():
            if key in reserved:
                continue
            try:
                json.dumps(value)
            except TypeError:
                continue
            payload[key] = value
        return json.dumps(payload, ensure_ascii=False)
