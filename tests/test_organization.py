"""API tests for Organization endpoints.

These tests verify the Organization API endpoints match the Go implementation
behavior including response formats, status codes, and error handling.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from mealbot.app import create_app


@pytest.fixture
def app():
    """Create a Flask application for testing."""
    app = create_app({"TESTING": True})
    return app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


class TestGetOrganizationsEndpoint:
    """Tests for GET /orgs endpoint."""

    def test_get_orgs_returns_list(self, client):
        """Test that GET /orgs returns a list of organization names."""
        with patch("mealbot.models.organization.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [("org1",), ("org2",), ("org3",)]
            mock_conn.return_value.__enter__ = MagicMock(return_value=mock_conn.return_value)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            mock_conn.return_value.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

            response = client.get("/orgs?admin=test@example.com")

            assert response.status_code == 200
            data = response.get_json()
            assert "orgs" in data
            assert data["orgs"] == ["org1", "org2", "org3"]

    def test_get_orgs_empty_list(self, client):
        """Test that GET /orgs returns empty list when no organizations exist."""
        with patch("mealbot.models.organization.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = []
            mock_conn.return_value.__enter__ = MagicMock(return_value=mock_conn.return_value)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            mock_conn.return_value.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

            response = client.get("/orgs?admin=test@example.com")

            assert response.status_code == 200
            data = response.get_json()
            assert data == {"orgs": []}

    def test_get_orgs_missing_admin_param_returns_400(self, client):
        """Test that GET /orgs without admin parameter returns 400."""
        response = client.get("/orgs")

        assert response.status_code == 400
        data = response.get_json()
        assert "message" in data
        assert "admin" in data["message"].lower()

    def test_get_orgs_multiple_admin_params_returns_400(self, client):
        """Test that GET /orgs with multiple admin parameters returns 400."""
        response = client.get("/orgs?admin=one@example.com&admin=two@example.com")

        assert response.status_code == 400
        data = response.get_json()
        assert "message" in data

    def test_get_orgs_post_method_returns_405(self, client):
        """Test that POST to /orgs returns 405 Method Not Allowed."""
        response = client.post("/orgs?admin=test@example.com")

        assert response.status_code == 405

    def test_get_orgs_database_error_returns_500(self, client):
        """Test that GET /orgs returns 500 on database error."""
        with patch("mealbot.models.organization.get_connection") as mock_conn:
            mock_conn.side_effect = Exception("Database connection failed")

            response = client.get("/orgs?admin=test@example.com")

            assert response.status_code == 500
            data = response.get_json()
            assert "message" in data


class TestCreateOrganizationEndpoint:
    """Tests for POST /org endpoint."""

    def test_create_org_success(self, client):
        """Test that POST /org creates organization and returns 201."""
        with patch("mealbot.models.organization.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_conn.return_value.__enter__ = MagicMock(return_value=mock_conn.return_value)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            mock_conn.return_value.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

            response = client.post(
                "/org?admin=test@example.com",
                data=json.dumps({"org": "new_org"}),
                content_type="application/json",
            )

            assert response.status_code == 201
            data = response.get_json()
            assert "message" in data
            assert "success" in data["message"].lower()

    def test_create_org_missing_admin_param_returns_400(self, client):
        """Test that POST /org without admin parameter returns 400."""
        response = client.post(
            "/org",
            data=json.dumps({"org": "new_org"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "message" in data
        assert "admin" in data["message"].lower()

    def test_create_org_empty_name_returns_500(self, client):
        """Test that POST /org with empty org name returns 500."""
        response = client.post(
            "/org?admin=test@example.com",
            data=json.dumps({"org": ""}),
            content_type="application/json",
        )

        assert response.status_code == 500
        data = response.get_json()
        assert "message" in data
        assert "empty" in data["message"].lower()

    def test_create_org_malformed_json_returns_400(self, client):
        """Test that POST /org with malformed JSON returns 400."""
        response = client.post(
            "/org?admin=test@example.com",
            data="not valid json",
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "message" in data

    def test_create_org_get_method_returns_405(self, client):
        """Test that GET to /org returns 405 Method Not Allowed."""
        response = client.get("/org?admin=test@example.com")

        assert response.status_code == 405

    def test_create_org_database_error_returns_500(self, client):
        """Test that POST /org returns 500 on database error (e.g., duplicate key)."""
        with patch("mealbot.models.organization.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.execute.side_effect = Exception(
                "duplicate key value violates unique constraint"
            )
            mock_conn.return_value.__enter__ = MagicMock(return_value=mock_conn.return_value)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            mock_conn.return_value.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

            response = client.post(
                "/org?admin=test@example.com",
                data=json.dumps({"org": "existing_org"}),
                content_type="application/json",
            )

            assert response.status_code == 500
            data = response.get_json()
            assert "message" in data


class TestCrossMatchTraitEndpoint:
    """Tests for POST /crossmatchtrait endpoint."""

    def test_set_cross_match_trait_success(self, client):
        """Test that POST /crossmatchtrait sets trait and returns 201."""
        with patch("mealbot.models.organization.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_conn.return_value.__enter__ = MagicMock(return_value=mock_conn.return_value)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            mock_conn.return_value.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

            response = client.post(
                "/crossmatchtrait?org=test_org",
                data=json.dumps({"trait": "department"}),
                content_type="application/json",
            )

            assert response.status_code == 201
            data = response.get_json()
            assert "message" in data
            assert "success" in data["message"].lower()

    def test_set_cross_match_trait_missing_org_param_returns_400(self, client):
        """Test that POST /crossmatchtrait without org parameter returns 400."""
        response = client.post(
            "/crossmatchtrait",
            data=json.dumps({"trait": "department"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "message" in data

    def test_set_cross_match_trait_malformed_json_returns_400(self, client):
        """Test that POST /crossmatchtrait with malformed JSON returns 400."""
        response = client.post(
            "/crossmatchtrait?org=test_org",
            data="not valid json",
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "message" in data
        assert "malformed" in data["message"].lower()

    def test_set_cross_match_trait_missing_trait_in_body_returns_400(self, client):
        """Test that POST /crossmatchtrait without trait in body returns 400."""
        response = client.post(
            "/crossmatchtrait?org=test_org",
            data=json.dumps({"other": "value"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "message" in data
        assert "malformed" in data["message"].lower()

    def test_set_cross_match_trait_get_method_returns_405(self, client):
        """Test that GET to /crossmatchtrait returns 405 Method Not Allowed."""
        response = client.get("/crossmatchtrait?org=test_org")

        assert response.status_code == 405

    def test_set_cross_match_trait_database_error_returns_500(self, client):
        """Test that POST /crossmatchtrait returns 500 on database error."""
        with patch("mealbot.models.organization.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.execute.side_effect = Exception("Database error")
            mock_conn.return_value.__enter__ = MagicMock(return_value=mock_conn.return_value)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            mock_conn.return_value.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

            response = client.post(
                "/crossmatchtrait?org=test_org",
                data=json.dumps({"trait": "department"}),
                content_type="application/json",
            )

            assert response.status_code == 500
            data = response.get_json()
            assert "message" in data


class TestGetCrossMatchTraitFunction:
    """Tests for the get_cross_match_trait database function."""

    def test_get_cross_match_trait_returns_trait(self):
        """Test that get_cross_match_trait returns the trait value."""
        from mealbot.models.organization import get_cross_match_trait

        with patch("mealbot.models.organization.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = ("department",)
            mock_conn.return_value.__enter__ = MagicMock(return_value=mock_conn.return_value)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            mock_conn.return_value.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

            result = get_cross_match_trait("test_org")

            assert result == "department"

    def test_get_cross_match_trait_returns_empty_for_null(self):
        """Test that get_cross_match_trait returns empty string for NULL value."""
        from mealbot.models.organization import get_cross_match_trait

        with patch("mealbot.models.organization.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (None,)
            mock_conn.return_value.__enter__ = MagicMock(return_value=mock_conn.return_value)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            mock_conn.return_value.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

            result = get_cross_match_trait("test_org")

            # Go implementation returns empty string for NULL
            assert result == ""

    def test_get_cross_match_trait_returns_none_for_nonexistent_org(self):
        """Test that get_cross_match_trait returns None for non-existent organization."""
        from mealbot.models.organization import get_cross_match_trait

        with patch("mealbot.models.organization.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_conn.return_value.__enter__ = MagicMock(return_value=mock_conn.return_value)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            mock_conn.return_value.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

            result = get_cross_match_trait("nonexistent_org")

            assert result is None


class TestResponseFormat:
    """Tests to verify response format matches Go implementation."""

    def test_error_response_format(self, client):
        """Test that error responses use {"message": "error text"} format."""
        response = client.get("/orgs")

        assert response.status_code == 400
        data = response.get_json()
        assert "message" in data
        assert isinstance(data["message"], str)

    def test_success_message_format(self, client):
        """Test that success messages use {"message": "text"} format."""
        with patch("mealbot.models.organization.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_conn.return_value.__enter__ = MagicMock(return_value=mock_conn.return_value)
            mock_conn.return_value.__exit__ = MagicMock(return_value=False)
            mock_conn.return_value.cursor.return_value.__enter__ = MagicMock(
                return_value=mock_cursor
            )
            mock_conn.return_value.cursor.return_value.__exit__ = MagicMock(return_value=False)

            response = client.post(
                "/org?admin=test@example.com",
                data=json.dumps({"org": "new_org"}),
                content_type="application/json",
            )

            assert response.status_code == 201
            data = response.get_json()
            assert "message" in data
            assert isinstance(data["message"], str)
