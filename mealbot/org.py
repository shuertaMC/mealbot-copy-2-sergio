"""
Organization routes and database functions.

Ported from org.go. Provides:
  - GET  /orgs             → get_organizations_handler
  - POST /org              → create_organization_handler
  - POST /crossmatchtrait  → cross_match_trait_handler

Database functions:
  - get_organizations(admin)
  - create_organization(name, admin)
  - get_cross_match_trait(orgname)   — exported, used by pairing algorithm
  - set_cross_match_trait(orgname, trait)
"""

import json
import logging

from flask import request

from . import db
from .utils import (
    err_to_bytes,
    get_query_param,
    log_and_write,
    log_and_write_err,
    log_and_write_status_bad_request,
    log_and_write_status_internal_server_error,
    str_to_bytes,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Database functions (from org.go)
# ---------------------------------------------------------------------------

def get_organizations(admin: str) -> list[str]:
    """
    Fetch all organization names managed by the given admin.

    Mirrors Go's getOrganizations: SELECT name FROM organizations WHERE admin = $1
    """
    rows = db.fetch_all(
        "SELECT name FROM organizations WHERE admin = %s",
        (admin,),
    )
    return [row["name"] for row in rows]


def create_organization(name: str, admin: str) -> None:
    """
    Create a new organization.

    Mirrors Go's createOrganization: validates name is non-empty, then INSERTs.

    Raises:
        ValueError: if name is empty.
    """
    if not name:
        raise ValueError("Organization name cannot be an empty string")

    db.execute(
        "INSERT INTO organizations (name, admin) VALUES (%s, %s)",
        (name, admin),
    )


def get_cross_match_trait(orgname: str) -> str:
    """
    Get the cross-match trait for an organization.

    Mirrors Go's GetCrossMatchTrait: returns empty string if trait is NULL.
    This function is exported (public) because it's used by the pairing
    algorithm in future milestones.
    """
    row = db.fetch_one(
        "SELECT cross_match_trait FROM organizations WHERE name = %s",
        (orgname,),
    )
    if row is None:
        return ""
    # Handle NULL cross_match_trait (Go uses sql.NullString)
    return row["cross_match_trait"] or ""


def set_cross_match_trait(orgname: str, cross_match_trait: str) -> None:
    """
    Set or update the cross-match trait for an organization.

    Mirrors Go's setCrossMatchTrait.
    """
    db.execute(
        "UPDATE organizations SET cross_match_trait = %s WHERE name = %s",
        (cross_match_trait, orgname),
    )


# ---------------------------------------------------------------------------
# HTTP Handlers (from org.go)
# ---------------------------------------------------------------------------

def get_organizations_handler():
    """
    HTTP handler for GET /orgs.

    Mirrors Go's GetOrganizationsHandler.
    Requires query parameter: admin
    Returns: {"orgs": ["org1", "org2", ...]}
    """
    function = "GetOrganizationsHandler"

    if request.method != "GET":
        return log_and_write_err(
            "Only GET requests are allowed at this route",
            405,
            function,
        )

    # Extract admin query parameter
    admin_values = request.args.getlist("admin")
    if not admin_values or len(admin_values) > 1:
        return log_and_write_err(
            "request query parameters must contain 'admin'",
            400,
            function,
        )
    admin = admin_values[0]

    try:
        organizations = get_organizations(admin)
    except Exception as e:
        return log_and_write_status_internal_server_error(e, function)

    resp = json.dumps({"orgs": organizations})
    return log_and_write(resp, 200, function)


def create_organization_handler():
    """
    HTTP handler for POST /org.

    Mirrors Go's CreateOrganizationHandler.
    Requires query parameter: admin
    Request body: {"org": "organization_name"}
    Returns: {"Message": "Successfully created new organization"}
    """
    function = "CreateOrganizationHandler"

    if request.method != "POST":
        return log_and_write_err(
            "Only POST requests are allowed at this route",
            405,
            function,
        )

    # Parse request body
    try:
        body = request.get_json(force=True)
    except Exception as e:
        return log_and_write_status_bad_request(e, function)

    if body is None:
        return log_and_write_status_bad_request(
            "Invalid request body", function
        )

    # Extract admin query parameter
    admin_values = request.args.getlist("admin")
    if not admin_values or len(admin_values) > 1:
        return log_and_write_err(
            "request query parameters must contain 'admin'",
            400,
            function,
        )
    admin = admin_values[0]

    org_name = body.get("org", "")
    logger.info("%s %s", org_name, admin)

    try:
        create_organization(org_name, admin)
    except Exception as e:
        return log_and_write_status_internal_server_error(e, function)

    return log_and_write(
        str_to_bytes("Successfully created new organization"),
        201,
        function,
    )


def cross_match_trait_handler():
    """
    HTTP handler for POST /crossmatchtrait.

    Mirrors Go's CrossMatchTraitHandler.
    Requires query parameter: org
    Request body: {"trait": "trait_name"}
    Returns: {"Message": "Successfully set the cross match trait"}
    """
    function = "CrossMatchTraitHandler"

    if request.method != "POST":
        return log_and_write_err(
            "Only POST requests are allowed at this route",
            405,
            function,
        )

    try:
        orgname = get_query_param("org")
    except ValueError as e:
        return log_and_write_status_bad_request(e, function)

    # Parse request body
    try:
        raw_data = request.get_data()
        if not raw_data:
            return log_and_write_err("Malformed body.", 400, function)
        body = json.loads(raw_data)
    except (json.JSONDecodeError, Exception):
        return log_and_write_err(
            "Request body is malformed", 400, function
        )

    trait = body.get("trait", "")

    try:
        set_cross_match_trait(orgname, trait)
    except Exception as e:
        from flask import Response
        return Response(
            err_to_bytes(e),
            status=500,
            mimetype="application/json",
        )

    return log_and_write(
        str_to_bytes("Successfully set the cross match trait"),
        201,
        function,
    )
