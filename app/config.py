"""
Configuration management for Mealbot application.

This module defines application settings using Pydantic BaseSettings,
which loads configuration from environment variables and .env files.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Settings can be provided via:
    - Environment variables
    - .env file in the project root (for local development)

    For production deployment (e.g., Heroku), set these as environment variables.
    """

    # Database Configuration
    database_url: str
    """PostgreSQL database URL (e.g., postgresql://user:pass@host:5432/db)"""

    # Server Configuration
    port: int = 8080
    """HTTP server port"""

    # Auth0 Configuration
    auth0_issuer: str = "https://mealbot.auth0.com/"
    """Auth0 JWT token issuer URL"""

    auth0_audience: str = "https://mealbot-2.herokuapp.com/"
    """Auth0 JWT token audience"""

    auth0_jwks_url: str = "https://mealbot.auth0.com/.well-known/jwks.json"
    """Auth0 JWKS (JSON Web Key Set) endpoint for JWT verification"""

    # Mailgun Configuration
    mailgun_domain: str
    """Mailgun domain for sending emails"""

    mailgun_api_key: str
    """Mailgun API key for authentication"""

    mailgun_smtp_login: str | None = None
    """Optional SMTP login for Mailgun (if using SMTP instead of API)"""

    # Application Configuration
    debug: bool = False
    """Enable debug mode (verbose logging, auto-reload, etc.)"""

    log_level: str = "INFO"
    """Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"""

    # CORS Configuration
    cors_origins: list[str] = ["*"]
    """List of allowed CORS origins. Use ["*"] to allow all origins."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


# Global settings instance
# This will be imported by other modules and FastAPI dependencies
# Note: In production, ensure environment variables are set before importing this module
# In tests, import Settings class directly instead of this instance
def get_settings() -> Settings:
    """
    Get or create the global settings instance.

    This function provides lazy initialization of settings,
    allowing tests to create their own Settings instances.
    """
    return Settings()
