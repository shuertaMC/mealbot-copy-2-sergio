"""Shared utilities for logging and request handling.

This module provides logging helpers and query parameter utilities that mirror
the Go implementation in log.go, utils.go, and vendor/github.com/johnamadeo/server/response.go.
"""

import json
import logging
from typing import Any

from flask import Response, request

logger = logging.getLogger(__name__)


def str_to_bytes(message: str) -> bytes:
    """Convert a message string to JSON bytes format.

    Mirrors the Go server.StrToBytes function.

    Args:
        message: The message to encode.

    Returns:
        JSON-encoded bytes in format {"message": "..."}.
    """
    return json.dumps({"message": message}).encode("utf-8")


def err_to_bytes(err: Exception) -> bytes:
    """Convert an exception to JSON bytes format.

    Mirrors the Go server.ErrToBytes function.

    Args:
        err: The exception to encode.

    Returns:
        JSON-encoded bytes in format {"message": "..."}.
    """
    return json.dumps({"message": str(err)}).encode("utf-8")


def log_and_write_err(
    err: Exception,
    status: int,
    function: str,
) -> Response:
    """Log an error and return an HTTP error response.

    Mirrors the Go LogAndWriteErr function.

    Args:
        err: The error to log and respond with.
        status: The HTTP status code.
        function: The name of the function where the error occurred.

    Returns:
        A Flask Response with the error message as JSON.
    """
    logger.error(
        "Error in %s: %s",
        function,
        str(err),
        extra={"status": status, "function": function},
    )
    return Response(
        err_to_bytes(err),
        status=status,
        mimetype="application/json",
    )


def log_and_write(data: Any, status: int, function: str) -> Response:
    """Log a successful response and return it.

    Mirrors the Go LogAndWrite function.

    Args:
        data: The data to return (will be JSON encoded if not bytes).
        status: The HTTP status code.
        function: The name of the function.

    Returns:
        A Flask Response with the data as JSON.
    """
    logger.debug(
        "Response from %s",
        function,
        extra={"status": status, "function": function},
    )
    if isinstance(data, bytes):
        response_data = data
    elif isinstance(data, str):
        response_data = data.encode("utf-8")
    else:
        response_data = json.dumps(data).encode("utf-8")

    return Response(
        response_data,
        status=status,
        mimetype="application/json",
    )


def log_and_write_status_bad_request(err: Exception, function: str) -> Response:
    """Log and return a 400 Bad Request error response.

    Mirrors the Go LogAndWriteStatusBadRequest function.

    Args:
        err: The error to log and respond with.
        function: The name of the function where the error occurred.

    Returns:
        A Flask Response with status 400.
    """
    return log_and_write_err(err, 400, function)


def log_and_write_status_internal_server_error(
    err: Exception, function: str
) -> Response:
    """Log and return a 500 Internal Server Error response.

    Mirrors the Go LogAndWriteStatusInternalServerError function.

    Args:
        err: The error to log and respond with.
        function: The name of the function where the error occurred.

    Returns:
        A Flask Response with status 500.
    """
    return log_and_write_err(err, 500, function)


class QueryParamError(Exception):
    """Exception raised when a required query parameter is missing or invalid."""

    pass


def get_query_param(key: str) -> str:
    """Get a single query parameter from the current request.

    Mirrors the Go getQueryParam function.

    Args:
        key: The query parameter name.

    Returns:
        The query parameter value.

    Raises:
        QueryParamError: If the parameter is missing or has multiple values.
    """
    values = request.args.getlist(key)
    if not values or len(values) > 1:
        raise QueryParamError(f"Request query parameters must contain {key}")
    return values[0]


def get_query_params(keys: list[str]) -> list[str]:
    """Get multiple query parameters from the current request.

    Mirrors the Go getQueryParams function.

    Args:
        keys: List of query parameter names.

    Returns:
        List of query parameter values in the same order as keys.

    Raises:
        QueryParamError: If any parameter is missing or has multiple values.
    """
    values = []
    for key in keys:
        param_values = request.args.getlist(key)
        if not param_values or len(param_values) > 1:
            raise QueryParamError(f"Request query parameters does not contain {key}")
        values.append(param_values[0])
    return values
