"""Flask application entry point and route registration.

Ported from: server.go

Creates the Flask application, registers middleware (CORS, auth),
registers routes for all domain handlers, and configures static
file serving. Also provides a CLI entry point.
"""

import logging
import os

from dotenv import load_dotenv
from flask import Flask

# Load .env before anything else reads environment variables
load_dotenv()


def create_app(testing: bool = False) -> Flask:
    """Create and configure the Flask application.

    Args:
        testing: If True, disables auth middleware for testing.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="/",
    )

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # Initialize CORS middleware
    from .cors import init_cors

    init_cors(app)

    # Initialize database connection pool (skip in testing if no DB)
    if not testing:
        from .db import init_db

        try:
            init_db()
        except RuntimeError:
            # Allow app to start without DB for development/testing
            logging.getLogger("mealbot").warning(
                "DATABASE_URL not set; database features will be unavailable"
            )

    # Register routes
    _register_routes(app, testing=testing)

    return app


def _register_routes(app: Flask, testing: bool = False) -> None:
    """Register all URL routes on the Flask app.

    Mirrors the route registration in Go's main() using http.NewServeMux.

    Args:
        app: The Flask application.
        testing: If True, skips auth decorator.
    """
    from .auth import get_auth_handler
    from .organizations import (
        create_organization_handler,
        cross_match_trait_handler,
        get_organizations_handler,
    )

    # Choose whether to apply auth middleware
    if testing:
        auth = lambda f: f  # noqa: E731 — no-op decorator for testing
    else:
        auth = get_auth_handler

    # Organization routes
    # Go: serveMux.Handle("/orgs", mw.Apply(GetOrganizationsHandler))
    app.add_url_rule(
        "/orgs",
        endpoint="get_organizations",
        view_func=auth(get_organizations_handler),
        methods=["GET", "OPTIONS"],
    )

    # Go: serveMux.Handle("/org", mw.Apply(CreateOrganizationHandler))
    app.add_url_rule(
        "/org",
        endpoint="create_organization",
        view_func=auth(create_organization_handler),
        methods=["POST", "OPTIONS"],
    )

    # Go: serveMux.Handle("/crossmatchtrait", mw.Apply(CrossMatchTraitHandler))
    app.add_url_rule(
        "/crossmatchtrait",
        endpoint="cross_match_trait",
        view_func=auth(cross_match_trait_handler),
        methods=["POST", "OPTIONS"],
    )

    # Static files are handled by Flask's built-in static file server
    # configured via static_folder="static" and static_url_path="/"
    # This mirrors Go's: serveMux.Handle("/", http.FileServer(http.Dir("./static")))


# Application instance for direct use
app = create_app()

if __name__ == "__main__":
    port = os.environ.get("PORT", "8080")
    app.run(host="0.0.0.0", port=int(port))
