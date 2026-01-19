"""
Logging configuration for Mealbot application.

This module sets up structured logging similar to the Go application's
use of logrus, with JSON output and structured fields.
"""

import logging
import logging.config
import sys

from app.config import get_settings


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured logs similar to logrus.

    Adds structured fields as key=value pairs after the main message,
    making logs easier to parse and query in log aggregation systems.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with structured fields.

        Args:
            record: The log record to format

        Returns:
            str: Formatted log string with structured fields
        """
        # Start with the standard formatted message
        base_message = super().format(record)

        # Extract extra fields (added via extra={} in log calls)
        extra_fields = {}
        for key, value in record.__dict__.items():
            # Skip standard logging attributes
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "taskName",
            ]:
                extra_fields[key] = value

        # If there are extra fields, append them as key=value pairs
        if extra_fields:
            fields_str = " ".join(f"{k}={v}" for k, v in extra_fields.items())
            return f"{base_message} {fields_str}"

        return base_message


def configure_logging() -> None:
    """
    Configure application-wide logging.

    This function should be called once at application startup (in main.py).
    It sets up:
    - Log level from settings
    - Structured output format
    - Console handler for development
    - JSON-like structured fields for production log aggregation

    The configuration mimics the Go application's use of logrus with
    structured fields (logger, status, function, error, etc.).
    """
    settings = get_settings()

    # Determine log level from settings
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure root logger
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": StructuredFormatter,
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {"format": "%(levelname)s: %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "structured" if not settings.debug else "simple",
                "stream": sys.stdout,
            }
        },
        "root": {"level": log_level, "handlers": ["console"]},
        "loggers": {
            # Application loggers
            "app": {"level": log_level, "handlers": ["console"], "propagate": False},
            # SQLAlchemy loggers (only log warnings unless debug mode)
            "sqlalchemy.engine": {
                "level": logging.DEBUG if settings.debug else logging.WARNING,
                "handlers": ["console"],
                "propagate": False,
            },
            # Uvicorn loggers
            "uvicorn": {
                "level": logging.INFO,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": logging.INFO if settings.debug else logging.WARNING,
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(logging_config)

    # Log startup message
    logger = logging.getLogger("app")
    logger.info(
        "Logging configured",
        extra={
            "logger": "python-logging",
            "level": settings.log_level,
            "debug": settings.debug,
        },
    )
