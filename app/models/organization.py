"""
Organization SQLAlchemy model.

Organizations represent multi-tenant entities in the Mealbot application.
Each organization has an admin and optional cross-match trait for intelligent pairing.
"""

from sqlalchemy import Column, String, CheckConstraint

from app.database import Base


class Organization(Base):
    """
    Organization model representing a tenant in the multi-tenant system.

    An organization groups members together for meal pairing. Each organization
    has an admin who can manage the organization's settings and members.

    Attributes:
        name: Unique organization name (primary key)
        admin: Email of the organization administrator
        cross_match_trait: Optional trait name used for intelligent cross-group pairing
    """

    __tablename__ = "organizations"

    name = Column(
        String,
        primary_key=True,
        nullable=False,
    )
    """Organization name (unique identifier)"""

    admin = Column(
        String,
        nullable=False,
    )
    """Administrator email address"""

    cross_match_trait = Column(
        String,
        nullable=True,
    )
    """Optional trait name for cross-match pairing (e.g., 'team', 'department')"""

    # Add check constraints to match schema.sql
    __table_args__ = (
        CheckConstraint("length(admin) > 0", name="organizations_admin_check"),
    )

    def __repr__(self) -> str:
        """Return string representation of Organization for debugging."""
        return f"<Organization(name={self.name!r}, admin={self.admin!r})>"
