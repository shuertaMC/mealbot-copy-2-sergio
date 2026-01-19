"""
Middleware package for Mealbot application.

Provides authentication (JWT/Auth0) and CORS functionality.
"""

from app.middleware.auth import get_current_user
from app.middleware.cors import get_cors_middleware_config, setup_cors

__all__ = [
    "get_current_user",
    "get_cors_middleware_config",
    "setup_cors",
]
