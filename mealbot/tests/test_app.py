"""
Tests for mealbot.app module.

Verifies the Flask app factory creates a working application with correct
configuration, CORS headers, and route registration.
"""

import json


class TestCreateApp:
    """Tests for the create_app() factory function."""

    def test_app_created_successfully(self, app):
        """Verify app factory returns a Flask application."""
        assert app is not None
        assert app.testing is True

    def test_app_has_registered_routes(self, app):
        """Verify all milestone 1 routes are registered."""
        rules = {rule.rule for rule in app.url_map.iter_rules()}
        assert "/orgs" in rules
        assert "/org" in rules
        assert "/crossmatchtrait" in rules

    def test_static_url_path_is_root(self, app):
        """Verify static files are served from root path (matching Go behavior)."""
        assert app.static_url_path == ""


class TestStaticFiles:
    """Tests for static file serving."""

    def test_privacy_html_served(self, client):
        """Verify privacy.html is accessible at /privacy.html."""
        response = client.get("/privacy.html")
        assert response.status_code == 200
        assert b"Privacy Policy" in response.data

    def test_sample_csv_served(self, client):
        """Verify sample.csv is accessible at /sample.csv."""
        response = client.get("/sample.csv")
        assert response.status_code == 200
        assert b"Name,Email" in response.data


class TestCORS:
    """Tests for CORS configuration (ported from cors.go behavior)."""

    def test_cors_headers_on_options(self, client):
        """Verify CORS headers are set on OPTIONS preflight requests."""
        response = client.options(
            "/orgs",
            headers={"Origin": "http://localhost:3000"},
        )
        # flask-cors should echo back the Origin
        assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"

    def test_cors_allow_headers(self, client):
        """Verify allowed headers match cors.go's AccessControlAllowHeaders."""
        # Proper CORS preflight requires Access-Control-Request-Method and
        # Access-Control-Request-Headers headers for flask-cors to respond
        # with Access-Control-Allow-Headers.
        response = client.options(
            "/orgs",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization, Content-Type",
            },
        )
        allow_headers = response.headers.get("Access-Control-Allow-Headers", "")
        # Check key headers from Go's constant
        assert "Authorization" in allow_headers
        assert "Content-Type" in allow_headers

    def test_cors_allows_different_origins(self, client):
        """Verify CORS echoes back different origins (Go echoes r.Header.Get("Origin"))."""
        response = client.options(
            "/org",
            headers={"Origin": "https://mealbot-web.herokuapp.com"},
        )
        assert (
            response.headers.get("Access-Control-Allow-Origin")
            == "https://mealbot-web.herokuapp.com"
        )

    def test_cors_allow_methods(self, client):
        """Verify allowed methods include GET, POST, DELETE."""
        # Proper CORS preflight requires Access-Control-Request-Method header
        # for flask-cors to respond with Access-Control-Allow-Methods.
        response = client.options(
            "/orgs",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        allow_methods = response.headers.get("Access-Control-Allow-Methods", "")
        assert "GET" in allow_methods
        assert "POST" in allow_methods
        assert "DELETE" in allow_methods
