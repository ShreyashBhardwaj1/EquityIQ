"""
Logging configuration setup for EquityIQ.
"""

import logging
import sys

from app.infrastructure.logging.formatter import JSONFormatter


def setup_logging(env: str = "development") -> None:
    """
    Configures the root logging handler to output structured JSON messages to stdout.

    Args:
        env: The current app execution environment (development/production/testing).
    """
    root_logger = logging.getLogger()

    # Clear existing handlers to prevent duplicate formatting output
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    # Configure log levels based on environment severity
    if env == "production":
        root_logger.setLevel(logging.INFO)
    else:
        root_logger.setLevel(logging.DEBUG)

    # Prevent SQL and web libraries from printing excessive raw logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)

    logging.getLogger("equityiq").info(
        f"Structured JSON logging initialized for environment: {env}"
    )
