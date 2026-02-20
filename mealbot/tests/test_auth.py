"""Tests for auth.py JWT authentication middleware."""

import json
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from mealbot.auth import get_auth_handler


@pytest.fixture
def app():
    """Create a minimal Flask app with an auth-protected route."""
    app = Flask(__name__)

    @app.route("/protected", methods=["GET", "OPTIONS"])
    @get_auth_handler
    def protected():
        return "ok"

    return app


@pytest.fixture
def client(app):
    return app.test_client()


class TestAuthMiddleware:
    """Tests for auth middleware behavior."""

    def test_missing_auth_header_returns_401(self, client):
        """Requests without Authorization header should be rejected."""
        response = client.get("/protected")
        assert response.status_code == 401
        data = json.loads(response.data)
        assert "Message" in data

    def test_malformed_auth_header_returns_401(self, client):
        """Requests with malformed Authorization header should be rejected."""
        response = client.get(
            "/protected",
            headers={"Authorization": "NotBearer token"},
        )
        assert response.status_code == 401

    def test_bearer_only_returns_401(self, client):
        """Authorization header with only 'Bearer' (no token) should fail."""
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer"},
        )
        assert response.status_code == 401

    def test_options_passes_through(self, client):
        """OPTIONS requests should bypass auth (for CORS preflight)."""
        response = client.options("/protected")
        assert response.status_code == 200

    @patch("mealbot.auth.requests.get")
    @patch("mealbot.auth.jwt.get_unverified_header")
    @patch("mealbot.auth.load_pem_x509_certificate")
    @patch("mealbot.auth.jwt.decode")
    def test_valid_token_passes(
        self, mock_decode, mock_load_cert, mock_header, mock_requests_get, client
    ):
        """A properly formed and validated token should pass through."""
        # Mock unverified header
        mock_header.return_value = {"alg": "RS256", "kid": "test-kid"}

        # Mock JWKS response
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "keys": [
                {
                    "kid": "test-kid",
                    "x5c": ["TESTCERTIFICATEBASE64DATA"],
                }
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_resp

        # Mock X.509 certificate loading
        mock_cert_obj = MagicMock()
        mock_cert_obj.public_key.return_value = "mock-public-key"
        mock_load_cert.return_value = mock_cert_obj

        # Mock JWT decode
        mock_decode.return_value = {
            "aud": ["https://test-audience.com/"],
            "iss": "https://test-issuer.com/",
        }

        import os

        with patch.dict(
            os.environ,
            {
                "AUTH0_ISSUER": "https://test-issuer.com/",
                "AUTH0_AUDIENCE": "https://test-audience.com/",
                "AUTH0_JWKS_URL": "https://test.auth0.com/.well-known/jwks.json",
            },
        ):
            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer test.jwt.token"},
            )
            assert response.status_code == 200

    @patch("mealbot.auth.requests.get")
    @patch("mealbot.auth.jwt.get_unverified_header")
    @patch("mealbot.auth.load_pem_x509_certificate")
    @patch("mealbot.auth.jwt.decode")
    def test_invalid_audience_returns_401(
        self, mock_decode, mock_load_cert, mock_header, mock_requests_get, client
    ):
        """Token with wrong audience should be rejected."""
        mock_header.return_value = {"alg": "RS256", "kid": "test-kid"}

        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "keys": [{"kid": "test-kid", "x5c": ["TESTCERT"]}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_requests_get.return_value = mock_resp

        mock_cert_obj = MagicMock()
        mock_cert_obj.public_key.return_value = "mock-public-key"
        mock_load_cert.return_value = mock_cert_obj

        mock_decode.return_value = {
            "aud": ["https://wrong-audience.com/"],
            "iss": "https://test-issuer.com/",
        }

        import os

        with patch.dict(
            os.environ,
            {
                "AUTH0_ISSUER": "https://test-issuer.com/",
                "AUTH0_AUDIENCE": "https://test-audience.com/",
                "AUTH0_JWKS_URL": "https://test.auth0.com/.well-known/jwks.json",
            },
        ):
            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer test.jwt.token"},
            )
            assert response.status_code == 401
