"""
Shared helpers and logging utilities.

Ported from:
  - utils.go      → get_query_param, get_query_params
  - log.go        → log_and_write_err, log_and_write, convenience wrappers
  - response.go   → str_to_bytes, err_to_bytes ({"Message": "..."} JSON shape)

Design Decision #4: Preserve exact {"Message": "..."} JSON response shape
for API contract compatibility.
"""

import json
import logging

from flask import Response, request

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Response helpers (from vendor/github.com/johnamadeo/server/response.go)
# ---------------------------------------------------------------------------

def str_to_bytes(message: str) -> str:
    """
    Return a JSON string with the shape {"Message": "..."}.

    Mirrors Go's server.StrToBytes which wraps a string in a Message struct.
    Returns a JSON string suitable for Flask responses.
    """
    return json.dumps({"Message": message})


def err_to_bytes(err: Exception | str) -> str:
    """
    Return a JSON string with the shape {"Message": "<error>"}.

    Mirrors Go's server.ErrToBytes which wraps an error in a Message struct.
    """
    message = str(err) if isinstance(err, Exception) else err
    return json.dumps({"Message": message})


# ---------------------------------------------------------------------------
# Logging + response writers (from log.go)
# ---------------------------------------------------------------------------

def log_and_write_err(
    err: Exception | str,
    status: int,
    function: str,
) -> Response:
    """
    Log an error and return a Flask Response with the error message.

    Mirrors Go's LogAndWriteErr: logs with structured fields, sets status,
    and writes {"Message": "..."} body.
    """
    logger.error(
        "%s",
        str(err),
        extra={"function": function, "status": status},
    )
    body = err_to_bytes(err)
    return Response(body, status=status, mimetype="application/json")


def log_and_write(data: str, status: int, function: str) -> Response:
    """
    Log a successful response and return a Flask Response.

    Mirrors Go's LogAndWrite: logs debug info and writes body bytes.
    """
    logger.debug(
        "status=%d",
        status,
        extra={"function": function},
    )
    return Response(data, status=status, mimetype="application/json")


def log_and_write_status_bad_request(
    err: Exception | str,
    function: str,
) -> Response:
    """Convenience wrapper: log error and return 400 Bad Request."""
    return log_and_write_err(err, 400, function)


def log_and_write_status_internal_server_error(
    err: Exception | str,
    function: str,
) -> Response:
    """Convenience wrapper: log error and return 500 Internal Server Error."""
    return log_and_write_err(err, 500, function)


# ---------------------------------------------------------------------------
# Query parameter helpers (from utils.go)
# ---------------------------------------------------------------------------

def get_query_param(key: str) -> str:
    """
    Extract a single query parameter from the current Flask request.

    Mirrors Go's getQueryParam: returns error if key is missing or has
    multiple values.

    Raises:
        ValueError: if the key is missing or has more than one value.
    """
    values = request.args.getlist(key)
    if not values or len(values) > 1:
        raise ValueError(
            f"Request query parameters must contain {key}"
        )
    return values[0]


def get_query_params(keys: list[str]) -> list[str]:
    """
    Extract multiple query parameters from the current Flask request.

    Mirrors Go's getQueryParams: returns error if any key is missing or has
    multiple values.

    Raises:
        ValueError: if any key is missing or has more than one value.
    """
    result = []
    for key in keys:
        values = request.args.getlist(key)
        if not values or len(values) > 1:
            raise ValueError(
                f"Request query parameters does not contain {key}"
            )
        result.append(values[0])
    return result
