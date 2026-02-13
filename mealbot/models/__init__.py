"""Models subpackage for Mealbot domain objects and handlers.

Exports:
    Organization functions:
        - get_organizations: Fetch organizations for an admin
        - create_organization: Create a new organization
        - get_cross_match_trait: Get cross-match trait (used by pairing algorithm)
        - set_cross_match_trait: Set cross-match trait for an organization
        - org_bp: Flask Blueprint for organization routes
"""

from mealbot.models.organization import (
    org_bp,
    get_organizations,
    create_organization,
    get_cross_match_trait,
    set_cross_match_trait,
)

__all__ = [
    "org_bp",
    "get_organizations",
    "create_organization",
    "get_cross_match_trait",
    "set_cross_match_trait",
]
