"""
Structured JSON log formatter for EquityIQ.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """
    Custom log formatter rendering log records as serialized JSON strings.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the LogRecord as a JSON string.

        Args:
            record: The logging record.

        Returns:
            A serialized JSON log message string.
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "filename": record.filename,
            "line": record.lineno,
        }

        # Include exception tracebacks if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include any custom dictionary fields provided via the 'extra' keyword argument
        # standard python logging populates any extra keys directly onto the record object
        # we skip built-in attributes
        builtin_attrs = {
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
        }
        extra_fields = {
            key: val for key, val in record.__dict__.items() if key not in builtin_attrs
        }
        if extra_fields:
            log_data["extra"] = extra_fields

        return json.dumps(log_data)
