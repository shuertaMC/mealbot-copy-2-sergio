"""Pydantic models for the Mealbot API.

This module defines Pydantic models for domain entities and request/response DTOs.
The models mirror the Go struct definitions from org.go and response.go.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class Organization(BaseModel):
    """Domain model for an organization.

    Corresponds to the Go Organization struct in org.go.
    """

    name: str
    admin: str
    cross_match_trait: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CreateOrganizationRequest(BaseModel):
    """Request body for creating a new organization.

    Corresponds to CreateOrganizationRequestBody in org.go.
    The 'org' field matches the JSON tag in the Go struct.
    """

    org: str


class SetCrossMatchTraitRequest(BaseModel):
    """Request body for setting a cross match trait.

    Corresponds to SetCrossMatchTraitRequestBody in org.go.
    The 'trait' field matches the JSON tag in the Go struct.
    """

    trait: str


class MessageResponse(BaseModel):
    """Standard message response for API operations.

    Corresponds to the Message struct in vendor/github.com/johnamadeo/server/response.go.
    Used for success and error messages.

    Note: The Go Message struct uses 'Message' (capital M) as the field name without
    a JSON tag, so the JSON output is {"Message": "..."}.
    """

    Message: str


class OrgsResponse(BaseModel):
    """Response model for GET /orgs endpoint.

    This matches the response format from GetOrganizationsHandler in org.go (line 61):
    resp := map[string][]string{"orgs": organizations}

    Returns a JSON object with a list of organization names.
    """

    orgs: List[str]
