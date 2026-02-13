"""Database connection factory for PostgreSQL using psycopg 3.x.

This module provides database connection utilities that mirror the Go implementation
in db.go and vendor/github.com/johnamadeo/server/dbconn.go.
"""

import os
import logging

import psycopg

logger = logging.getLogger(__name__)

# Error message for duplicate key constraint violations
DUPLICATE_KEY_ERR = "duplicate key value violates unique constraint"


def get_connection():
    """Create and return a new database connection.

    Uses DATABASE_URL environment variable when available (production/Heroku),
    otherwise falls back to a local development default.

    Returns:
        psycopg.Connection: A new database connection.

    Raises:
        psycopg.Error: If the connection cannot be established.
    """
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        # Production: use DATABASE_URL from environment
        # Handle Heroku's postgres:// vs postgresql:// URL scheme
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return psycopg.connect(database_url)
    else:
        # Development: use local connection defaults
        # This mirrors the Go LocalDBConnection struct defaults
        return psycopg.connect(
            dbname="mealbot",
            user=os.environ.get("USER", ""),
            host="localhost",
        )


def create_connection():
    """Alias for get_connection() for API compatibility.

    Returns:
        psycopg.Connection: A new database connection.
    """
    return get_connection()
