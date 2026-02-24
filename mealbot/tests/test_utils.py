"""
Tests for mealbot.utils module.

Tests the response helpers (str_to_bytes, err_to_bytes) and
query parameter extraction functions.
"""

import json

import pytest

from mealbot.utils import (
    err_to_bytes,
    get_query_param,
    get_query_params,
    log_and_write,
    log_and_write_err,
    log_and_write_status_bad_request,
    log_and_write_status_internal_server_error,
    str_to_bytes,
)


class TestStrToBytes:
    """Tests for str_to_bytes (ported from server.StrToBytes)."""

    def test_basic_message(self):
        result = json.loads(str_to_bytes("hello"))
        assert result == {"Message": "hello"}

    def test_empty_message(self):
        result = json.loads(str_to_bytes(""))
        assert result == {"Message": ""}

    def test_message_with_special_chars(self):
        result = json.loads(str_to_bytes('He said "hello" & goodbye'))
        assert result == {"Message": 'He said "hello" & goodbye'}

    def test_success_message(self):
        """Verify the exact format used by Go handlers."""
        result = json.loads(str_to_bytes("Successfully created new organization"))
        assert result == {"Message": "Successfully created new organization"}


class TestErrToBytes:
    """Tests for err_to_bytes (ported from server.ErrToBytes)."""

    def test_exception_message(self):
        err = ValueError("something went wrong")
        result = json.loads(err_to_bytes(err))
        assert result == {"Message": "something went wrong"}

    def test_string_message(self):
        result = json.loads(err_to_bytes("error text"))
        assert result == {"Message": "error text"}

    def test_empty_exception(self):
        err = ValueError("")
        result = json.loads(err_to_bytes(err))
        assert result == {"Message": ""}


class TestLogAndWrite:
    """Tests for log_and_write response helper."""

    def test_returns_response_with_correct_status(self):
        response = log_and_write('{"key": "value"}', 200, "TestFunc")
        assert response.status_code == 200
        assert response.mimetype == "application/json"

    def test_returns_response_body(self):
        body = str_to_bytes("test message")
        response = log_and_write(body, 201, "TestFunc")
        assert response.status_code == 201
        data = json.loads(response.get_data(as_text=True))
        assert data == {"Message": "test message"}


class TestLogAndWriteErr:
    """Tests for log_and_write_err response helper."""

    def test_returns_error_response(self):
        response = log_and_write_err("bad request", 400, "TestFunc")
        assert response.status_code == 400
        data = json.loads(response.get_data(as_text=True))
        assert data == {"Message": "bad request"}

    def test_exception_error(self):
        err = RuntimeError("internal error")
        response = log_and_write_err(err, 500, "TestFunc")
        assert response.status_code == 500
        data = json.loads(response.get_data(as_text=True))
        assert data == {"Message": "internal error"}


class TestLogAndWriteStatusBadRequest:
    """Tests for log_and_write_status_bad_request convenience wrapper."""

    def test_returns_400(self):
        response = log_and_write_status_bad_request("missing param", "TestFunc")
        assert response.status_code == 400


class TestLogAndWriteStatusInternalServerError:
    """Tests for log_and_write_status_internal_server_error convenience wrapper."""

    def test_returns_500(self):
        response = log_and_write_status_internal_server_error("db error", "TestFunc")
        assert response.status_code == 500


class TestGetQueryParam:
    """Tests for get_query_param (ported from utils.go getQueryParam)."""

    def test_single_param(self, app):
        with app.test_request_context("/?admin=john@test.com"):
            result = get_query_param("admin")
            assert result == "john@test.com"

    def test_missing_param_raises(self, app):
        with app.test_request_context("/"):
            with pytest.raises(ValueError, match="Request query parameters must contain admin"):
                get_query_param("admin")

    def test_multiple_values_raises(self, app):
        """Go behavior: error if len(queries) > 1."""
        with app.test_request_context("/?admin=a&admin=b"):
            with pytest.raises(ValueError, match="Request query parameters must contain admin"):
                get_query_param("admin")

    def test_empty_value_is_valid(self, app):
        """A parameter with an empty value is still present."""
        with app.test_request_context("/?org="):
            result = get_query_param("org")
            assert result == ""


class TestGetQueryParams:
    """Tests for get_query_params (ported from utils.go getQueryParams)."""

    def test_multiple_keys(self, app):
        with app.test_request_context("/?org=ysc&admin=john"):
            result = get_query_params(["org", "admin"])
            assert result == ["ysc", "john"]

    def test_missing_key_raises(self, app):
        with app.test_request_context("/?org=ysc"):
            with pytest.raises(ValueError, match="does not contain admin"):
                get_query_params(["org", "admin"])

    def test_empty_keys_list(self, app):
        with app.test_request_context("/"):
            result = get_query_params([])
            assert result == []
