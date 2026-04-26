from __future__ import annotations

import json
import logging

from common.logging import JsonFormatter


class TestJsonFormatter:
    def test_emits_required_keys(self):
        record = logging.LogRecord(
            name="appointments.services",
            level=logging.WARNING,
            pathname=__file__,
            lineno=1,
            msg="appointment %s confirmed",
            args=("a-1",),
            exc_info=None,
        )
        formatter = JsonFormatter()
        payload = json.loads(formatter.format(record))
        assert payload["level"] == "WARNING"
        assert payload["logger"] == "appointments.services"
        assert payload["msg"] == "appointment a-1 confirmed"
        assert "ts" in payload

    def test_passes_extra_fields_through(self):
        logger = logging.getLogger("test.json")
        record = logger.makeRecord(
            name=logger.name,
            level=logging.INFO,
            fn=__file__,
            lno=1,
            msg="completed",
            args=None,
            exc_info=None,
            extra={"appointment_id": 42, "actor_role": "doctor"},
        )
        payload = json.loads(JsonFormatter().format(record))
        assert payload["appointment_id"] == 42
        assert payload["actor_role"] == "doctor"

    def test_includes_exception_info(self):
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            import sys

            record = logging.LogRecord(
                name="appointments",
                level=logging.ERROR,
                pathname=__file__,
                lineno=1,
                msg="failed to confirm",
                args=(),
                exc_info=sys.exc_info(),
            )
        payload = json.loads(JsonFormatter().format(record))
        assert "exc" in payload
        assert "RuntimeError" in payload["exc"]
