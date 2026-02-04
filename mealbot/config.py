from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Server
    port: int = 8080

    # Database
    database_url: str

    # Mailgun
    mailgun_smtp_login: str = ""
    mailgun_domain: str = ""
    mailgun_api_key: str = ""

    # Auth0
    auth0_domain: str = ""
    auth0_audience: str = ""
    auth0_issuer: str = ""
    auth0_jwks_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


def get_settings() -> Settings:
    """Get the application settings instance."""
    return Settings()
