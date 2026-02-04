"""Organization endpoints and database access functions for the Mealbot API.

This module implements the organization-related API endpoints, mirroring the behavior
of org.go from the Go implementation. It provides:
- GET /orgs - Retrieve organizations by admin email
- POST /org - Create a new organization
- POST /crossmatchtrait - Set the cross-match trait for an organization

Database functions follow the same SQL queries as the Go implementation.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, insert, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from mealbot.auth import get_current_user
from mealbot.database import get_db, organizations
from mealbot.models import (
    CreateOrganizationRequest,
    MessageResponse,
    OrgsResponse,
    SetCrossMatchTraitRequest,
)

logger = logging.getLogger(__name__)

# Create router for organization endpoints
router = APIRouter()


# Database access functions


def get_organizations_by_admin(db: Session, admin: str) -> List[str]:
    """
    Get all organization names for an admin.

    This mirrors getOrganizations in org.go (lines 165-191).
    SQL: SELECT name FROM organizations WHERE admin = $1

    Args:
        db: Database session.
        admin: The admin email to filter by.

    Returns:
        List of organization names.

    Raises:
        SQLAlchemyError: If the database query fails.
    """
    stmt = select(organizations.c.name).where(organizations.c.admin == admin)
    result = db.execute(stmt)
    return [row[0] for row in result.fetchall()]


def create_organization(db: Session, name: str, admin: str) -> None:
    """
    Create a new organization.

    This mirrors createOrganization in org.go (lines 194-214).
    SQL: INSERT INTO organizations (name, admin) VALUES ($1, $2)

    Args:
        db: Database session.
        name: The organization name (cannot be empty).
        admin: The admin email.

    Raises:
        ValueError: If the organization name is empty.
        SQLAlchemyError: If the database insert fails.
    """
    if name == "":
        raise ValueError("Organization name cannot be an empty string")

    stmt = insert(organizations).values(name=name, admin=admin)
    db.execute(stmt)
    db.commit()


def get_cross_match_trait(db: Session, orgname: str) -> Optional[str]:
    """
    Get the cross-match trait for an organization.

    This mirrors GetCrossMatchTrait in org.go (lines 217-248).
    SQL: SELECT cross_match_trait FROM organizations WHERE name = $1

    The cross_match_trait column can be NULL in the database.

    Args:
        db: Database session.
        orgname: The organization name.

    Returns:
        The cross-match trait value, or None if NULL or org not found.

    Raises:
        SQLAlchemyError: If the database query fails.
    """
    stmt = select(organizations.c.cross_match_trait).where(
        organizations.c.name == orgname
    )
    result = db.execute(stmt)
    row = result.fetchone()

    if row is None:
        return None

    # row[0] will be None if cross_match_trait is NULL
    return row[0] if row[0] else ""


def set_cross_match_trait(db: Session, orgname: str, cross_match_trait: str) -> None:
    """
    Set the cross-match trait for an organization.

    This mirrors setCrossMatchTrait in org.go (lines 250-266).
    SQL: UPDATE organizations SET cross_match_trait = $1 WHERE name = $2

    Args:
        db: Database session.
        orgname: The organization name.
        cross_match_trait: The cross-match trait value to set.

    Raises:
        SQLAlchemyError: If the database update fails.
    """
    stmt = (
        update(organizations)
        .where(organizations.c.name == orgname)
        .values(cross_match_trait=cross_match_trait)
    )
    db.execute(stmt)
    db.commit()


# Route handlers


@router.get("/orgs", response_model=OrgsResponse)
def get_orgs_handler(
    admin: str = Query(..., description="Admin email to filter organizations"),
    db: Session = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> OrgsResponse:
    """
    HTTP Handler for fetching all the organizations an admin manages.

    This mirrors GetOrganizationsHandler in org.go (lines 32-69).

    Query Parameters:
        admin: Required. The admin email to filter organizations.

    Returns:
        OrgsResponse with list of organization names.

    Raises:
        HTTPException 400: If admin parameter is missing.
        HTTPException 401: If not authenticated.
        HTTPException 500: If database error occurs.
    """
    function = "get_orgs_handler"

    try:
        org_list = get_organizations_by_admin(db, admin)
        logger.debug(
            "Retrieved %d organizations for admin %s",
            len(org_list),
            admin,
            extra={"function": function},
        )
        return OrgsResponse(orgs=org_list)
    except SQLAlchemyError as e:
        logger.error(
            "Database error: %s",
            str(e),
            extra={"function": function},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MessageResponse(Message=str(e)).model_dump(),
        )


@router.post("/org", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_org_handler(
    body: CreateOrganizationRequest,
    admin: str = Query(..., description="Admin email for the new organization"),
    db: Session = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> MessageResponse:
    """
    HTTP handler for creating a new organization.

    This mirrors CreateOrganizationHandler in org.go (lines 72-124).

    Query Parameters:
        admin: Required. The admin email for the organization.

    Request Body:
        {"org": "organization_name"}

    Returns:
        MessageResponse with success message (status 201).

    Raises:
        HTTPException 400: If admin parameter is missing or org name is empty.
        HTTPException 401: If not authenticated.
        HTTPException 500: If database error occurs (e.g., duplicate key).
    """
    function = "create_org_handler"

    # Log the request as Go does (org.go:110)
    logger.info(
        "Creating organization: %s, admin: %s",
        body.org,
        admin,
        extra={"function": function},
    )

    try:
        create_organization(db, body.org, admin)
        logger.debug(
            "Successfully created organization",
            extra={"function": function, "status": 201},
        )
        return MessageResponse(Message="Successfully created new organization")
    except ValueError as e:
        # Empty organization name
        logger.error(
            "Validation error: %s",
            str(e),
            extra={"function": function},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MessageResponse(Message=str(e)).model_dump(),
        )
    except IntegrityError as e:
        # Duplicate key or constraint violation
        db.rollback()
        logger.error(
            "Database integrity error: %s",
            str(e),
            extra={"function": function},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MessageResponse(Message=str(e)).model_dump(),
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            "Database error: %s",
            str(e),
            extra={"function": function},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MessageResponse(Message=str(e)).model_dump(),
        )


@router.post(
    "/crossmatchtrait",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def cross_match_trait_handler(
    body: SetCrossMatchTraitRequest,
    org: str = Query(..., description="Organization name"),
    db: Session = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> MessageResponse:
    """
    HTTP handler for setting the cross match trait for an organization.

    This mirrors CrossMatchTraitHandler in org.go (lines 127-162).

    Query Parameters:
        org: Required. The organization name.

    Request Body:
        {"trait": "trait_name"}

    Returns:
        MessageResponse with success message (status 201).

    Raises:
        HTTPException 400: If org parameter is missing.
        HTTPException 401: If not authenticated.
        HTTPException 500: If database error occurs.
    """
    function = "cross_match_trait_handler"

    try:
        set_cross_match_trait(db, org, body.trait)
        logger.debug(
            "Successfully set cross match trait for org %s",
            org,
            extra={"function": function, "status": 201},
        )
        return MessageResponse(Message="Successfully set the cross match trait")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(
            "Database error: %s",
            str(e),
            extra={"function": function},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=MessageResponse(Message=str(e)).model_dump(),
        )
