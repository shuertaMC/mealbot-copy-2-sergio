"""Tests for database module.

These tests verify the database connection factory works correctly.
Note: Tests that require an actual database connection are skipped
if DATABASE_URL is not set.
"""

import os
import pytest
from mealbot.db import get_connection, create_connection, DUPLICATE_KEY_ERR


class TestDatabaseConstants:
    """Tests for database module constants."""

    def test_duplicate_key_err_constant(self):
        """Test that DUPLICATE_KEY_ERR constant is defined correctly."""
        assert DUPLICATE_KEY_ERR == "duplicate key value violates unique constraint"


class TestConnectionFactory:
    """Tests for database connection factory functions."""

    def test_get_connection_function_exists(self):
        """Test that get_connection function is available."""
        assert callable(get_connection)

    def test_create_connection_function_exists(self):
        """Test that create_connection function is available."""
        assert callable(create_connection)

    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="DATABASE_URL not set - skipping live database test",
    )
    def test_get_connection_returns_connection(self):
        """Test that get_connection returns a psycopg connection."""
        conn = get_connection()
        try:
            # Verify we can execute a simple query
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                assert result[0] == 1
        finally:
            conn.close()

    @pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="DATABASE_URL not set - skipping live database test",
    )
    def test_create_connection_returns_connection(self):
        """Test that create_connection returns a psycopg connection."""
        conn = create_connection()
        try:
            # Verify we can execute a simple query
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                assert result[0] == 1
        finally:
            conn.close()
