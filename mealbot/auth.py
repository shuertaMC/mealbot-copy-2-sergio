"""JWT authentication middleware for Flask.

Ported from: auth.go

Validates Auth0-issued JWT tokens using RS256 signing with JWKS.
Configuration is read from environment variables (instead of hardcoded
constants in the Go version):
  - AUTH0_ISSUER: e.g. "https://mealbot.auth0.com/"
  - AUTH0_AUDIENCE: e.g. "https://mealbot-2.herokuapp.com/"
  - AUTH0_JWKS_URL: e.g. "https://mealbot.auth0.com/.well-known/jwks.json"
"""

import functools
import json
import logging
import os
from typing import Optional

import jwt
import requests
from cryptography.x509 import load_pem_x509_certificate
from flask import Response, request

logger = logging.getLogger("mealbot.auth")


def _get_auth_config() -> dict[str, str]:
    """Read Auth0 configuration from environment variables.

    Uses Flask app config if available, otherwise falls back to
    environment variables.
    """
    return {
        "issuer": os.environ.get("AUTH0_ISSUER", ""),
        "audience": os.environ.get("AUTH0_AUDIENCE", ""),
        "jwks_url": os.environ.get("AUTH0_JWKS_URL", ""),
    }


def _get_jwks(jwks_url: str) -> dict:
    """Fetch the JSON Web Key Set from the Auth0 endpoint."""
    resp = requests.get(jwks_url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _get_pem_certificate(token_header: dict, jwks_url: str) -> Optional[str]:
    """Find the PEM certificate matching the token's kid from JWKS.

    Mirrors Go's getPEMCertificate function.

    Args:
        token_header: Decoded JWT header containing 'kid'.
        jwks_url: URL to fetch the JWKS from.

    Returns:
        PEM-formatted certificate string, or None if not found.
    """
    jwks = _get_jwks(jwks_url)
    kid = token_header.get("kid", "")

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            x5c = key.get("x5c", [])
            if x5c:
                return (
                    "-----BEGIN CERTIFICATE-----\n"
                    + x5c[0]
                    + "\n-----END CERTIFICATE-----"
                )

    return None


def _verify_audience(claims: dict, audience: str) -> bool:
    """Verify the audience claim, handling both string and array formats.

    Mirrors Go's verifyAudience which checks for audience in an array.
    """
    aud = claims.get("aud")
    if aud is None:
        return False

    if isinstance(aud, str):
        return aud == audience

    if isinstance(aud, list):
        return audience in aud

    return False


def get_auth_handler(f):
    """Decorator that validates JWT tokens on incoming requests.

    Equivalent to Go's GetAuthHandler middleware. Validates:
    - Bearer token is present in Authorization header.
    - Token uses RS256 signing.
    - Token issuer matches AUTH0_ISSUER.
    - Token audience includes AUTH0_AUDIENCE.
    - Token signature is valid using the JWKS public key.

    OPTIONS requests are passed through for CORS preflight.
    """

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # Allow preflight requests through (matches Go behavior)
        if request.method == "OPTIONS":
            return f(*args, **kwargs)

        config = _get_auth_config()

        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            logger.error("No authorization header")
            return Response(
                json.dumps({"Message": "No authorization header"}),
                status=401,
                content_type="application/json",
            )

        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.error("Authorization header format must be Bearer {token}")
            return Response(
                json.dumps(
                    {
                        "Message": "Authorization header format must be Bearer {token}"
                    }
                ),
                status=401,
                content_type="application/json",
            )

        token = parts[1]

        try:
            # Decode the header without verification to get kid and alg
            unverified_header = jwt.get_unverified_header(token)

            # Verify signing algorithm matches RS256
            if unverified_header.get("alg") != "RS256":
                logger.error("Token must use RS256 signing method")
                return Response(
                    json.dumps({"Message": "Token must use 'alg' signing method"}),
                    status=401,
                    content_type="application/json",
                )

            # Get PEM certificate from JWKS
            cert = _get_pem_certificate(unverified_header, config["jwks_url"])
            if cert is None:
                logger.error("Unable to find appropriate key")
                return Response(
                    json.dumps({"Message": "Unable to find appropriate key"}),
                    status=401,
                    content_type="application/json",
                )

            # Extract the public key from the X.509 certificate.
            # The Go code uses jwt.ParseRSAPublicKeyFromPEM(cert) which
            # extracts the RSA public key from the certificate. PyJWT's
            # jwt.decode can accept the PEM certificate directly when
            # using the cryptography backend.
            cert_obj = load_pem_x509_certificate(cert.encode("utf-8"))
            public_key = cert_obj.public_key()

            # Decode and validate the token
            decoded = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                issuer=config["issuer"],
                options={
                    "verify_aud": False,  # We'll verify manually like Go
                    "verify_iss": True,
                },
            )

            # Manual audience verification to match Go's verifyAudience behavior
            # Go treats aud as an array and checks if audience is in that array
            if not _verify_audience(decoded, config["audience"]):
                logger.error("Invalid audience")
                return Response(
                    json.dumps({"Message": "Invalid audience"}),
                    status=401,
                    content_type="application/json",
                )

        except jwt.ExpiredSignatureError:
            logger.error("Token is expired")
            return Response(
                json.dumps({"Message": "Token is expired"}),
                status=401,
                content_type="application/json",
            )
        except jwt.InvalidTokenError as e:
            logger.error("Token is invalid: %s", str(e))
            return Response(
                json.dumps({"Message": "Token is invalid"}),
                status=401,
                content_type="application/json",
            )
        except requests.RequestException as e:
            logger.error("JWKS fetch failed: %s", str(e))
            return Response(
                json.dumps({"Message": "PEM Certificate failed"}),
                status=401,
                content_type="application/json",
            )
        except Exception as e:
            logger.error("Auth error: %s", str(e))
            return Response(
                json.dumps({"Message": str(e)}),
                status=401,
                content_type="application/json",
            )

        return f(*args, **kwargs)

    return decorated
