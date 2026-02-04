"""Utility functions for the Mealbot API.

This module provides query parameter extraction helpers that mirror the behavior
of the Go implementation in utils.go.
"""

from typing import List

from fastapi import HTTPException, Request, status


def get_query_param(request: Request, key: str) -> str:
    """
    Extract a single required query parameter from a request.

    This mirrors the Go getQueryParam function. It raises an HTTPException
    if the parameter is missing or if multiple values are provided.

    Args:
        request: The FastAPI Request object.
        key: The name of the query parameter to extract.

    Returns:
        The value of the query parameter.

    Raises:
        HTTPException: If the parameter is missing or has multiple values.
    """
    values = request.query_params.getlist(key)

    if not values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request query parameters must contain {key}",
        )

    if len(values) > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Request query parameters must contain {key}",
        )

    return values[0]


def get_query_params(request: Request, keys: List[str]) -> List[str]:
    """
    Extract multiple required query parameters from a request.

    This mirrors the Go getQueryParams function. It raises an HTTPException
    if any parameter is missing or if multiple values are provided for any key.

    Args:
        request: The FastAPI Request object.
        keys: List of query parameter names to extract.

    Returns:
        List of values for each key, in the same order as the keys.

    Raises:
        HTTPException: If any parameter is missing or has multiple values.
    """
    result = []

    for key in keys:
        values = request.query_params.getlist(key)

        if not values:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request query parameters does not contain {key}",
            )

        if len(values) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Request query parameters does not contain {key}",
            )

        result.append(values[0])

    return result
