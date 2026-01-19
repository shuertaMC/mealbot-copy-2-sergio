"""
Organization API endpoints.

This module provides HTTP handlers for organization management:
- GET /orgs?admin={email} - List organizations by admin
- POST /org?admin={email} - Create new organization
- POST /crossmatchtrait?org={name} - Set cross-match trait
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_query_param, raise_400, raise_500
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.organization import Organization
from app.schemas.organization import (
    CreateOrganizationRequest,
    GetOrganizationsResponse,
    SetCrossMatchTraitRequest,
    SuccessMessageResponse,
)

# Create router for organization endpoints
router = APIRouter()

# Logger for this module
logger = logging.getLogger(__name__)


@router.get(
    "/orgs",
    response_model=GetOrganizationsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get organizations by admin",
    description="Fetch all organizations managed by a specific admin",
)
async def get_organizations(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> GetOrganizationsResponse:
    """
    Get organizations by admin email.

    Implements GetOrganizationsHandler from org.go:32-69.

    Query Parameters:
        admin: Email of the organization administrator

    Returns:
        GetOrganizationsResponse with list of organization names

    Raises:
        HTTPException(400): If admin query parameter is missing
        HTTPException(500): If database query fails
    """
    function_name = "get_organizations"

    # Extract admin query parameter (raises 400 if missing)
    admin = get_query_param(request, "admin")

    try:
        # Query organizations by admin
        # SQL: SELECT name FROM organizations WHERE admin = $1
        stmt = select(Organization.name).where(Organization.admin == admin)
        result = await db.execute(stmt)
        organization_names = result.scalars().all()

        # Log success
        logger.info(
            "Successfully fetched organizations",
            extra={"function": function_name, "status": 200, "admin": admin},
        )

        # Return list of organization names
        return GetOrganizationsResponse(orgs=list(organization_names))

    except Exception as e:
        # Log and raise 500 Internal Server Error
        logger.error(
            f"Failed to fetch organizations: {str(e)}",
            extra={"function": function_name, "status": 500, "admin": admin},
        )
        raise_500(f"Database error: {str(e)}", function_name)


@router.post(
    "/org",
    response_model=SuccessMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
    description="Create a new organization with the specified name and admin",
)
async def create_organization(
    request: Request,
    body: CreateOrganizationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> SuccessMessageResponse:
    """
    Create a new organization.

    Implements CreateOrganizationHandler from org.go:71-124.

    Query Parameters:
        admin: Email of the organization administrator

    Request Body:
        CreateOrganizationRequest with org field

    Returns:
        Success message

    Raises:
        HTTPException(400): If admin query parameter is missing or org name is empty
        HTTPException(500): If database insert fails (e.g., duplicate organization)
    """
    function_name = "create_organization"

    # Extract admin query parameter (raises 400 if missing)
    admin = get_query_param(request, "admin")

    # Validate organization name (Pydantic validator already checks this, but be explicit)
    org_name = body.org.strip()
    if not org_name:
        raise_400("Organization name cannot be an empty string", function_name)

    try:
        # Insert new organization
        # SQL: INSERT INTO organizations (name, admin) VALUES ($1, $2)
        new_org = Organization(name=org_name, admin=admin)
        db.add(new_org)
        await db.commit()

        # Log success
        logger.info(
            "Successfully created organization",
            extra={
                "function": function_name,
                "status": 201,
                "org_name": org_name,
                "admin": admin,
            },
        )

        return SuccessMessageResponse(message="Successfully created new organization")

    except IntegrityError as e:
        # Handle duplicate key violation (organization already exists)
        await db.rollback()
        logger.error(
            f"Failed to create organization (duplicate): {str(e)}",
            extra={
                "function": function_name,
                "status": 500,
                "org_name": org_name,
                "admin": admin,
            },
        )
        raise_500(
            f"Organization '{org_name}' already exists or constraint violation",
            function_name,
        )

    except Exception as e:
        # Handle other database errors
        await db.rollback()
        logger.error(
            f"Failed to create organization: {str(e)}",
            extra={
                "function": function_name,
                "status": 500,
                "org_name": org_name,
                "admin": admin,
            },
        )
        raise_500(f"Database error: {str(e)}", function_name)


@router.post(
    "/crossmatchtrait",
    response_model=SuccessMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Set cross-match trait",
    description="Set or update the cross-match trait for an organization",
)
async def set_cross_match_trait(
    request: Request,
    body: SetCrossMatchTraitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[dict, Depends(get_current_user)],
) -> SuccessMessageResponse:
    """
    Set cross-match trait for an organization.

    Implements CrossMatchTraitHandler from org.go:126-162.

    Query Parameters:
        org: Organization name

    Request Body:
        SetCrossMatchTraitRequest with trait field

    Returns:
        Success message

    Raises:
        HTTPException(400): If org query parameter is missing
        HTTPException(500): If database update fails
    """
    function_name = "set_cross_match_trait"

    # Extract org query parameter (raises 400 if missing)
    org_name = get_query_param(request, "org")

    try:
        # Update organization's cross_match_trait
        # SQL: UPDATE organizations SET cross_match_trait = $1 WHERE name = $2
        stmt = (
            update(Organization)
            .where(Organization.name == org_name)
            .values(cross_match_trait=body.trait)
        )
        result = await db.execute(stmt)
        await db.commit()

        # Check if organization was found and updated
        if result.rowcount == 0:
            logger.warning(
                f"Organization not found: {org_name}",
                extra={
                    "function": function_name,
                    "status": 500,
                    "org_name": org_name,
                },
            )
            raise_500(f"Organization '{org_name}' not found", function_name)

        # Log success
        logger.info(
            "Successfully set cross match trait",
            extra={
                "function": function_name,
                "status": 201,
                "org_name": org_name,
                "trait": body.trait,
            },
        )

        return SuccessMessageResponse(message="Successfully set the cross match trait")

    except Exception as e:
        # Handle database errors
        await db.rollback()
        logger.error(
            f"Failed to set cross match trait: {str(e)}",
            extra={
                "function": function_name,
                "status": 500,
                "org_name": org_name,
            },
        )
        raise_500(f"Database error: {str(e)}", function_name)
