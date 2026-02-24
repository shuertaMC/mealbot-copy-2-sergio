"""
Tests for mealbot.auth module.

Tests JWT authentication middleware behavior including:
- OPTIONS preflight bypass
- Missing/malformed Authorization headers
- Token validation errors
- Audience and issuer verification
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from mealbot.auth import (
    AUDIENCE,
    ISSUER,
    check_jwt,
    get_pem_certificate,
    require_jwt,
    verify_audience,
)


class TestVerifyAudience:
    """Tests for verify_audience function."""

    def test_valid_audience_in_list(self):
        """Audience found in list should not raise."""
        claims = {"aud": [AUDIENCE, "other"]}
        verify_audience(claims, AUDIENCE)  # Should not raise

    def test_valid_audience_as_string(self):
        """Audience as string should not raise if it matches."""
        claims = {"aud": AUDIENCE}
        verify_audience(claims, AUDIENCE)  # Should not raise

    def test_missing_audience_raises(self):
        """No aud claim should raise ValueError."""
        claims = {}
        with pytest.raises(ValueError, match="No audience claim"):
            verify_audience(claims, AUDIENCE)

    def test_invalid_audience_raises(self):
        """Wrong audience should raise ValueError."""
        claims = {"aud": ["wrong-audience"]}
        with pytest.raises(ValueError, match="Invalid audience"):
            verify_audience(claims, AUDIENCE)

    def test_invalid_audience_string_raises(self):
        """Wrong audience string should raise ValueError."""
        claims = {"aud": "wrong-audience"}
        with pytest.raises(ValueError, match="Invalid audience"):
            verify_audience(claims, AUDIENCE)


class TestCheckJWT:
    """Tests for check_jwt function."""

    def test_options_request_passes(self, app):
        """OPTIONS requests should bypass JWT validation."""
        with app.test_request_context("/orgs", method="OPTIONS"):
            result = check_jwt()
            assert result is None

    def test_missing_auth_header_raises(self, app):
        """Request without Authorization header should raise."""
        with app.test_request_context("/orgs", method="GET"):
            with pytest.raises(ValueError, match="No authorization header"):
                check_jwt()

    def test_malformed_auth_header_raises(self, app):
        """Malformed Authorization header should raise."""
        with app.test_request_context(
            "/orgs",
            method="GET",
            headers={"Authorization": "InvalidFormat"},
        ):
            with pytest.raises(ValueError, match="Authorization header format"):
                check_jwt()

    def test_non_bearer_auth_raises(self, app):
        """Non-Bearer token type should raise."""
        with app.test_request_context(
            "/orgs",
            method="GET",
            headers={"Authorization": "Basic abc123"},
        ):
            with pytest.raises(ValueError, match="Authorization header format"):
                check_jwt()

    def test_invalid_token_raises(self, app):
        """Invalid JWT token should raise."""
        with app.test_request_context(
            "/orgs",
            method="GET",
            headers={"Authorization": "Bearer invalid.token.here"},
        ):
            with pytest.raises(ValueError):
                check_jwt()


class TestRequireJWTDecorator:
    """Tests for @require_jwt decorator behavior."""

    def test_unauthenticated_request_returns_401(self, client):
        """Request without JWT to protected route returns 401."""
        response = client.get("/orgs?admin=test@test.com")
        assert response.status_code == 401

    def test_options_request_passes_through(self, client):
        """OPTIONS request to protected route should succeed (CORS preflight)."""
        # Proper CORS preflight requires Access-Control-Request-Method header
        response = client.options(
            "/orgs",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # OPTIONS should get CORS response, not 401
        assert response.status_code == 200


class TestGetPEMCertificate:
    """Tests for get_pem_certificate function."""

    @patch("mealbot.auth.requests.get")
    def test_matching_kid_returns_cert(self, mock_get):
        """Matching kid should return PEM certificate."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "keys": [
                {
                    "kid": "test-kid",
                    "x5c": ["MIIC+zCCAeOgAwIBAgI..."],
                    "kty": "RSA",
                    "use": "sig",
                    "n": "test-n",
                    "e": "AQAB",
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        cert = get_pem_certificate({"kid": "test-kid"})
        assert cert.startswith("-----BEGIN CERTIFICATE-----")
        assert cert.endswith("-----END CERTIFICATE-----")
        assert "MIIC+zCCAeOgAwIBAgI..." in cert

    @patch("mealbot.auth.requests.get")
    def test_no_matching_kid_raises(self, mock_get):
        """No matching kid should raise ValueError."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "keys": [
                {"kid": "other-kid", "x5c": ["cert"]}
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Unable to find appropriate key"):
            get_pem_certificate({"kid": "test-kid"})
