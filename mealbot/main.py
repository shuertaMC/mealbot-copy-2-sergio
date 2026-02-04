"""FastAPI application entry point for the Mealbot API.

This module initializes the FastAPI application, configures middleware (CORS, logging),
and provides the main entry point for the service.

The logging utilities mirror the behavior of log.go from the Go implementation,
providing structured logging with function names and status codes.
"""

import logging
import sys

from fastapi import FastAPI, HTTPException, status

from mealbot.auth import get_current_user  # noqa: F401
from mealbot.cors import setup_cors
from mealbot.models import MessageResponse

# Configure logging
# Uses structured logging format compatible with Heroku (stdout, single-line)
# This mirrors the logging approach from log.go using logrus
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Create logger instance for this module
logger = logging.getLogger(__name__)


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance for a module.

    This provides consistent logging configuration across the application,
    similar to how logrus is used in the Go implementation.

    Args:
        name: The name for the logger, typically __name__ of the module.

    Returns:
        A configured Logger instance.
    """
    return logging.getLogger(name)


def log_and_raise_error(
    logger_instance: logging.Logger,
    error: Exception,
    status_code: int,
    function: str,
) -> None:
    """
    Log an error and raise an HTTPException.

    This mirrors the Go LogAndWriteErr function from log.go. In FastAPI,
    we raise HTTPException instead of directly writing to the response.

    Args:
        logger_instance: The logger to use for logging.
        error: The exception that occurred.
        status_code: The HTTP status code to return.
        function: The name of the function where the error occurred.

    Raises:
        HTTPException: Always raised with the given status code and error message.
    """
    logger_instance.error(
        "%s",
        str(error),
        extra={"status": status_code, "function": function},
    )
    raise HTTPException(
        status_code=status_code,
        detail=MessageResponse(Message=str(error)).model_dump(),
    )


def log_and_raise_bad_request(
    logger_instance: logging.Logger,
    error: Exception,
    function: str,
) -> None:
    """
    Log an error and raise a 400 Bad Request HTTPException.

    This mirrors the Go LogAndWriteStatusBadRequest function from log.go.

    Args:
        logger_instance: The logger to use for logging.
        error: The exception that occurred.
        function: The name of the function where the error occurred.

    Raises:
        HTTPException: Always raised with status code 400.
    """
    log_and_raise_error(
        logger_instance,
        error,
        status.HTTP_400_BAD_REQUEST,
        function,
    )


def log_and_raise_internal_error(
    logger_instance: logging.Logger,
    error: Exception,
    function: str,
) -> None:
    """
    Log an error and raise a 500 Internal Server Error HTTPException.

    This mirrors the Go LogAndWriteStatusInternalServerError function from log.go.

    Args:
        logger_instance: The logger to use for logging.
        error: The exception that occurred.
        function: The name of the function where the error occurred.

    Raises:
        HTTPException: Always raised with status code 500.
    """
    log_and_raise_error(
        logger_instance,
        error,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        function,
    )


def log_debug(
    logger_instance: logging.Logger,
    status_code: int,
    function: str,
) -> None:
    """
    Log a debug message for a successful response.

    This mirrors the debug logging part of Go's LogAndWrite function from log.go.

    Args:
        logger_instance: The logger to use for logging.
        status_code: The HTTP status code being returned.
        function: The name of the function.
    """
    logger_instance.debug(
        "Status: %d",
        status_code,
        extra={"function": function},
    )


# Create FastAPI application
app = FastAPI(
    title="Mealbot API",
    version="1.0.0",
    description="REST API for meal pairing service",
)

# Configure CORS middleware
# Must be added before routes to ensure CORS headers are included in all responses
setup_cors(app)

logger.info("Mealbot API initialized with CORS middleware")


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}
