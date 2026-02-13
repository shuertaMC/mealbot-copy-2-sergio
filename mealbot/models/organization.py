"""Organization management handlers and database queries.

This module provides HTTP handlers and database query functions for organization
management, mirroring the Go implementation in org.go.

Endpoints:
    GET /orgs - Fetch organizations for an admin user
    POST /org - Create a new organization
    POST /crossmatchtrait - Set cross-match trait for an organization
"""

import json
import logging
from typing import Optional

from flask import Blueprint, request, Response

from mealbot.db import get_connection
from mealbot.utils import (
    get_query_param,
    log_and_write,
    log_and_write_err,
    log_and_write_status_bad_request,
    log_and_write_status_internal_server_error,
    str_to_bytes,
    QueryParamError,
)

logger = logging.getLogger(__name__)

# Create a Blueprint for organization routes
org_bp = Blueprint("organization", __name__)


# =============================================================================
# HTTP Handlers
# =============================================================================


@org_bp.route("/orgs", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def get_organizations_handler() -> Response:
    """HTTP Handler for fetching all the organizations an admin manages.

    Mirrors the Go GetOrganizationsHandler function.

    Query Parameters:
        admin: The admin email to filter organizations by.

    Returns:
        JSON response with {"orgs": [list of organization names]}.
    """
    function = "get_organizations_handler"

    # Validate method - matches Go behavior which allows GET or empty method
    if request.method != "GET" and request.method != "":
        return log_and_write_err(
            Exception("Only GET requests are allowed at this route"),
            405,
            function,
        )

    # Get required 'admin' query parameter
    queries = request.args.getlist("admin")
    if not queries or len(queries) > 1:
        return log_and_write_err(
            Exception("request query parameters must contain 'admin'"),
            400,
            function,
        )

    admin = queries[0]

    try:
        organizations = get_organizations(admin)
    except Exception as err:
        return log_and_write_status_internal_server_error(err, function)

    resp = {"orgs": organizations}
    return log_and_write(resp, 200, function)


@org_bp.route("/org", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def create_organization_handler() -> Response:
    """HTTP handler for creating a new organization.

    Mirrors the Go CreateOrganizationHandler function.

    Query Parameters:
        admin: The admin email for the new organization.

    Request Body:
        {"org": "organization_name"}

    Returns:
        JSON response with success message and status 201.
    """
    function = "create_organization_handler"

    # Validate method - Flask handles this via route definition, but we check explicitly
    if request.method != "POST":
        return log_and_write_err(
            Exception("Only POST requests are allowed at this route"),
            405,
            function,
        )

    # Parse request body
    try:
        body_bytes = request.get_data()
        body = json.loads(body_bytes)
    except Exception as err:
        return log_and_write_status_bad_request(err, function)

    # Get required 'admin' query parameter
    queries = request.args.getlist("admin")
    if not queries or len(queries) > 1:
        return log_and_write_err(
            Exception("request query parameters must contain 'admin'"),
            400,
            function,
        )
    admin = queries[0]

    org_name = body.get("org", "")
    print(org_name, admin)

    try:
        create_organization(org_name, admin)
    except Exception as err:
        return log_and_write_status_internal_server_error(err, function)

    return log_and_write(
        str_to_bytes("Successfully created new organization"),
        201,
        function,
    )


@org_bp.route("/crossmatchtrait", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def cross_match_trait_handler() -> Response:
    """HTTP handler for setting a cross match trait for an organization.

    Mirrors the Go CrossMatchTraitHandler function.

    Query Parameters:
        org: The organization name.

    Request Body:
        {"trait": "trait_name"}

    Returns:
        JSON response with success message and status 201.
    """
    function = "cross_match_trait_handler"

    # Validate method - Flask handles this via route definition
    if request.method != "POST":
        return log_and_write_err(
            Exception("Only POST requests are allowed at this route"),
            405,
            function,
        )

    # Get required 'org' query parameter
    try:
        orgname = get_query_param("org")
    except QueryParamError as err:
        return log_and_write_status_bad_request(err, function)

    # Parse request body
    try:
        body_bytes = request.get_data()
        body = json.loads(body_bytes)
    except Exception:
        return log_and_write_err(
            Exception("Malformed body."),
            400,
            function,
        )

    trait = body.get("trait")
    if trait is None:
        return log_and_write_err(
            Exception("Request body is malformed"),
            400,
            function,
        )

    try:
        set_cross_match_trait(orgname, trait)
    except Exception as err:
        # Go implementation: w.WriteHeader(http.StatusInternalServerError); w.Write(server.ErrToBytes(err))
        return Response(
            json.dumps({"message": str(err)}).encode("utf-8"),
            status=500,
            mimetype="application/json",
        )

    return log_and_write(
        str_to_bytes("Successfully set the cross match trait"),
        201,
        function,
    )


# =============================================================================
# Database Query Functions
# =============================================================================


def get_organizations(admin: str) -> list[str]:
    """Fetch all organizations for a given admin.

    Mirrors the Go getOrganizations function.

    Args:
        admin: The admin email to filter by.

    Returns:
        List of organization names managed by the admin.

    Raises:
        Exception: If there's a database error.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name FROM organizations WHERE admin = %s",
                (admin,),
            )
            rows = cur.fetchall()

        organizations = [row[0] for row in rows]
        return organizations
    finally:
        conn.close()


def create_organization(name: str, admin: str) -> None:
    """Create a new organization.

    Mirrors the Go createOrganization function.

    Args:
        name: The organization name.
        admin: The admin email for the organization.

    Raises:
        Exception: If the organization name is empty or there's a database error.
    """
    if name == "":
        raise Exception("Organization name cannot be an empty string")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO organizations (name, admin) VALUES (%s, %s)",
                (name, admin),
            )
        conn.commit()
    finally:
        conn.close()


def get_cross_match_trait(orgname: str) -> Optional[str]:
    """Get the cross-match trait for an organization.

    Mirrors the Go GetCrossMatchTrait function. This function is exported
    for use by the pairing algorithm in Milestone 5.

    Args:
        orgname: The organization name.

    Returns:
        The cross-match trait string, or None if not set.

    Raises:
        Exception: If there's a database error.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT cross_match_trait FROM organizations WHERE name = %s",
                (orgname,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        # Handle nullable column - psycopg returns None for SQL NULL
        cross_match_trait = row[0]
        if cross_match_trait is None:
            return ""

        return cross_match_trait
    finally:
        conn.close()


def set_cross_match_trait(orgname: str, cross_match_trait: str) -> None:
    """Set the cross-match trait for an organization.

    Mirrors the Go setCrossMatchTrait function.

    Args:
        orgname: The organization name.
        cross_match_trait: The trait to set.

    Raises:
        Exception: If there's a database error.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE organizations SET cross_match_trait = %s WHERE name = %s",
                (cross_match_trait, orgname),
            )
        conn.commit()
    finally:
        conn.close()
