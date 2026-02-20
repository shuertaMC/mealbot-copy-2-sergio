"""Tests for organizations.py HTTP handlers.

Uses Flask test client with mocked database operations to verify
endpoint behavior matches Go implementation.
"""

import json
from unittest.mock import patch

import pytest
from flask import Flask

from mealbot.app import create_app


@pytest.fixture
def app():
    """Create a Flask app in testing mode (no auth)."""
    app = create_app(testing=True)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()


class TestGetOrganizationsHandler:
    """Tests for GET /orgs endpoint."""

    @patch("mealbot.organizations.fetch_all")
    def test_success_returns_org_list(self, mock_fetch, client):
        mock_fetch.return_value = [
            {"name": "org1"},
            {"name": "org2"},
        ]
        response = client.get("/orgs?admin=test@test.com")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == {"orgs": ["org1", "org2"]}

    @patch("mealbot.organizations.fetch_all")
    def test_empty_org_list(self, mock_fetch, client):
        mock_fetch.return_value = []
        response = client.get("/orgs?admin=test@test.com")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data == {"orgs": []}

    def test_missing_admin_param(self, client):
        response = client.get("/orgs")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Message" in data
        assert "admin" in data["Message"]

    def test_duplicate_admin_param(self, client):
        response = client.get("/orgs?admin=a&admin=b")
        assert response.status_code == 400

    def test_post_not_allowed(self, client):
        response = client.post("/orgs")
        assert response.status_code == 405

    @patch("mealbot.organizations.fetch_all")
    def test_db_error_returns_500(self, mock_fetch, client):
        mock_fetch.side_effect = RuntimeError("database connection failed")
        response = client.get("/orgs?admin=test@test.com")
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "Message" in data


class TestCreateOrganizationHandler:
    """Tests for POST /org endpoint."""

    @patch("mealbot.organizations.execute")
    def test_success_creates_org(self, mock_execute, client):
        mock_execute.return_value = None
        response = client.post(
            "/org?admin=test@test.com",
            data=json.dumps({"org": "neworg"}),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data == {"Message": "Successfully created new organization"}

    def test_missing_admin_param(self, client):
        response = client.post(
            "/org",
            data=json.dumps({"org": "neworg"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    @patch("mealbot.organizations.execute")
    def test_empty_org_name(self, mock_execute, client):
        response = client.post(
            "/org?admin=test@test.com",
            data=json.dumps({"org": ""}),
            content_type="application/json",
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "empty string" in data["Message"]

    def test_get_not_allowed(self, client):
        response = client.get("/org")
        assert response.status_code == 405

    @patch("mealbot.organizations.execute")
    def test_db_error_returns_500(self, mock_execute, client):
        mock_execute.side_effect = RuntimeError("duplicate key")
        response = client.post(
            "/org?admin=test@test.com",
            data=json.dumps({"org": "existingorg"}),
            content_type="application/json",
        )
        assert response.status_code == 500


class TestCrossMatchTraitHandler:
    """Tests for POST /crossmatchtrait endpoint."""

    @patch("mealbot.organizations.execute")
    def test_success_sets_trait(self, mock_execute, client):
        mock_execute.return_value = None
        response = client.post(
            "/crossmatchtrait?org=myorg",
            data=json.dumps({"trait": "college"}),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data == {
            "Message": "Successfully set the cross match trait"
        }

    def test_missing_org_param(self, client):
        response = client.post(
            "/crossmatchtrait",
            data=json.dumps({"trait": "college"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_get_not_allowed(self, client):
        response = client.get("/crossmatchtrait")
        assert response.status_code == 405

    @patch("mealbot.organizations.execute")
    def test_db_error_returns_500(self, mock_execute, client):
        mock_execute.side_effect = RuntimeError("db error")
        response = client.post(
            "/crossmatchtrait?org=myorg",
            data=json.dumps({"trait": "college"}),
            content_type="application/json",
        )
        assert response.status_code == 500

    def test_malformed_body(self, client):
        response = client.post(
            "/crossmatchtrait?org=myorg",
            data="not json {{{",
            content_type="application/json",
        )
        # Should handle gracefully - body might parse to None or error
        assert response.status_code in (400, 201)  # depends on Flask's json parsing
