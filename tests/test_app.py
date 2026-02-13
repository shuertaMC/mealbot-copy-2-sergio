"""Smoke tests for the Flask application.

These tests verify that the Flask app can be created and responds to requests,
static files are served correctly, and CORS headers are set correctly.
"""

import pytest
from mealbot.app import create_app


@pytest.fixture
def app():
    """Create a Flask application for testing."""
    app = create_app({"TESTING": True})
    return app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


class TestAppCreation:
    """Tests for Flask application creation."""

    def test_create_app_returns_flask_instance(self):
        """Test that create_app() returns a Flask application instance."""
        app = create_app()
        assert app is not None
        assert app.name == "mealbot.app"

    def test_create_app_with_config(self):
        """Test that create_app() accepts custom configuration."""
        app = create_app({"TESTING": True, "DEBUG": False})
        assert app.config["TESTING"] is True
        assert app.config["DEBUG"] is False


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_endpoint_returns_ok(self, client):
        """Test that /health returns status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data == {"status": "ok"}


class TestStaticFiles:
    """Tests for static file serving."""

    def test_privacy_html_served(self, client):
        """Test that privacy.html is served at root path."""
        response = client.get("/privacy.html")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data
        assert b"Privacy Policy" in response.data

    def test_sample_csv_served(self, client):
        """Test that sample.csv is served at root path."""
        response = client.get("/sample.csv")
        assert response.status_code == 200
        assert b"Name,Email" in response.data


class TestCorsHeaders:
    """Tests for CORS header configuration."""

    def test_cors_headers_on_get_request(self, client):
        """Test that CORS headers are set on GET requests with Origin header."""
        response = client.get("/health", headers={"Origin": "http://example.com"})
        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == "http://example.com"

    def test_cors_preflight_request(self, client):
        """Test that CORS preflight requests are handled correctly."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization, Content-Type",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == "http://example.com"
        # Check that allowed headers include the requested ones
        allowed_headers = response.headers.get("Access-Control-Allow-Headers", "")
        assert "Authorization" in allowed_headers
        assert "Content-Type" in allowed_headers
        # Check that allowed methods include GET, POST, DELETE
        allowed_methods = response.headers.get("Access-Control-Allow-Methods", "")
        assert "GET" in allowed_methods
        assert "POST" in allowed_methods
        assert "DELETE" in allowed_methods
