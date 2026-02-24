"""
Shared pytest fixtures for mealbot tests.

Provides a Flask test app and client configured for testing
without requiring a real database connection.
"""

import pytest

from mealbot.app import create_app


@pytest.fixture
def app():
    """Create a Flask application configured for testing."""
    app = create_app(test_config={
        "TESTING": True,
        "SKIP_DB_INIT": True,
    })
    yield app


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()
