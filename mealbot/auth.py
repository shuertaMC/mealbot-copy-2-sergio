"""
JWT authentication middleware.

Ported from auth.go. Implements RS256 JWT validation using PyJWT with
Auth0 JWKS fetching.

Design Decision #3: @require_jwt decorator applied per-route, closely
mirroring the Go middleware chain where GetAuthHandler wraps each handler.
"""

import functools
import json
import logging

import jwt
import requests
from flask import Response, request

logger = logging.getLogger(__name__)

# Auth constants matching auth.go
INVALID_ACCESS_TOKEN = "Invalid access token"
ISSUER = "https://mealbot.auth0.com/"
AUDIENCE = "https://mealbot-2.herokuapp.com/"
JSON_WEB_KEY_SET = "https://mealbot.auth0.com/.well-known/jwks.json"


def get_pem_certificate(token_header: dict) -> str:
    """
    Fetch the PEM certificate for a JWT from the Auth0 JWKS endpoint.

    Mirrors Go's getPEMCertificate: fetches JWKS on every request (no caching)
    and matches the kid from the token header.

    Args:
        token_header: The JWT header dict containing 'kid'.

    Returns:
        PEM-formatted certificate string.

    Raises:
        ValueError: If no matching key is found.
        requests.RequestException: If JWKS fetch fails.
    """
    resp = requests.get(JSON_WEB_KEY_SET, timeout=10)
    resp.raise_for_status()
    jwks = resp.json()

    cert = ""
    for key in jwks.get("keys", []):
        if token_header.get("kid") == key.get("kid"):
            x5c = key.get("x5c", [])
            if x5c:
                cert = (
                    "-----BEGIN CERTIFICATE-----\n"
                    + x5c[0]
                    + "\n-----END CERTIFICATE-----"
                )
                break

    if not cert:
        raise ValueError("Unable to find appropriate key")

    return cert


def verify_audience(claims: dict, audience: str) -> None:
    """
    Verify the audience claim in a JWT.

    Mirrors Go's verifyAudience: checks if the audience string is present
    in the 'aud' claim (which may be a list or a string).

    Raises:
        ValueError: If audience claim is missing or doesn't match.
    """
    aud = claims.get("aud")
    if aud is None:
        raise ValueError("No audience claim")

    # aud can be a string or a list
    if isinstance(aud, str):
        if aud == audience:
            return
    elif isinstance(aud, list):
        for item in aud:
            if item == audience:
                return

    raise ValueError("Invalid audience")


def check_jwt() -> str | None:
    """
    Validate the JWT from the current request's Authorization header.

    Mirrors Go's CustomJWTMiddleware.CheckJWT.

    Returns:
        None on success.

    Raises:
        ValueError: On any validation failure.
    """
    # Pass through OPTIONS preflight requests (matches Go behavior)
    if request.method == "OPTIONS":
        return None

    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        raise ValueError("No authorization header")

    parts = auth_header.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError("Authorization header format must be Bearer {token}")

    token_str = parts[1]

    # Decode header without verification to get kid for JWKS lookup
    try:
        unverified_header = jwt.get_unverified_header(token_str)
    except jwt.exceptions.DecodeError as e:
        raise ValueError(f"Invalid token: {e}")

    # Verify signing algorithm matches RS256
    if unverified_header.get("alg") != "RS256":
        raise ValueError("Token must use 'alg' signing method")

    # Fetch PEM certificate from JWKS
    cert = get_pem_certificate(unverified_header)

    # Decode and verify the token
    try:
        decoded = jwt.decode(
            token_str,
            cert,
            algorithms=["RS256"],
            options={
                # We do audience verification ourselves to match Go behavior
                "verify_aud": False,
            },
        )
    except jwt.ExpiredSignatureError:
        raise ValueError("Token is expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Token is invalid: {e}")

    # Verify audience (matches Go verifyAudience)
    verify_audience(decoded, AUDIENCE)

    # Verify issuer (matches Go VerifyIssuer)
    if decoded.get("iss") != ISSUER:
        raise ValueError("Invalid issuer")

    return None


def require_jwt(f):
    """
    Flask decorator that enforces JWT authentication on a route.

    Mirrors Go's GetAuthHandler middleware wrapper. Applied per-route:

        @app.route("/orgs")
        @require_jwt
        def get_orgs():
            ...

    On validation failure, the request is rejected (returns empty response
    matching Go behavior where handler.ServeHTTP is not called).
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            check_jwt()
        except (ValueError, requests.RequestException) as e:
            logger.error("JWT validation failed: %s", str(e))
            # Go behavior: prints error and returns without calling handler
            # This results in no response body being written.
            return Response(status=401)
        return f(*args, **kwargs)
    return decorated_function
