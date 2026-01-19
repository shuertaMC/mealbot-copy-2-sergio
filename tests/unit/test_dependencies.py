"""
Unit tests for app/api/dependencies.py utilities.

Tests query parameter extraction, error handling, and logging utilities
to ensure they match the Go implementation behavior.
"""

import logging
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request
from starlette.datastructures import QueryParams

from app.api.dependencies import (
    get_query_param,
    get_query_params,
    log_and_raise_http_exception,
    raise_400,
    raise_500,
)


class TestGetQueryParam:
    """Test cases for get_query_param function."""

    def test_get_query_param_success(self):
        """Test successful extraction of a query parameter."""
        # Create a mock request with query parameters
        request = MagicMock(spec=Request)
        request.query_params = QueryParams({"admin": "user@example.com"})

        result = get_query_param(request, "admin")
        assert result == "user@example.com"

    def test_get_query_param_missing(self):
        """Test error when parameter is missing."""
        request = MagicMock(spec=Request)
        request.query_params = QueryParams({})

        with pytest.raises(HTTPException) as exc_info:
            get_query_param(request, "admin")

        assert exc_info.value.status_code == 400
        assert "Request query parameters must contain admin" in exc_info.value.detail

    def test_get_query_param_multiple_values(self):
        """Test error when parameter has multiple values."""
        request = MagicMock(spec=Request)
        # Create query params with multiple values for the same key
        request.query_params = QueryParams(
            [("admin", "user1@example.com"), ("admin", "user2@example.com")]
        )

        with pytest.raises(HTTPException) as exc_info:
            get_query_param(request, "admin")

        assert exc_info.value.status_code == 400
        assert "Request query parameters must contain admin" in exc_info.value.detail


class TestGetQueryParams:
    """Test cases for get_query_params function."""

    def test_get_query_params_success(self):
        """Test successful extraction of multiple query parameters."""
        request = MagicMock(spec=Request)
        request.query_params = QueryParams({"org": "acme", "admin": "user@example.com"})

        result = get_query_params(request, ["org", "admin"])
        assert result == ["acme", "user@example.com"]

    def test_get_query_params_missing_one(self):
        """Test error when one of the parameters is missing."""
        request = MagicMock(spec=Request)
        request.query_params = QueryParams({"org": "acme"})

        with pytest.raises(HTTPException) as exc_info:
            get_query_params(request, ["org", "admin"])

        assert exc_info.value.status_code == 400
        assert (
            "Request query parameters does not contain admin" in exc_info.value.detail
        )

    def test_get_query_params_multiple_values(self):
        """Test error when one parameter has multiple values."""
        request = MagicMock(spec=Request)
        request.query_params = QueryParams(
            [
                ("org", "acme"),
                ("admin", "user1@example.com"),
                ("admin", "user2@example.com"),
            ]
        )

        with pytest.raises(HTTPException) as exc_info:
            get_query_params(request, ["org", "admin"])

        assert exc_info.value.status_code == 400
        assert (
            "Request query parameters does not contain admin" in exc_info.value.detail
        )

    def test_get_query_params_empty_list(self):
        """Test that empty keys list returns empty result."""
        request = MagicMock(spec=Request)
        request.query_params = QueryParams({})

        result = get_query_params(request, [])
        assert result == []


class TestErrorHandling:
    """Test cases for error handling and logging utilities."""

    def test_log_and_raise_http_exception(self, caplog):
        """Test that log_and_raise_http_exception logs and raises correctly."""
        with caplog.at_level(logging.ERROR):
            with pytest.raises(HTTPException) as exc_info:
                log_and_raise_http_exception(
                    status_code=400,
                    detail="Invalid input",
                    function_name="test_function",
                )

        # Verify the exception
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Invalid input"

        # Verify logging occurred
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert "Invalid input" in caplog.records[0].message

    def test_raise_400(self):
        """Test convenience function for 400 errors."""
        with pytest.raises(HTTPException) as exc_info:
            raise_400("Bad request", "test_function")

        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "Bad request"

    def test_raise_500(self):
        """Test convenience function for 500 errors."""
        with pytest.raises(HTTPException) as exc_info:
            raise_500("Internal error", "test_function")

        assert exc_info.value.status_code == 500
        assert exc_info.value.detail == "Internal error"

    def test_log_and_raise_with_extra_fields(self, caplog):
        """Test that extra fields are included in logs."""
        with caplog.at_level(logging.ERROR):
            with pytest.raises(HTTPException):
                log_and_raise_http_exception(
                    status_code=400,
                    detail="Test error",
                    function_name="test_func",
                    user_id="123",
                    request_id="abc",
                )

        # Verify extra fields are in the log record
        record = caplog.records[0]
        assert hasattr(record, "user_id")
        assert hasattr(record, "request_id")
        assert record.user_id == "123"
        assert record.request_id == "abc"
