"""Logging and HTTP response helpers.

Provides standardized response writing with structured logging, mirroring
the Go application's log.go and vendor/github.com/johnamadeo/server/response.go.

The JSON error/success format uses {"Message": "..."} with a capital M
to preserve wire-level API compatibility with the Go app.
"""

import json
import logging
from typing import Any

from flask import Response

logger = logging.getLogger("mealbot")


def _message_to_bytes(message: str) -> str:
    """Convert a string message to the JSON {"Message": "..."} format.

    Equivalent to Go's server.StrToBytes().
    """
    return json.dumps({"Message": message})


def _err_to_bytes(err: Exception) -> str:
    """Convert an error to the JSON {"Message": "..."} format.

    Equivalent to Go's server.ErrToBytes().
    """
    return json.dumps({"Message": str(err)})


def log_and_write_err(
    err: Exception, status: int, function: str
) -> Response:
    """Log an error and return a Flask Response with the error message.

    Equivalent to Go's LogAndWriteErr.

    Args:
        err: The exception/error to log and return.
        status: HTTP status code.
        function: Name of the calling function (for log context).

    Returns:
        Flask Response with JSON error body and status code.
    """
    logger.error(
        "%s",
        str(err),
        extra={"function": function, "status": status},
    )
    return Response(
        _err_to_bytes(err),
        status=status,
        content_type="application/json",
    )


def log_and_write(
    data: Any, status: int, function: str
) -> Response:
    """Log a debug message and return a Flask Response.

    Equivalent to Go's LogAndWrite.

    Args:
        data: Response body. If it's a string, it will be wrapped in
              {"Message": "..."} format. If it's bytes/already encoded,
              it will be used directly.
        status: HTTP status code.
        function: Name of the calling function (for log context).

    Returns:
        Flask Response with the body and status code.
    """
    logger.debug(
        "%s",
        str(status),
        extra={"function": function},
    )

    if isinstance(data, str):
        body = _message_to_bytes(data)
    elif isinstance(data, bytes):
        body = data
    else:
        # Already encoded JSON string or similar
        body = data

    return Response(
        body,
        status=status,
        content_type="application/json",
    )


def log_and_write_status_bad_request(
    err: Exception, function: str
) -> Response:
    """Log and return a 400 Bad Request error.

    Equivalent to Go's LogAndWriteStatusBadRequest.
    """
    return log_and_write_err(err, 400, function)


def log_and_write_status_internal_server_error(
    err: Exception, function: str
) -> Response:
    """Log and return a 500 Internal Server Error.

    Equivalent to Go's LogAndWriteStatusInternalServerError.
    """
    return log_and_write_err(err, 500, function)
