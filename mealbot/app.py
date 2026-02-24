"""
Flask application factory.

Ported from server.go. Implements:
  - create_app() factory with configuration loading, CORS, route registration,
    static file serving, and database pool initialization.
  - Middleware chain: CORS (flask-cors) → Auth (@require_jwt per-route).
  - Static files served from mealbot/static/ at the root path.

CORS behavior (from cors.go):
  The Go code echoes back the request's Origin header as
  Access-Control-Allow-Origin, sets specific allowed headers and methods,
  and returns early on OPTIONS requests. flask-cors with
  `supports_credentials=False` and `origins="*"` combined with
  `send_wildcard=False` achieves the same echo-back behavior.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from . import db
from .auth import require_jwt
from .org import (
    create_organization_handler,
    cross_match_trait_handler,
    get_organizations_handler,
)

logger = logging.getLogger(__name__)


def create_app(test_config: dict | None = None) -> Flask:
    """
    Flask application factory.

    Mirrors Go's main() function: sets up middleware, registers routes,
    configures static file serving, and initializes the database pool.

    Args:
        test_config: Optional dict of config overrides for testing.
                     If provided, .env is NOT loaded and DB pool init
                     can be skipped by setting SKIP_DB_INIT=True.
    """
    # Load .env in development (before creating Flask app)
    if test_config is None:
        load_dotenv()

    # Create Flask app with static file serving
    # Go serves static files at "/" via http.FileServer(http.Dir("./static"))
    # Flask's static_url_path="" + static_folder="static" achieves the same.
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="",
    )

    # Apply test configuration if provided
    if test_config is not None:
        app.config.update(test_config)

    # Configure logging
    _configure_logging(app)

    # Initialize CORS (from cors.go)
    # Go behavior: echoes Origin header back as Access-Control-Allow-Origin
    # flask-cors with origins="*" and send_wildcard=False echoes the Origin
    CORS(
        app,
        # Matches Go: w.Header().Set("Access-Control-Allow-Origin", r.Header.Get("Origin"))
        origins="*",
        send_wildcard=False,
        # Matches Go: AccessControlAllowHeaders constant
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Origin",
            "Accept",
            "token",
        ],
        # Matches Go: "GET, POST, DELETE"
        methods=["GET", "POST", "DELETE", "OPTIONS"],
    )

    # Initialize database pool (skip in test mode if requested)
    if not app.config.get("SKIP_DB_INIT"):
        try:
            db.init_pool(database_url=app.config.get("DATABASE_URL"))
        except Exception as e:
            logger.error("Failed to initialize database pool: %s", e)
            # Don't crash on startup if DB is unavailable; routes will fail
            # gracefully when they try to use the pool.

    # Register teardown to close pool
    @app.teardown_appcontext
    def close_db_pool(exception=None):
        # Pool cleanup is handled at app shutdown, not per-request
        pass

    # Register routes with authentication middleware
    # Mirrors Go's serveMux.Handle("/orgs", mw.Apply(GetOrganizationsHandler))
    app.add_url_rule(
        "/orgs",
        endpoint="get_organizations",
        view_func=require_jwt(get_organizations_handler),
        methods=["GET", "OPTIONS"],
    )

    # Mirrors Go: serveMux.Handle("/org", mw.Apply(CreateOrganizationHandler))
    app.add_url_rule(
        "/org",
        endpoint="create_organization",
        view_func=require_jwt(create_organization_handler),
        methods=["POST", "OPTIONS"],
    )

    # Mirrors Go: serveMux.Handle("/crossmatchtrait", mw.Apply(CrossMatchTraitHandler))
    app.add_url_rule(
        "/crossmatchtrait",
        endpoint="cross_match_trait",
        view_func=require_jwt(cross_match_trait_handler),
        methods=["POST", "OPTIONS"],
    )

    logger.info("Mealbot Flask application initialized.")
    return app


def _configure_logging(app: Flask) -> None:
    """
    Configure logging to match Go's logrus-based logging.

    Sets up structured logging format with timestamp, level, and message.
    """
    log_level = logging.DEBUG if app.debug else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Configure root logger for the mealbot package
    mealbot_logger = logging.getLogger("mealbot")
    mealbot_logger.setLevel(log_level)
    mealbot_logger.addHandler(handler)
    # Prevent duplicate logging from Flask's default handler
    mealbot_logger.propagate = False
