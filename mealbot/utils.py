"""Query parameter extraction helpers.

Ported from: utils.go
"""

from flask import Request


def get_query_param(request: Request, key: str) -> tuple[str, Exception | None]:
    """Extract a single query parameter from the request.

    Mirrors Go's getQueryParam: the parameter must be present and must
    not have more than one value.

    Args:
        request: The Flask request object.
        key: The query parameter name.

    Returns:
        Tuple of (value, None) on success, or ("", error) on failure.
    """
    values = request.args.getlist(key)
    if len(values) == 0 or len(values) > 1:
        return "", ValueError(
            f"Request query parameters must contain {key}"
        )
    return values[0], None


def get_query_params(
    request: Request, keys: list[str]
) -> tuple[list[str], Exception | None]:
    """Extract multiple query parameters from the request.

    Mirrors Go's getQueryParams: each parameter must be present and
    must not have more than one value.

    Args:
        request: The Flask request object.
        keys: List of query parameter names.

    Returns:
        Tuple of (values_list, None) on success, or ([], error) on failure.
    """
    values: list[str] = []
    for key in keys:
        param_values = request.args.getlist(key)
        if len(param_values) == 0 or len(param_values) > 1:
            return [], ValueError(
                f"Request query parameters does not contain {key}"
            )
        values.append(param_values[0])
    return values, None
