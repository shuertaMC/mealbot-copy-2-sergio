"""Tests for CORS middleware behavior."""

import json
from unittest.mock import patch

import pytest

from mealbot.app import create_app


@pytest.fixture
def app():
    """Create a Flask app in testing mode."""
    app = create_app(testing=True)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()


class TestCorsHeaders:
    """Tests for CORS header injection."""

    @patch("mealbot.organizations.fetch_all")
    def test_cors_reflects_origin(self, mock_fetch, client):
        """CORS should reflect the request Origin header."""
        mock_fetch.return_value = []
        response = client.get(
            "/orgs?admin=test@test.com",
            headers={"Origin": "http://localhost:3000"},
        )
        assert (
            response.headers.get("Access-Control-Allow-Origin")
            == "http://localhost:3000"
        )

    @patch("mealbot.organizations.fetch_all")
    def test_cors_allow_headers(self, mock_fetch, client):
        """CORS should include proper allow headers."""
        mock_fetch.return_value = []
        response = client.get(
            "/orgs?admin=test@test.com",
            headers={"Origin": "http://example.com"},
        )
        allow_headers = response.headers.get("Access-Control-Allow-Headers")
        assert "Authorization" in allow_headers
        assert "Content-Type" in allow_headers

    @patch("mealbot.organizations.fetch_all")
    def test_cors_allow_methods(self, mock_fetch, client):
        """CORS should allow GET, POST, DELETE methods."""
        mock_fetch.return_value = []
        response = client.get(
            "/orgs?admin=test@test.com",
            headers={"Origin": "http://example.com"},
        )
        allow_methods = response.headers.get("Access-Control-Allow-Methods")
        assert "GET" in allow_methods
        assert "POST" in allow_methods
        assert "DELETE" in allow_methods


class TestOptionsPreflightHandler:
    """Tests for OPTIONS preflight handling."""

    def test_options_returns_200(self, client):
        """OPTIONS requests should return 200 with CORS headers."""
        response = client.options(
            "/orgs",
            headers={"Origin": "http://localhost:3000"},
        )
        assert response.status_code == 200

    def test_options_has_cors_headers(self, client):
        """OPTIONS should include all CORS headers."""
        response = client.options(
            "/orgs",
            headers={"Origin": "https://mealbot-web.herokuapp.com"},
        )
        assert (
            response.headers.get("Access-Control-Allow-Origin")
            == "https://mealbot-web.herokuapp.com"
        )
        assert "Access-Control-Allow-Headers" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
