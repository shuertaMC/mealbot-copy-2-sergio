"""
Tests for mealbot.org module.

Tests the organization HTTP handlers and database functions using
mocked database calls.
"""

import json
from unittest.mock import patch

import pytest


class TestGetOrganizationsHandler:
    """Tests for GET /orgs endpoint."""

    def test_returns_401_without_auth(self, client):
        """Requests without JWT should be rejected."""
        response = client.get("/orgs?admin=test@test.com")
        assert response.status_code == 401

    @patch("mealbot.auth.check_jwt", return_value=None)
    @patch("mealbot.org.get_organizations", return_value=["org1", "org2"])
    def test_returns_organizations(self, mock_get_orgs, mock_auth, client):
        """Successful GET returns {"orgs": [...]}."""
        response = client.get("/orgs?admin=test@test.com")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == {"orgs": ["org1", "org2"]}

    @patch("mealbot.auth.check_jwt", return_value=None)
    def test_missing_admin_param(self, mock_auth, client):
        """Missing admin parameter returns 400."""
        response = client.get("/orgs")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "admin" in data["Message"]

    @patch("mealbot.auth.check_jwt", return_value=None)
    @patch("mealbot.org.get_organizations", return_value=[])
    def test_empty_organizations(self, mock_get_orgs, mock_auth, client):
        """No organizations returns empty list."""
        response = client.get("/orgs?admin=nobody@test.com")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == {"orgs": []}

    @patch("mealbot.auth.check_jwt", return_value=None)
    def test_post_method_not_allowed(self, mock_auth, client):
        """POST to /orgs returns 405."""
        response = client.post("/orgs")
        assert response.status_code == 405

    @patch("mealbot.auth.check_jwt", return_value=None)
    @patch("mealbot.org.get_organizations", side_effect=Exception("DB error"))
    def test_db_error_returns_500(self, mock_get_orgs, mock_auth, client):
        """Database errors return 500."""
        response = client.get("/orgs?admin=test@test.com")
        assert response.status_code == 500


class TestCreateOrganizationHandler:
    """Tests for POST /org endpoint."""

    def test_returns_401_without_auth(self, client):
        """Requests without JWT should be rejected."""
        response = client.post(
            "/org?admin=test@test.com",
            data=json.dumps({"org": "test_org"}),
            content_type="application/json",
        )
        assert response.status_code == 401

    @patch("mealbot.auth.check_jwt", return_value=None)
    @patch("mealbot.org.create_organization")
    def test_creates_organization(self, mock_create, mock_auth, client):
        """Successful POST returns 201 with success message."""
        response = client.post(
            "/org?admin=admin@test.com",
            data=json.dumps({"org": "new_org"}),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data == {"Message": "Successfully created new organization"}
        mock_create.assert_called_once_with("new_org", "admin@test.com")

    @patch("mealbot.auth.check_jwt", return_value=None)
    def test_missing_admin_param(self, mock_auth, client):
        """Missing admin parameter returns 400."""
        response = client.post(
            "/org",
            data=json.dumps({"org": "new_org"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    @patch("mealbot.auth.check_jwt", return_value=None)
    def test_get_method_not_allowed(self, mock_auth, client):
        """GET to /org is rejected (Flask routing handles method restriction)."""
        response = client.get("/org")
        # Flask returns 405 for known routes with wrong method, but since
        # static file serving is at root, GET requests may get 404 instead.
        assert response.status_code in (404, 405)

    @patch("mealbot.auth.check_jwt", return_value=None)
    @patch("mealbot.org.create_organization", side_effect=Exception("duplicate key"))
    def test_duplicate_org_returns_500(self, mock_create, mock_auth, client):
        """Duplicate organization name returns 500."""
        response = client.post(
            "/org?admin=admin@test.com",
            data=json.dumps({"org": "existing_org"}),
            content_type="application/json",
        )
        assert response.status_code == 500


class TestCrossMatchTraitHandler:
    """Tests for POST /crossmatchtrait endpoint."""

    def test_returns_401_without_auth(self, client):
        """Requests without JWT should be rejected."""
        response = client.post(
            "/crossmatchtrait?org=test_org",
            data=json.dumps({"trait": "College"}),
            content_type="application/json",
        )
        assert response.status_code == 401

    @patch("mealbot.auth.check_jwt", return_value=None)
    @patch("mealbot.org.set_cross_match_trait")
    def test_sets_cross_match_trait(self, mock_set, mock_auth, client):
        """Successful POST returns 201 with success message."""
        response = client.post(
            "/crossmatchtrait?org=test_org",
            data=json.dumps({"trait": "College"}),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data == {"Message": "Successfully set the cross match trait"}
        mock_set.assert_called_once_with("test_org", "College")

    @patch("mealbot.auth.check_jwt", return_value=None)
    def test_missing_org_param(self, mock_auth, client):
        """Missing org parameter returns 400."""
        response = client.post(
            "/crossmatchtrait",
            data=json.dumps({"trait": "College"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    @patch("mealbot.auth.check_jwt", return_value=None)
    def test_malformed_body(self, mock_auth, client):
        """Malformed JSON body returns 400."""
        response = client.post(
            "/crossmatchtrait?org=test_org",
            data="not json",
            content_type="text/plain",
        )
        assert response.status_code == 400

    @patch("mealbot.auth.check_jwt", return_value=None)
    def test_empty_body(self, mock_auth, client):
        """Empty request body returns 400."""
        response = client.post(
            "/crossmatchtrait?org=test_org",
            data="",
            content_type="application/json",
        )
        assert response.status_code == 400

    @patch("mealbot.auth.check_jwt", return_value=None)
    def test_get_method_not_allowed(self, mock_auth, client):
        """GET to /crossmatchtrait is rejected (Flask routing handles method restriction)."""
        response = client.get("/crossmatchtrait")
        # Flask returns 405 for known routes with wrong method, but since
        # static file serving is at root, GET requests may get 404 instead.
        assert response.status_code in (404, 405)

    @patch("mealbot.auth.check_jwt", return_value=None)
    @patch("mealbot.org.set_cross_match_trait", side_effect=Exception("DB error"))
    def test_db_error_returns_500(self, mock_set, mock_auth, client):
        """Database errors return 500."""
        response = client.post(
            "/crossmatchtrait?org=test_org",
            data=json.dumps({"trait": "College"}),
            content_type="application/json",
        )
        assert response.status_code == 500
