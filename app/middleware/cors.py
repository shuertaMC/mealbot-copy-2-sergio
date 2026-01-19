"""
CORS (Cross-Origin Resource Sharing) middleware configuration.

This module provides CORS policy configuration for the FastAPI application,
allowing the frontend (running on a different origin) to make requests to the API.
"""

# CORS configuration constants matching Go implementation
# From cors.go: AccessControlAllowHeaders
CORS_ALLOW_HEADERS = [
    "Authorization",
    "Content-Type",
    "Origin",
    "Accept",
    "token",
]

# From cors.go: Access-Control-Allow-Methods
CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "DELETE",
]


def get_cors_middleware_config() -> dict:
    """
    Get CORS middleware configuration for FastAPI.

    Returns configuration dict to be used with:
        app.add_middleware(CORSMiddleware, **get_cors_middleware_config())

    The Go implementation dynamically reflects the request's Origin header
    (sets Access-Control-Allow-Origin to the value of the Origin header).
    FastAPI's CORSMiddleware can achieve this with allow_origins=["*"] but
    we use allow_origin_regex to be more explicit.

    Returns:
        Dictionary with CORS configuration parameters
    """
    return {
        # Allow all origins (matches Go's dynamic Origin reflection)
        # Go: w.Header().Set("Access-Control-Allow-Origin", r.Header.Get("Origin"))
        "allow_origins": ["*"],
        # Credentials: Go does not set Access-Control-Allow-Credentials header
        # Explicitly set to False (compatible with allow_origins=["*"])
        "allow_credentials": False,
        # Allowed HTTP methods
        "allow_methods": CORS_ALLOW_METHODS,
        # Allowed request headers
        "allow_headers": CORS_ALLOW_HEADERS,
        # Expose headers to the browser
        # (Not explicitly set in Go, but commonly needed)
        "expose_headers": [],
        # Cache preflight responses for 1 hour (3600 seconds)
        "max_age": 3600,
    }


def setup_cors(app):
    """
    Add CORS middleware to FastAPI application.

    This is a convenience function for setting up CORS in app/main.py:
        from app.middleware.cors import setup_cors
        setup_cors(app)

    Args:
        app: FastAPI application instance
    """
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(CORSMiddleware, **get_cors_middleware_config())
