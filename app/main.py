"""
Main FastAPI application for Mealbot.

This module initializes the FastAPI app, applies middleware (CORS, authentication),
registers routers, and configures static file serving.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.organizations import router as organizations_router
from app.config import get_settings
from app.logging_config import configure_logging
from app.middleware.cors import setup_cors

# Initialize logging
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.

    Handles startup and shutdown events for the application.
    This is the modern FastAPI pattern (replaces @app.on_event decorators).

    Startup:
        - Log application startup
        - Initialize any resources (database connections, etc.)

    Shutdown:
        - Log application shutdown
        - Clean up resources
    """
    # Startup
    settings = get_settings()
    logger.info(
        "Starting Mealbot application",
        extra={"port": settings.port, "debug": settings.debug},
    )

    yield

    # Shutdown
    logger.info("Shutting down Mealbot application")


# Create FastAPI application
app = FastAPI(
    title="Mealbot API",
    description="Meal pairing application for organizing lunch/dinner meetings",
    version="1.0.0",
    lifespan=lifespan,
)

# Apply CORS middleware
# This must be added before routes are registered
# Matches Go's middleware order: auth.go -> cors.go
setup_cors(app)

# Register routers
# Organization API endpoints: /orgs, /org, /crossmatchtrait
app.include_router(organizations_router, tags=["organizations"])

# Mount static files at root path
# Serves privacy.html and other static files from ./static directory
# Matches Go's http.FileServer(http.Dir("./static"))
# NOTE: This must be added AFTER all other routes, as it uses a catch-all pattern
app.mount("/", StaticFiles(directory="static", html=True), name="static")


# Health check endpoint (useful for container orchestration and monitoring)
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns basic status information about the application.
    Useful for container orchestration (Kubernetes, ECS) and monitoring.

    Returns:
        dict: Status information
    """
    return {"status": "healthy", "service": "mealbot"}


# Root endpoint (will be overridden by static files, but useful for debugging)
@app.get("/api", tags=["info"])
async def root():
    """
    API information endpoint.

    Returns basic information about the API.

    Returns:
        dict: API information
    """
    return {
        "name": "Mealbot API",
        "version": "1.0.0",
        "description": "Meal pairing application",
    }
