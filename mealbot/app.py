"""Flask application factory for Mealbot.

This module provides the Flask application factory that mirrors the Go server setup
in server.go with CORS middleware from cors.go.
"""

import logging
import os

from flask import Flask
from flask_cors import CORS

try:
    from dotenv import load_dotenv
except ImportError:
    # python-dotenv is optional - only used in development
    def load_dotenv() -> None:
        pass

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(config: dict | None = None) -> Flask:
    """Create and configure the Flask application.

    This factory function creates a Flask app with CORS middleware and static file
    serving configured to match the Go implementation.

    Args:
        config: Optional configuration dictionary to override defaults.

    Returns:
        A configured Flask application instance.
    """
    # Load environment variables from .env file in development
    load_dotenv()

    # Create Flask app with static files served from the 'static' folder
    app = Flask(
        __name__,
        static_url_path="",
        static_folder="static",
    )

    # Apply any custom configuration
    if config:
        app.config.update(config)

    # Configure CORS to match the Go implementation in cors.go
    # Access-Control-Allow-Origin: mirrors the request's Origin header
    # Access-Control-Allow-Headers: "Authorization, Content-Type, Origin, Accept, token"
    # Access-Control-Allow-Methods: "GET, POST, DELETE"
    CORS(
        app,
        origins="*",  # Will reflect the Origin header due to supports_credentials
        allow_headers=["Authorization", "Content-Type", "Origin", "Accept", "token"],
        methods=["GET", "POST", "DELETE", "OPTIONS"],
        supports_credentials=False,
    )

    # Register a simple health check or index route
    @app.route("/health")
    def health_check():
        return {"status": "ok"}

    logger.info("Mealbot application created")
    return app


if __name__ == "__main__":
    # For development: run with flask run or python -m mealbot.app
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
