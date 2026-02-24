"""
Database connection and pooling layer.

Ported from db.go + vendor/github.com/johnamadeo/server/dbconn.go.

Uses psycopg 3 with connection pooling. The Go application created a new DB
connection on every function call; this module improves on that by maintaining
a module-level ConnectionPool singleton.

Design Decision #1: Module-level pool with get_connection() context manager.
Domain functions accept a connection parameter, keeping them framework-agnostic
and testable (important for CLI commands in future milestones).

Design Decision #2: JSONB is handled natively by psycopg 3 — dicts are
automatically serialized/deserialized for JSONB columns, so no custom wrapper
is needed.
"""

import logging
import os
from contextlib import contextmanager

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

# Module-level pool singleton; initialized by init_pool().
_pool: ConnectionPool | None = None

# Error constant matching Go's DuplicateKeyErr from db.go
DUPLICATE_KEY_ERR = "duplicate key value violates unique constraint"


def get_database_url() -> str:
    """
    Return the database connection string.

    Mirrors the Go logic in dbconn.go: use DATABASE_URL env var if set,
    otherwise fall back to a local connection string.
    """
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        return db_url
    # Fallback for local development (mirrors Go's createLocalDBUrl)
    user = os.environ.get("DB_USER", "postgres")
    dbname = os.environ.get("DB_NAME", "mealbot")
    return f"user={user} dbname={dbname} sslmode=disable"


def init_pool(database_url: str | None = None, min_size: int = 2, max_size: int = 10) -> None:
    """
    Initialize the global connection pool.

    Called during create_app() startup. Accepts an optional explicit URL;
    otherwise reads from environment via get_database_url().
    """
    global _pool
    if _pool is not None:
        logger.warning("Connection pool already initialized; closing existing pool.")
        _pool.close()

    conninfo = database_url or get_database_url()
    logger.info("Initializing database connection pool.")
    _pool = ConnectionPool(
        conninfo=conninfo,
        min_size=min_size,
        max_size=max_size,
        kwargs={"row_factory": dict_row},
    )


def close_pool() -> None:
    """Close the global connection pool (e.g. on app teardown)."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
        logger.info("Database connection pool closed.")


@contextmanager
def get_connection():
    """
    Acquire a connection from the pool as a context manager.

    Usage:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT ...")

    The connection is automatically returned to the pool on exit.
    If an exception occurs, the transaction is rolled back.
    """
    if _pool is None:
        raise RuntimeError(
            "Database pool not initialized. Call init_pool() first."
        )
    with _pool.connection() as conn:
        yield conn


def fetch_all(query: str, params: tuple | None = None) -> list[dict]:
    """
    Execute a query and return all rows as a list of dicts.

    Convenience wrapper matching the Go pattern of query + rows.Next() loops.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()


def fetch_one(query: str, params: tuple | None = None) -> dict | None:
    """
    Execute a query and return a single row as a dict, or None.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()


def execute(query: str, params: tuple | None = None) -> None:
    """
    Execute a statement (INSERT, UPDATE, DELETE) and commit.

    Mirrors the Go db.Exec() pattern.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
        conn.commit()
