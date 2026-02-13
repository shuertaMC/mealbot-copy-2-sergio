"""Tests for utility functions.

These tests verify the logging helpers and query parameter utilities work correctly.
"""

import json
import pytest
from flask import Flask
from mealbot.utils import (
    str_to_bytes,
    err_to_bytes,
    log_and_write_err,
    log_and_write,
    log_and_write_status_bad_request,
    log_and_write_status_internal_server_error,
    QueryParamError,
    get_query_param,
    get_query_params,
)


class TestBytesHelpers:
    """Tests for str_to_bytes and err_to_bytes functions."""

    def test_str_to_bytes_returns_json(self):
        """Test that str_to_bytes returns JSON-encoded bytes."""
        result = str_to_bytes("hello world")
        assert result == b'{"message": "hello world"}'

    def test_str_to_bytes_handles_special_chars(self):
        """Test that str_to_bytes handles special characters."""
        result = str_to_bytes('test "quotes" and \\backslash')
        data = json.loads(result)
        assert data["message"] == 'test "quotes" and \\backslash'

    def test_err_to_bytes_returns_json(self):
        """Test that err_to_bytes returns JSON-encoded error message."""
        err = ValueError("something went wrong")
        result = err_to_bytes(err)
        assert result == b'{"message": "something went wrong"}'

    def test_err_to_bytes_with_exception(self):
        """Test that err_to_bytes handles Exception instances."""
        err = Exception("generic error")
        result = err_to_bytes(err)
        data = json.loads(result)
        assert data["message"] == "generic error"


class TestLogAndWriteHelpers:
    """Tests for log_and_write* functions."""

    def test_log_and_write_err_returns_response(self):
        """Test that log_and_write_err returns a Flask Response."""
        app = Flask(__name__)
        with app.app_context():
            response = log_and_write_err(ValueError("test error"), 500, "test_func")
            assert response.status_code == 500
            assert response.mimetype == "application/json"
            data = json.loads(response.data)
            assert data["message"] == "test error"

    def test_log_and_write_returns_response(self):
        """Test that log_and_write returns a Flask Response with data."""
        app = Flask(__name__)
        with app.app_context():
            response = log_and_write({"key": "value"}, 200, "test_func")
            assert response.status_code == 200
            assert response.mimetype == "application/json"
            data = json.loads(response.data)
            assert data["key"] == "value"

    def test_log_and_write_with_bytes(self):
        """Test that log_and_write handles bytes input."""
        app = Flask(__name__)
        with app.app_context():
            response = log_and_write(b'{"raw": "bytes"}', 200, "test_func")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["raw"] == "bytes"

    def test_log_and_write_status_bad_request(self):
        """Test that log_and_write_status_bad_request returns 400."""
        app = Flask(__name__)
        with app.app_context():
            response = log_and_write_status_bad_request(
                ValueError("bad request"), "test_func"
            )
            assert response.status_code == 400

    def test_log_and_write_status_internal_server_error(self):
        """Test that log_and_write_status_internal_server_error returns 500."""
        app = Flask(__name__)
        with app.app_context():
            response = log_and_write_status_internal_server_error(
                ValueError("internal error"), "test_func"
            )
            assert response.status_code == 500


class TestQueryParamHelpers:
    """Tests for query parameter extraction functions."""

    def test_get_query_param_extracts_single_param(self):
        """Test that get_query_param extracts a single query parameter."""
        app = Flask(__name__)
        with app.test_request_context("/?key=value"):
            result = get_query_param("key")
            assert result == "value"

    def test_get_query_param_raises_for_missing_param(self):
        """Test that get_query_param raises QueryParamError for missing param."""
        app = Flask(__name__)
        with app.test_request_context("/?other=value"):
            with pytest.raises(QueryParamError) as exc_info:
                get_query_param("key")
            assert "must contain key" in str(exc_info.value)

    def test_get_query_param_raises_for_multiple_values(self):
        """Test that get_query_param raises for multiple values of same param."""
        app = Flask(__name__)
        with app.test_request_context("/?key=value1&key=value2"):
            with pytest.raises(QueryParamError) as exc_info:
                get_query_param("key")
            assert "must contain key" in str(exc_info.value)

    def test_get_query_params_extracts_multiple_params(self):
        """Test that get_query_params extracts multiple parameters."""
        app = Flask(__name__)
        with app.test_request_context("/?a=1&b=2&c=3"):
            result = get_query_params(["a", "b", "c"])
            assert result == ["1", "2", "3"]

    def test_get_query_params_raises_for_missing_param(self):
        """Test that get_query_params raises for missing param."""
        app = Flask(__name__)
        with app.test_request_context("/?a=1"):
            with pytest.raises(QueryParamError) as exc_info:
                get_query_params(["a", "b"])
            assert "does not contain b" in str(exc_info.value)
