"""Tests for utils.py query parameter helpers."""

import pytest
from flask import Flask


@pytest.fixture
def app():
    """Create a minimal Flask app for testing."""
    app = Flask(__name__)
    return app


class TestGetQueryParam:
    """Tests for get_query_param."""

    def test_single_param_present(self, app):
        from mealbot.utils import get_query_param

        with app.test_request_context("/?org=myorg"):
            from flask import request

            value, err = get_query_param(request, "org")
            assert value == "myorg"
            assert err is None

    def test_param_missing(self, app):
        from mealbot.utils import get_query_param

        with app.test_request_context("/"):
            from flask import request

            value, err = get_query_param(request, "org")
            assert value == ""
            assert err is not None
            assert "org" in str(err)

    def test_param_duplicate(self, app):
        from mealbot.utils import get_query_param

        with app.test_request_context("/?org=a&org=b"):
            from flask import request

            value, err = get_query_param(request, "org")
            assert value == ""
            assert err is not None

    def test_param_empty_value(self, app):
        from mealbot.utils import get_query_param

        with app.test_request_context("/?org="):
            from flask import request

            value, err = get_query_param(request, "org")
            assert value == ""
            assert err is None


class TestGetQueryParams:
    """Tests for get_query_params."""

    def test_all_params_present(self, app):
        from mealbot.utils import get_query_params

        with app.test_request_context("/?org=myorg&admin=test@test.com"):
            from flask import request

            values, err = get_query_params(request, ["org", "admin"])
            assert values == ["myorg", "test@test.com"]
            assert err is None

    def test_one_param_missing(self, app):
        from mealbot.utils import get_query_params

        with app.test_request_context("/?org=myorg"):
            from flask import request

            values, err = get_query_params(request, ["org", "admin"])
            assert values == []
            assert err is not None
            assert "admin" in str(err)

    def test_duplicate_param(self, app):
        from mealbot.utils import get_query_params

        with app.test_request_context("/?org=a&org=b&admin=test"):
            from flask import request

            values, err = get_query_params(request, ["org", "admin"])
            assert values == []
            assert err is not None

    def test_empty_keys_list(self, app):
        from mealbot.utils import get_query_params

        with app.test_request_context("/"):
            from flask import request

            values, err = get_query_params(request, [])
            assert values == []
            assert err is None
