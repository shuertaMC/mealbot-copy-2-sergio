"""
Round SQLAlchemy model.

Rounds represent scheduled pairing events within an organization.
Each round has a scheduled date and tracks whether pairing has been completed.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    CheckConstraint,
)

from app.database import Base


class Round(Base):
    """
    Round model representing a scheduled pairing event.

    Rounds are scoped to organizations and identified by a sequential ID.
    When a round's scheduled_date is reached, the pairing algorithm runs
    and creates pairs for that round.

    Attributes:
        organization: Foreign key to the organization this round belongs to
        id: Sequential round ID within the organization (part of composite primary key)
        scheduled_date: UTC timestamp when this round should be executed
        done: Boolean indicating if pairing has been completed for this round
    """

    __tablename__ = "rounds"

    organization = Column(
        String,
        ForeignKey("organizations.name"),
        primary_key=True,
        nullable=False,
    )
    """Organization name (foreign key, part of composite primary key)"""

    id = Column(
        Integer,
        primary_key=True,
        nullable=False,
    )
    """Sequential round ID within the organization (part of composite primary key)"""

    scheduled_date = Column(
        DateTime,
        nullable=False,
    )
    """
    UTC timestamp when this round should be executed.
    The scheduler checks for rounds where scheduled_date <= now() and done = false.
    """

    done = Column(
        Boolean,
        nullable=False,
    )
    """Whether pairing has been completed for this round"""

    # Add check constraint to match schema.sql
    __table_args__ = (CheckConstraint("id >= 0", name="rounds_id_check"),)

    def __repr__(self) -> str:
        """Return string representation of Round for debugging."""
        return f"<Round(org={self.organization!r}, id={self.id}, scheduled={self.scheduled_date}, done={self.done})>"
