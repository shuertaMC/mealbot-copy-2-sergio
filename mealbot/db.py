"""Database connection pooling and helper functions.

Provides a global connection pool using psycopg_pool.ConnectionPool,
with helper functions for common database operations. All domain modules
(organizations.py, members.py, rounds.py, pairs.py, pairing.py) use
these helpers for database access.

Ported from: db.go + vendor/github.com/johnamadeo/server/dbconn.go
"""

import os
from contextlib import contextmanager
from typing import Any, Optional

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

# Error message constant matching Go's DuplicateKeyErr
DUPLICATE_KEY_ERR = "duplicate key value violates unique constraint"

# Global connection pool, initialized lazily via init_db()
_pool: Optional[ConnectionPool] = None


def init_db(database_url: Optional[str] = None) -> None:
    """Initialize the global connection pool.

    Args:
        database_url: PostgreSQL connection URL. If not provided,
                      reads from DATABASE_URL environment variable.
    """
    global _pool
    if _pool is not None:
        return

    url = database_url or os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set and no URL was provided"
        )

    _pool = ConnectionPool(url, min_size=1, max_size=10)


def get_pool() -> ConnectionPool:
    """Return the global connection pool, initializing if needed."""
    if _pool is None:
        init_db()
    assert _pool is not None
    return _pool


@contextmanager
def get_connection():
    """Context manager that checks out a connection from the pool."""
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


def fetch_all(sql: str, params: Optional[tuple] = None) -> list[dict[str, Any]]:
    """Execute a query and return all rows as dicts.

    Args:
        sql: SQL query with $1, $2, ... placeholders.
        params: Tuple of parameter values.

    Returns:
        List of dicts, one per row.
    """
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()


def fetch_one(sql: str, params: Optional[tuple] = None) -> Optional[dict[str, Any]]:
    """Execute a query and return the first row as a dict, or None.

    Args:
        sql: SQL query with $1, $2, ... placeholders.
        params: Tuple of parameter values.

    Returns:
        Dict for the first row, or None if no rows.
    """
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()


def execute(sql: str, params: Optional[tuple] = None) -> None:
    """Execute a statement (INSERT, UPDATE, DELETE) with no return value.

    Args:
        sql: SQL statement with $1, $2, ... placeholders.
        params: Tuple of parameter values.
    """
    pool = get_pool()
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
        conn.commit()


def close_pool() -> None:
    """Close the global connection pool."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
