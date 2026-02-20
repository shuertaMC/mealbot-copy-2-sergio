"""CORS middleware for Flask.

Ported from: cors.go

Sets Cross-Origin Resource Sharing headers on all responses,
reflecting the request's Origin header back as the allowed origin
(matching the Go behavior). OPTIONS preflight requests are handled
by returning a 200 with CORS headers and an empty body.
"""

from flask import Flask, request

# Mirrors Go's AccessControlAllowHeaders constant
ACCESS_CONTROL_ALLOW_HEADERS = (
    "Authorization, Content-Type, Origin, Accept, token"
)


def init_cors(app: Flask) -> None:
    """Attach CORS handling to a Flask app via after_request hook.

    This replicates the behavior of Go's GetCorsHandler:
    - Sets Access-Control-Allow-Origin to the request's Origin header
    - Sets Access-Control-Allow-Headers
    - Sets Access-Control-Allow-Methods to GET, POST, DELETE
    - Returns early (200 with empty body) for OPTIONS preflight requests

    Args:
        app: The Flask application instance.
    """

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin", "")
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = (
            ACCESS_CONTROL_ALLOW_HEADERS
        )
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE"
        return response

    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            from flask import Response

            resp = Response("", status=200)
            origin = request.headers.get("Origin", "")
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Headers"] = (
                ACCESS_CONTROL_ALLOW_HEADERS
            )
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE"
            return resp
