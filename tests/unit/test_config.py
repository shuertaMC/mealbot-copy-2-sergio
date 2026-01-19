"""
Tests for configuration management.

These tests verify that the Pydantic settings class can be instantiated
and properly loads configuration values.
"""

import pytest
from pydantic import ValidationError


def test_settings_can_be_imported():
    """Test that Settings class can be imported."""
    from app.config import Settings

    assert Settings is not None


def test_settings_requires_database_url():
    """Test that database_url is a required field."""
    from app.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings(
            mailgun_domain="test.mailgun.org",
            mailgun_api_key="test-key",
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("database_url",) for error in errors)


def test_settings_requires_mailgun_domain():
    """Test that mailgun_domain is a required field."""
    from app.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings(
            database_url="postgresql://localhost/test",
            mailgun_api_key="test-key",
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("mailgun_domain",) for error in errors)


def test_settings_requires_mailgun_api_key():
    """Test that mailgun_api_key is a required field."""
    from app.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings(
            database_url="postgresql://localhost/test",
            mailgun_domain="test.mailgun.org",
        )

    errors = exc_info.value.errors()
    assert any(error["loc"] == ("mailgun_api_key",) for error in errors)


def test_settings_with_all_required_fields():
    """Test that Settings can be instantiated with all required fields."""
    from app.config import Settings

    settings = Settings(
        database_url="postgresql://localhost/test",
        mailgun_domain="test.mailgun.org",
        mailgun_api_key="test-key",
    )

    assert settings.database_url == "postgresql://localhost/test"
    assert settings.mailgun_domain == "test.mailgun.org"
    assert settings.mailgun_api_key == "test-key"


def test_settings_default_values():
    """Test that Settings has correct default values."""
    from app.config import Settings

    settings = Settings(
        database_url="postgresql://localhost/test",
        mailgun_domain="test.mailgun.org",
        mailgun_api_key="test-key",
    )

    assert settings.port == 8080
    assert settings.auth0_issuer == "https://mealbot.auth0.com/"
    assert settings.auth0_audience == "https://mealbot-2.herokuapp.com/"
    assert settings.auth0_jwks_url == "https://mealbot.auth0.com/.well-known/jwks.json"
    assert settings.debug is False
    assert settings.log_level == "INFO"
    assert settings.cors_origins == ["*"]
    assert settings.mailgun_smtp_login is None


def test_settings_can_override_defaults():
    """Test that default values can be overridden."""
    from app.config import Settings

    settings = Settings(
        database_url="postgresql://localhost/test",
        mailgun_domain="test.mailgun.org",
        mailgun_api_key="test-key",
        port=9000,
        debug=True,
        log_level="DEBUG",
        cors_origins=["http://localhost:3000"],
    )

    assert settings.port == 9000
    assert settings.debug is True
    assert settings.log_level == "DEBUG"
    assert settings.cors_origins == ["http://localhost:3000"]
