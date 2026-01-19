"""
Pydantic schemas for Organization API requests and responses.

These models define the structure for organization-related HTTP requests
and responses, providing validation and serialization.
"""

from pydantic import BaseModel, Field, field_validator


class CreateOrganizationRequest(BaseModel):
    """
    Request body for creating a new organization.

    Matches Go's CreateOrganizationRequestBody (org.go:22-24).
    """

    org: str = Field(..., description="Organization name")

    @field_validator("org")
    @classmethod
    def validate_org_not_empty(cls, v: str) -> str:
        """Validate that organization name is not empty."""
        if not v or not v.strip():
            raise ValueError("Organization name cannot be an empty string")
        return v


class SetCrossMatchTraitRequest(BaseModel):
    """
    Request body for setting the cross-match trait of an organization.

    Matches Go's SetCrossMatchTraitRequestBody (org.go:26-28).
    """

    trait: str = Field(..., description="Cross-match trait name")


class OrganizationResponse(BaseModel):
    """
    Response model for a single organization.

    Attributes:
        name: Organization name
        admin: Administrator email address
        cross_match_trait: Optional cross-match trait for intelligent pairing
    """

    name: str
    admin: str
    cross_match_trait: str | None = None

    model_config = {"from_attributes": True}


class GetOrganizationsResponse(BaseModel):
    """
    Response model for listing organizations.

    Matches Go's response format (org.go:61).
    """

    orgs: list[str] = Field(
        default_factory=list, description="List of organization names"
    )


class SuccessMessageResponse(BaseModel):
    """
    Generic success message response.

    Used for POST endpoints that don't return specific data.
    """

    message: str
