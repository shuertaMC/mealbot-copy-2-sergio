"""Organization domain: HTTP handlers and database operations.

Ported from: org.go

Endpoints:
  GET  /orgs            - List organizations by admin email
  POST /org             - Create a new organization
  POST /crossmatchtrait - Set cross-match trait for an organization
"""

import json

from flask import Response, request

from .db import execute, fetch_all, fetch_one
from .logging_utils import (
    log_and_write,
    log_and_write_err,
    log_and_write_status_bad_request,
    log_and_write_status_internal_server_error,
    str_to_bytes,
)
from .utils import get_query_param


# ---------------------------------------------------------------------------
# Database functions
# ---------------------------------------------------------------------------


def get_organizations(admin: str) -> tuple[list[str], Exception | None]:
    """Fetch all organization names for a given admin.

    Mirrors Go's getOrganizations function.

    Args:
        admin: Admin email address.

    Returns:
        Tuple of (list of org names, None) on success, or ([], error).
    """
    try:
        rows = fetch_all(
            "SELECT name FROM organizations WHERE admin = $1",
            (admin,),
        )
        return [row["name"] for row in rows], None
    except Exception as e:
        return [], e


def create_organization(name: str, admin: str) -> Exception | None:
    """Create a new organization.

    Mirrors Go's createOrganization function.

    Args:
        name: Organization name (must not be empty).
        admin: Admin email address.

    Returns:
        None on success, or an error.
    """
    if not name:
        return ValueError("Organization name cannot be an empty string")

    try:
        execute(
            "INSERT INTO organizations (name, admin) VALUES ($1, $2)",
            (name, admin),
        )
        return None
    except Exception as e:
        return e


def get_cross_match_trait(orgname: str) -> tuple[str, Exception | None]:
    """Fetch the cross-match trait for an organization.

    Mirrors Go's GetCrossMatchTrait function. This function is exported
    (public) because it is consumed by the pairing algorithm in Milestone 4.

    Args:
        orgname: Organization name.

    Returns:
        Tuple of (trait string, None) on success, or ("", error).
        If the trait is NULL in the database, returns empty string.
    """
    try:
        row = fetch_one(
            "SELECT cross_match_trait FROM organizations WHERE name = $1",
            (orgname,),
        )
        if row is None:
            return "", None

        trait = row.get("cross_match_trait")
        return trait if trait is not None else "", None
    except Exception as e:
        return "", e


def set_cross_match_trait(
    orgname: str, cross_match_trait: str
) -> Exception | None:
    """Set the cross-match trait for an organization.

    Mirrors Go's setCrossMatchTrait function.

    Args:
        orgname: Organization name.
        cross_match_trait: The trait to set.

    Returns:
        None on success, or an error.
    """
    try:
        execute(
            "UPDATE organizations SET cross_match_trait = $1 WHERE name = $2",
            (cross_match_trait, orgname),
        )
        return None
    except Exception as e:
        return e


# ---------------------------------------------------------------------------
# HTTP Handlers
# ---------------------------------------------------------------------------


def get_organizations_handler() -> Response:
    """Handle GET /orgs - fetch organizations by admin.

    Mirrors Go's GetOrganizationsHandler.
    Expects query parameter: admin

    Returns JSON: {"orgs": ["org1", "org2", ...]}
    """
    function = "GetOrganizationsHandler"

    if request.method not in ("GET", ""):
        return log_and_write_err(
            ValueError("Only GET requests are allowed at this route"),
            405,
            function,
        )

    admin_values = request.args.getlist("admin")
    if len(admin_values) == 0 or len(admin_values) > 1:
        return log_and_write_err(
            ValueError("request query parameters must contain 'admin'"),
            400,
            function,
        )
    admin = admin_values[0]

    organizations, err = get_organizations(admin)
    if err is not None:
        return log_and_write_status_internal_server_error(err, function)

    resp = json.dumps({"orgs": organizations})
    return log_and_write(resp, 200, function)


def create_organization_handler() -> Response:
    """Handle POST /org - create a new organization.

    Mirrors Go's CreateOrganizationHandler.
    Expects query parameter: admin
    Expects JSON body: {"org": "organization_name"}

    Returns JSON: {"Message": "Successfully created new organization"}
    with status 201 on success.
    """
    function = "CreateOrganizationHandler"

    if request.method != "POST":
        return log_and_write_err(
            ValueError("Only POST requests are allowed at this route"),
            405,
            function,
        )

    try:
        body = request.get_json(force=True)
    except Exception as e:
        return log_and_write_status_bad_request(e, function)

    if body is None:
        return log_and_write_status_bad_request(
            ValueError("Request body is malformed"), function
        )

    org_name = body.get("org", "")

    admin_values = request.args.getlist("admin")
    if len(admin_values) == 0 or len(admin_values) > 1:
        return log_and_write_err(
            ValueError("request query parameters must contain 'admin'"),
            400,
            function,
        )
    admin = admin_values[0]

    err = create_organization(org_name, admin)
    if err is not None:
        return log_and_write_status_internal_server_error(err, function)

    return log_and_write(
        str_to_bytes("Successfully created new organization"),
        201,
        function,
    )


def cross_match_trait_handler() -> Response:
    """Handle POST /crossmatchtrait - set cross-match trait.

    Mirrors Go's CrossMatchTraitHandler.
    Expects query parameter: org
    Expects JSON body: {"trait": "trait_name"}

    Returns JSON: {"Message": "Successfully set the cross match trait"}
    with status 201 on success.
    """
    function = "CrossMatchTraitHandler"

    if request.method != "POST":
        return log_and_write_err(
            ValueError("Only POST requests are allowed at this route"),
            405,
            function,
        )

    orgname, err = get_query_param(request, "org")
    if err is not None:
        return log_and_write_status_bad_request(err, function)

    try:
        body = request.get_json(force=True)
    except Exception:
        return log_and_write_err(
            ValueError("Malformed body."), 400, function
        )

    if body is None:
        return log_and_write_err(
            ValueError("Request body is malformed"), 400, function
        )

    trait = body.get("trait", "")

    err = set_cross_match_trait(orgname, trait)
    if err is not None:
        return log_and_write_status_internal_server_error(err, function)

    return log_and_write(
        str_to_bytes("Successfully set the cross match trait"),
        201,
        function,
    )
