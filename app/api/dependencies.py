"""
FastAPI dependencies and utilities for request handling, error management, and logging.

This module provides:
- Query parameter extraction utilities
- Consistent error handling and logging
- Database session dependency
- HTTP exception helpers

Migrated from Go's utils.go and log.go to maintain API compatibility.
"""

import logging
from typing import Any

from fastapi import HTTPException, Request

from app.database import get_db

# Re-export get_db for convenience
__all__ = [
    "get_db",
    "get_query_param",
    "get_query_params",
    "log_and_raise_http_exception",
    "raise_400",
    "raise_500",
]


# Configure structured logging
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with structured logging configuration.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


def get_query_param(request: Request, key: str) -> str:
    """
    Extract a single required query parameter from the request.

    This function replicates the Go getQueryParam behavior:
    - The parameter must exist
    - The parameter must have exactly 1 value (not 0, not multiple)

    Args:
        request: FastAPI Request object
        key: Query parameter name to extract

    Returns:
        str: The query parameter value

    Raises:
        HTTPException: 400 Bad Request if parameter is missing or has multiple values

    Example:
        # For URL: /endpoint?admin=user@example.com
        admin = get_query_param(request, "admin")
        # admin == "user@example.com"
    """
    # Get all values for this query parameter
    values = request.query_params.getlist(key)

    # Check if parameter exists and has exactly 1 value
    if not values or len(values) != 1:
        error_msg = f"Request query parameters must contain {key}"
        logger = get_logger(__name__)
        logger.error(
            "Query parameter validation failed",
            extra={
                "function": "get_query_param",
                "key": key,
                "status": 400,
                "error": error_msg,
            },
        )
        raise HTTPException(status_code=400, detail=error_msg)

    return values[0]


def get_query_params(request: Request, keys: list[str]) -> list[str]:
    """
    Extract multiple required query parameters from the request.

    This function replicates the Go getQueryParams behavior:
    - Each parameter must exist
    - Each parameter must have exactly 1 value

    Args:
        request: FastAPI Request object
        keys: List of query parameter names to extract

    Returns:
        list[str]: List of query parameter values in the same order as keys

    Raises:
        HTTPException: 400 Bad Request if any parameter is missing or has multiple values

    Example:
        # For URL: /endpoint?org=acme&admin=user@example.com
        org, admin = get_query_params(request, ["org", "admin"])
        # org == "acme", admin == "user@example.com"
    """
    values = []

    for key in keys:
        # Get all values for this query parameter
        param_values = request.query_params.getlist(key)

        # Check if parameter exists and has exactly 1 value
        if not param_values or len(param_values) != 1:
            error_msg = f"Request query parameters does not contain {key}"
            logger = get_logger(__name__)
            logger.error(
                "Query parameter validation failed",
                extra={
                    "function": "get_query_params",
                    "key": key,
                    "status": 400,
                    "error": error_msg,
                },
            )
            raise HTTPException(status_code=400, detail=error_msg)

        values.append(param_values[0])

    return values


def log_and_raise_http_exception(
    status_code: int,
    detail: str,
    function_name: str,
    logger: logging.Logger | None = None,
    **extra_fields: Any,
) -> None:
    """
    Log an error with structured fields and raise an HTTPException.

    This function replicates Go's LogAndWriteErr pattern but adapted for FastAPI:
    - Logs with structured fields (function, status, error message)
    - Raises HTTPException instead of writing directly to ResponseWriter
    - Maintains the same error messages for API compatibility

    Args:
        status_code: HTTP status code (e.g., 400, 500)
        detail: Error message to return to the client
        function_name: Name of the function where error occurred
        logger: Optional logger instance (defaults to module logger)
        **extra_fields: Additional fields to include in the log entry

    Raises:
        HTTPException: Always raises with the given status code and detail

    Example:
        log_and_raise_http_exception(
            status_code=400,
            detail="Invalid organization name",
            function_name="create_organization"
        )
    """
    if logger is None:
        logger = get_logger(__name__)

    # Build structured log fields similar to logrus
    log_fields = {
        "logger": "python-logging",
        "status": status_code,
        "function": function_name,
        "error": detail,
        **extra_fields,
    }

    # Log at error level for 4xx and 5xx status codes
    if status_code >= 400:
        logger.error(detail, extra=log_fields)
    else:
        logger.warning(detail, extra=log_fields)

    # Raise HTTPException with the error details
    raise HTTPException(status_code=status_code, detail=detail)


def raise_400(detail: str, function_name: str, **extra_fields: Any) -> None:
    """
    Convenience function to log and raise a 400 Bad Request error.

    Args:
        detail: Error message to return to the client
        function_name: Name of the function where error occurred
        **extra_fields: Additional fields to include in the log entry

    Raises:
        HTTPException: 400 Bad Request

    Example:
        raise_400("Invalid email address", "create_member")
    """
    log_and_raise_http_exception(400, detail, function_name, **extra_fields)


def raise_500(detail: str, function_name: str, **extra_fields: Any) -> None:
    """
    Convenience function to log and raise a 500 Internal Server Error.

    Args:
        detail: Error message to return to the client
        function_name: Name of the function where error occurred
        **extra_fields: Additional fields to include in the log entry

    Raises:
        HTTPException: 500 Internal Server Error

    Example:
        raise_500("Database connection failed", "get_members")
    """
    log_and_raise_http_exception(500, detail, function_name, **extra_fields)


def raise_405(detail: str, function_name: str, **extra_fields: Any) -> None:
    """
    Convenience function to log and raise a 405 Method Not Allowed error.

    Args:
        detail: Error message to return to the client
        function_name: Name of the function where error occurred
        **extra_fields: Additional fields to include in the log entry

    Raises:
        HTTPException: 405 Method Not Allowed

    Example:
        raise_405("POST not allowed", "handle_request")
    """
    log_and_raise_http_exception(405, detail, function_name, **extra_fields)


# Common error message constants for API compatibility
# These match the exact error messages from the Go implementation
ERROR_MSG_INVALID_ACCESS_TOKEN = "Invalid access token"
ERROR_MSG_MISSING_AUTH_HEADER = "Authorization header required"
ERROR_MSG_QUERY_PARAM_MISSING = "Request query parameters must contain {key}"
ERROR_MSG_QUERY_PARAM_NOT_CONTAIN = "Request query parameters does not contain {key}"
