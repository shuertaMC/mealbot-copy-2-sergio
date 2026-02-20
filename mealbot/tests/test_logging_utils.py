"""Tests for logging_utils.py response helpers."""

import json

import pytest
from flask import Flask


@pytest.fixture
def app():
    """Create a minimal Flask app for testing."""
    app = Flask(__name__)
    return app


class TestLogAndWriteErr:
    """Tests for log_and_write_err."""

    def test_returns_json_error_with_status(self, app):
        from mealbot.logging_utils import log_and_write_err

        with app.app_context():
            response = log_and_write_err(
                ValueError("something went wrong"), 400, "TestFunction"
            )
            assert response.status_code == 400
            data = json.loads(response.get_data(as_text=True))
            assert data == {"Message": "something went wrong"}

    def test_500_error(self, app):
        from mealbot.logging_utils import log_and_write_err

        with app.app_context():
            response = log_and_write_err(
                RuntimeError("db error"), 500, "TestFunction"
            )
            assert response.status_code == 500
            data = json.loads(response.get_data(as_text=True))
            assert data == {"Message": "db error"}

    def test_content_type_is_json(self, app):
        from mealbot.logging_utils import log_and_write_err

        with app.app_context():
            response = log_and_write_err(
                ValueError("test"), 400, "TestFunction"
            )
            assert "application/json" in response.content_type


class TestLogAndWrite:
    """Tests for log_and_write."""

    def test_string_passed_through_as_is(self, app):
        """log_and_write passes data as-is without wrapping."""
        from mealbot.logging_utils import log_and_write

        with app.app_context():
            response = log_and_write("plain text", 200, "TestFunction")
            assert response.status_code == 200
            assert response.get_data(as_text=True) == "plain text"

    def test_json_string_passed_through(self, app):
        """Pre-encoded JSON strings are passed through as-is."""
        from mealbot.logging_utils import log_and_write

        with app.app_context():
            body = json.dumps({"orgs": ["a", "b"]})
            response = log_and_write(body, 200, "TestFunction")
            assert response.status_code == 200
            data = json.loads(response.get_data(as_text=True))
            assert data == {"orgs": ["a", "b"]}

    def test_str_to_bytes_wraps_message(self, app):
        """str_to_bytes should wrap strings in Message format."""
        from mealbot.logging_utils import log_and_write, str_to_bytes

        with app.app_context():
            body = str_to_bytes("Success")
            response = log_and_write(body, 200, "TestFunction")
            assert response.status_code == 200
            data = json.loads(response.get_data(as_text=True))
            assert data == {"Message": "Success"}

    def test_status_201(self, app):
        from mealbot.logging_utils import log_and_write, str_to_bytes

        with app.app_context():
            response = log_and_write(str_to_bytes("Created"), 201, "TestFunction")
            assert response.status_code == 201
            data = json.loads(response.get_data(as_text=True))
            assert data == {"Message": "Created"}


class TestConvenienceWrappers:
    """Tests for LogAndWriteStatusBadRequest and LogAndWriteStatusInternalServerError."""

    def test_bad_request(self, app):
        from mealbot.logging_utils import log_and_write_status_bad_request

        with app.app_context():
            response = log_and_write_status_bad_request(
                ValueError("bad input"), "TestFunction"
            )
            assert response.status_code == 400
            data = json.loads(response.get_data(as_text=True))
            assert data == {"Message": "bad input"}

    def test_internal_server_error(self, app):
        from mealbot.logging_utils import (
            log_and_write_status_internal_server_error,
        )

        with app.app_context():
            response = log_and_write_status_internal_server_error(
                RuntimeError("db fail"), "TestFunction"
            )
            assert response.status_code == 500
            data = json.loads(response.get_data(as_text=True))
            assert data == {"Message": "db fail"}
