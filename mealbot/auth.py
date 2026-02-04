"""Authentication middleware for the Mealbot API.

This module implements JWT validation using Auth0 JWKS, mirroring the behavior
of the Go implementation in auth.go. It provides a FastAPI dependency for
protecting endpoints with JWT authentication.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx
from cachetools import TTLCache
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWTError

from mealbot.config import get_settings

logger = logging.getLogger(__name__)

# Cache for JWKS keys with 1 hour TTL
# This improves performance over the Go implementation which fetches on every request
_jwks_cache: TTLCache = TTLCache(maxsize=10, ttl=3600)

# Security scheme for extracting Bearer token from Authorization header
security = HTTPBearer(auto_error=False)


class JSONWebKey:
    """Represents a JSON Web Key from the JWKS endpoint.

    Corresponds to the JSONWebKeys struct in auth.go.
    """

    def __init__(
        self,
        kty: str,
        kid: str,
        use: str,
        n: str,
        e: str,
        x5c: List[str],
    ):
        self.kty = kty
        self.kid = kid
        self.use = use
        self.n = n
        self.e = e
        self.x5c = x5c

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JSONWebKey":
        """Create a JSONWebKey from a dictionary."""
        return cls(
            kty=data.get("kty", ""),
            kid=data.get("kid", ""),
            use=data.get("use", ""),
            n=data.get("n", ""),
            e=data.get("e", ""),
            x5c=data.get("x5c", []),
        )


class JWKS:
    """Represents a JSON Web Key Set.

    Corresponds to the Jwks struct in auth.go.
    """

    def __init__(self, keys: List[JSONWebKey]):
        self.keys = keys

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JWKS":
        """Create a JWKS from a dictionary."""
        keys = [JSONWebKey.from_dict(k) for k in data.get("keys", [])]
        return cls(keys=keys)


def fetch_jwks(jwks_url: str) -> JWKS:
    """
    Fetch JWKS from the Auth0 endpoint.

    This function caches the result to avoid per-request HTTP calls,
    improving over the Go implementation which fetches on every request.

    Args:
        jwks_url: The URL to fetch JWKS from.

    Returns:
        JWKS object containing the keys.

    Raises:
        HTTPException: If the JWKS cannot be fetched or parsed.
    """
    # Check cache first
    if jwks_url in _jwks_cache:
        return _jwks_cache[jwks_url]

    try:
        with httpx.Client() as client:
            response = client.get(jwks_url, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            jwks = JWKS.from_dict(data)
            # Cache the result
            _jwks_cache[jwks_url] = jwks
            logger.debug("Fetched and cached JWKS from %s", jwks_url)
            return jwks
    except httpx.HTTPError as e:
        logger.error("Failed to fetch JWKS: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch authentication keys",
        )
    except (KeyError, ValueError) as e:
        logger.error("Failed to parse JWKS: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse authentication keys",
        )


def get_pem_certificate(token: str, jwks_url: str) -> str:
    """
    Get the PEM certificate for a JWT token from JWKS.

    This mirrors the getPEMCertificate function in auth.go. It finds the
    key matching the token's 'kid' header and constructs the PEM certificate
    by wrapping the X5c value with BEGIN/END CERTIFICATE markers.

    Args:
        token: The JWT token string.
        jwks_url: The URL to fetch JWKS from.

    Returns:
        The PEM certificate string.

    Raises:
        HTTPException: If the appropriate key cannot be found.
    """
    # Get the unverified header to extract kid
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as e:
        logger.error("Failed to get token header: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )

    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing key ID",
        )

    jwks = fetch_jwks(jwks_url)

    # Find the key matching the token's kid
    for key in jwks.keys:
        if key.kid == kid:
            if not key.x5c:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Key missing certificate",
                )
            # Construct PEM certificate as in Go implementation
            cert = (
                "-----BEGIN CERTIFICATE-----\n"
                + key.x5c[0]
                + "\n-----END CERTIFICATE-----"
            )
            return cert

    # No matching key found - mirrors Go behavior
    logger.error("Unable to find appropriate key for kid: %s", kid)
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to find appropriate key",
    )


def verify_audience(claims: Dict[str, Any], audience: str) -> bool:
    """
    Verify the audience claim in JWT claims.

    This mirrors the verifyAudience function in auth.go (lines 169-184).
    The Go implementation handles 'aud' as a potentially array-like claim.

    Args:
        claims: The JWT claims dictionary.
        audience: The expected audience value.

    Returns:
        True if audience is valid, False otherwise.
    """
    if "aud" not in claims:
        return False

    aud = claims["aud"]

    # Handle both string and array audience formats
    if isinstance(aud, str):
        return aud == audience
    elif isinstance(aud, list):
        return audience in aud

    return False


def validate_token(token: str) -> Dict[str, Any]:
    """
    Validate a JWT token against Auth0 configuration.

    This implements the validation logic from GetAuthHandler in auth.go,
    including audience verification, issuer verification, and RS256 signature
    verification using the PEM certificate from JWKS.

    Args:
        token: The JWT token string.

    Returns:
        The validated token claims.

    Raises:
        HTTPException: If the token is invalid.
    """
    settings = get_settings()

    # Get PEM certificate for signature verification
    cert = get_pem_certificate(token, settings.auth0_jwks_url)

    try:
        # Decode and validate the token
        # Note: python-jose handles signature verification automatically
        claims = jwt.decode(
            token,
            cert,
            algorithms=["RS256"],
            audience=settings.auth0_audience,
            issuer=settings.auth0_issuer,
        )
        return claims
    except ExpiredSignatureError:
        logger.warning("Token has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except JWTClaimsError as e:
        logger.warning("Invalid token claims: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
        )
    except JWTError as e:
        logger.warning("Token validation failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """
    FastAPI dependency to get the current authenticated user.

    This dependency extracts the Bearer token from the Authorization header,
    validates it against Auth0, and returns the user claims. It mirrors the
    CheckJWT method in auth.go.

    For OPTIONS requests (CORS preflight), authentication is bypassed.

    Usage:
        @app.get("/protected")
        def protected_route(user: dict = Depends(get_current_user)):
            return {"user": user["sub"]}

    Args:
        request: The FastAPI Request object.
        credentials: The HTTP Bearer credentials (auto-extracted).

    Returns:
        Dictionary containing the validated JWT claims.

    Raises:
        HTTPException: If authentication fails.
    """
    # Bypass authentication for OPTIONS requests (CORS preflight)
    # This mirrors the Go behavior in CheckJWT (auth.go line 48)
    if request.method == "OPTIONS":
        return {}

    if credentials is None:
        logger.warning("No authorization header provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    claims = validate_token(token)
    return claims


def clear_jwks_cache() -> None:
    """
    Clear the JWKS cache.

    This can be called if keys need to be refreshed manually,
    for example after a key rotation.
    """
    _jwks_cache.clear()
    logger.info("JWKS cache cleared")
