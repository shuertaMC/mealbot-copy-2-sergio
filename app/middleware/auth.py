"""
JWT authentication middleware for Auth0 integration.

This module provides JWT validation using Auth0's RS256-signed tokens,
including JWKS fetching, audience/issuer verification, and signature validation.
"""

import time
from typing import Optional

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import Settings, get_settings

# Error message constants matching Go implementation (auth.go:14-15, and other error strings)
INVALID_ACCESS_TOKEN = "Invalid access token"
INVALID_AUDIENCE = "Invalid audience"
INVALID_ISSUER = "Invalid issuer"
TOKEN_INVALID = "Token is invalid"
NO_AUTHORIZATION_HEADER = "No authorization header"
AUTH_HEADER_FORMAT_ERROR = "Authorization header format must be Bearer {token}"
NO_AUDIENCE_CLAIM = "No audience claim"
NO_ISSUER_CLAIM = "No issuer claim"
PEM_CERTIFICATE_FAILED = "PEM Certificate failed"
TOKEN_MUST_USE_ALG = "Token must use 'alg' signing method"
UNABLE_TO_FIND_KEY = "Unable to find appropriate key"

# Simple in-memory cache for JWKS
# Structure: {"jwks": {...}, "fetched_at": timestamp}
# NOTE: This is an intentional improvement over Go's implementation (auth.go:137-165)
# which fetches JWKS on every request. The task architecture notes suggest implementing
# caching for better performance. The 1-hour TTL balances performance with key rotation.
_jwks_cache: dict = {}
_JWKS_CACHE_TTL = 3600  # 1 hour in seconds


async def fetch_jwks(jwks_url: str) -> dict:
    """
    Fetch JWKS (JSON Web Key Set) from Auth0.

    Implements simple in-memory caching with 1-hour TTL to avoid
    fetching JWKS on every request (improves performance over Go implementation).

    Args:
        jwks_url: URL to Auth0's JWKS endpoint

    Returns:
        JWKS dictionary containing public keys

    Raises:
        HTTPException: If JWKS fetch fails
    """
    global _jwks_cache

    # Check cache
    if _jwks_cache:
        cached_jwks = _jwks_cache.get("jwks")
        fetched_at = _jwks_cache.get("fetched_at", 0)
        current_time = time.time()

        # Return cached JWKS if still valid
        if cached_jwks and (current_time - fetched_at) < _JWKS_CACHE_TTL:
            return cached_jwks

    # Fetch fresh JWKS
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            jwks = response.json()

            # Update cache
            _jwks_cache = {"jwks": jwks, "fetched_at": time.time()}

            return jwks
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch JWKS: {str(e)}",
        )


def get_pem_certificate(token_header: dict, jwks: dict) -> str:
    """
    Extract PEM certificate from JWKS for the given token.

    Matches the token's 'kid' (key ID) header with keys in JWKS
    and constructs a PEM-formatted certificate from the X.509 certificate.

    Args:
        token_header: JWT header containing 'kid' field
        jwks: JWKS dictionary from Auth0

    Returns:
        PEM-formatted certificate string

    Raises:
        HTTPException: If matching key is not found or X.509 cert is missing
    """
    kid = token_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token header missing 'kid' field",
        )

    # Find matching key in JWKS
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            # Extract X.509 certificate (x5c field)
            x5c = key.get("x5c")
            if not x5c or len(x5c) == 0:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Key missing X.509 certificate",
                )

            # Construct PEM certificate
            cert = f"-----BEGIN CERTIFICATE-----\n{x5c[0]}\n-----END CERTIFICATE-----"
            return cert

    # No matching key found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=UNABLE_TO_FIND_KEY,
    )


def verify_audience(claims: dict, expected_audience: str) -> None:
    """
    Verify JWT audience claim.

    Matches Go's verifyAudience implementation (auth.go:169-185) which only
    handles the array format. The 'aud' claim is expected to be a list.

    Args:
        claims: JWT claims dictionary
        expected_audience: Expected audience value (from settings)

    Raises:
        HTTPException: If audience claim is missing or doesn't match
    """
    aud = claims.get("aud")

    if not aud:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=NO_AUDIENCE_CLAIM
        )

    # Go implementation only handles array format: claims["aud"].([]interface{})
    # Match this behavior exactly
    if not isinstance(aud, list):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_AUDIENCE
        )

    # Check if expected audience is in the list
    if expected_audience not in aud:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_AUDIENCE
        )


def verify_issuer(claims: dict, expected_issuer: str) -> None:
    """
    Verify JWT issuer claim.

    Args:
        claims: JWT claims dictionary
        expected_issuer: Expected issuer value (from settings)

    Raises:
        HTTPException: If issuer claim is missing or doesn't match
    """
    iss = claims.get("iss")

    if not iss:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=NO_ISSUER_CLAIM
        )

    if iss != expected_issuer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID_ISSUER
        )


# HTTPBearer scheme for extracting Authorization header
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    settings: Settings = Depends(get_settings),
) -> dict:
    """
    FastAPI dependency for JWT authentication.

    Validates JWT tokens from Auth0 using RS256 signature verification.
    Checks audience, issuer, expiration, and signature validity.

    This dependency should be used on protected routes:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            ...

    Args:
        request: FastAPI request object (to check HTTP method)
        credentials: Bearer token credentials from Authorization header
        settings: Application settings (injected dependency)

    Returns:
        Dictionary containing JWT claims (user context)

    Raises:
        HTTPException(401): If token is missing, invalid, or fails validation
    """
    # Skip authentication for OPTIONS requests (preflight)
    # Go's CheckJWT (auth.go:48-49) returns nil for OPTIONS, bypassing all validation.
    # Returning empty dict {} here allows the CORS middleware to handle the preflight
    # response without authentication. Route handlers should not be called for OPTIONS.
    if request.method == "OPTIONS":
        return {}

    # Check if Authorization header is present and properly formatted
    # Match Go's behavior at auth.go:52-60
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=NO_AUTHORIZATION_HEADER,
        )

    # Validate header format: "Bearer {token}"
    # HTTPBearer returns None if format is wrong, but we want the specific error message
    if not credentials:
        # Header exists but doesn't match "Bearer {token}" format
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=AUTH_HEADER_FORMAT_ERROR,
        )

    # Extract token from bearer scheme
    token = credentials.credentials

    try:
        # Decode token header without verification (to get 'kid' for JWKS lookup)
        unverified_header = jwt.get_unverified_header(token)

        # Check signing algorithm
        alg = unverified_header.get("alg")
        if alg != "RS256":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=TOKEN_MUST_USE_ALG,
            )

        # Fetch JWKS (cached)
        jwks = await fetch_jwks(settings.auth0_jwks_url)

        # Get PEM certificate for this token
        try:
            pem_cert = get_pem_certificate(unverified_header, jwks)
        except HTTPException:
            # Wrap PEM certificate errors to match Go's error at auth.go:116
            # Note: This intentionally discards specific error details (missing kid,
            # missing x5c, key not found) in favor of a generic message, matching Go's
            # behavior which returns a single "PEM Certificate failed" for all errors.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=PEM_CERTIFICATE_FAILED,
            )

        # Decode and verify token
        # python-jose handles signature verification, expiration, etc.
        claims = jwt.decode(
            token,
            pem_cert,
            algorithms=["RS256"],
            # Note: python-jose checks audience and issuer if provided here
            # but we verify them manually for consistency with Go code
        )

        # Verify audience (custom logic to handle array format)
        verify_audience(claims, settings.auth0_audience)

        # Verify issuer
        verify_issuer(claims, settings.auth0_issuer)

        # Token is valid, return claims
        return claims

    except JWTError:
        # JWT library errors (expired, invalid signature, malformed, etc.)
        # Match Go's error message at auth.go:69 (!parsedToken.Valid)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=TOKEN_INVALID,
        )
    except HTTPException:
        # Re-raise our custom HTTP exceptions
        raise
    except Exception:
        # Catch-all for unexpected errors
        # Use Go's general token validation failure message (auth.go:69)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=TOKEN_INVALID,
        )
