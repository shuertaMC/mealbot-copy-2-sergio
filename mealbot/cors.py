"""CORS middleware configuration for the Mealbot API.

This module mirrors the CORS behavior from the Go implementation in cors.go.
The Go implementation dynamically sets Access-Control-Allow-Origin to match the
request's Origin header.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Headers allowed by the Go implementation
ALLOWED_HEADERS = ["Authorization", "Content-Type", "Origin", "Accept", "token"]

# Methods allowed by the Go implementation
ALLOWED_METHODS = ["GET", "POST", "DELETE", "OPTIONS"]


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware on the FastAPI application.

    The Go implementation dynamically echoes the Origin header back as
    Access-Control-Allow-Origin. In FastAPI, we achieve similar behavior
    by using allow_origins=["*"] with allow_credentials=True, or by using
    a regex pattern. For maximum compatibility with the Go behavior,
    we use allow_origin_regex to match any origin.

    Args:
        app: The FastAPI application instance to configure.
    """
    app.add_middleware(
        CORSMiddleware,
        # Match any origin - mirrors Go's behavior of echoing back the Origin header
        allow_origin_regex=".*",
        allow_credentials=True,
        allow_methods=ALLOWED_METHODS,
        allow_headers=ALLOWED_HEADERS,
        expose_headers=[],
    )
