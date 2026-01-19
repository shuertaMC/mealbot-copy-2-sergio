"""
Mealbot application package.

This module initializes the application-wide logging configuration
when the app package is imported.
"""

# Import logging configuration to make it available
from app.logging_config import configure_logging

# Note: configure_logging() should be called explicitly in main.py
# when the FastAPI application starts. This import just makes it available.

__all__ = ["configure_logging"]
