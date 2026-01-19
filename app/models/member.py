"""
Member SQLAlchemy model.

Members belong to organizations and participate in meal pairings.
This model stores member information, metadata, pairing history, and active status.
"""

from sqlalchemy import Boolean, Column, ForeignKey, String, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB

from app.database import Base


class Member(Base):
    """
    Member model representing a participant in meal pairings.

    Members are scoped to organizations and identified by their email address.
    The model tracks pairing history using JSONB fields for flexible data storage.

    Attributes:
        organization: Foreign key to the organization this member belongs to
        email: Member's email address (part of composite primary key)
        name: Member's display name
        metadata_: Optional JSONB field for flexible metadata storage (maps to 'metadata' column)
        pair_counts: JSONB field tracking pairing frequency with other members
        active: Boolean indicating if member is currently active for pairing
    """

    __tablename__ = "members"

    organization = Column(
        String,
        ForeignKey("organizations.name"),
        primary_key=True,
        nullable=False,
    )
    """Organization name (foreign key, part of composite primary key)"""

    email = Column(
        String,
        primary_key=True,
        nullable=False,
    )
    """Member email address (part of composite primary key)"""

    name = Column(
        String,
        nullable=False,
    )
    """Member display name"""

    metadata_ = Column(
        "metadata",  # Database column name
        JSONB,
        nullable=True,
    )
    """
    Optional JSONB metadata for flexible data storage.
    Can store arbitrary member attributes (e.g., team, location, preferences).
    Note: Mapped to 'metadata_' in Python to avoid conflict with SQLAlchemy's reserved 'metadata' attribute.
    """

    pair_counts = Column(
        JSONB,
        nullable=False,
    )
    """
    JSONB field tracking pairing history.
    Maps member email -> count of times paired with that member.
    Used by pairing algorithm to avoid recent repeats.
    Example: {"alice@example.com": 2, "bob@example.com": 1}
    """

    active = Column(
        Boolean,
        nullable=False,
    )
    """Whether this member is currently active for pairing"""

    # Add check constraints to match schema.sql
    __table_args__ = (
        CheckConstraint("length(email) > 0", name="members_email_check"),
        CheckConstraint("length(name) > 0", name="members_name_check"),
    )

    def __repr__(self) -> str:
        """Return string representation of Member for debugging."""
        return f"<Member(org={self.organization!r}, email={self.email!r}, name={self.name!r}, active={self.active})>"
