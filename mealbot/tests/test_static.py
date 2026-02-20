"""Tests for static file serving."""

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
    return app.test_client()


class TestStaticFiles:
    """Tests for static file serving."""

    def test_privacy_html_served(self, client):
        """privacy.html should be accessible at /privacy.html."""
        response = client.get("/privacy.html")
        assert response.status_code == 200
        assert b"Privacy Policy" in response.data

    def test_sample_csv_served(self, client):
        """sample.csv should be accessible at /sample.csv."""
        response = client.get("/sample.csv")
        assert response.status_code == 200
        assert b"Name,Email" in response.data
