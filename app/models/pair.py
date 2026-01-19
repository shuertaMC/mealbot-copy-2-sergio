"""
Pair SQLAlchemy model.

Pairs represent the result of the pairing algorithm for a specific round.
Each pair links two (or three, with extraId) members within an organization.
"""

from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    CheckConstraint,
    ForeignKeyConstraint,
)

from app.database import Base


class Pair(Base):
    """
    Pair model representing a pairing result.

    Pairs are created by the pairing algorithm and link members together
    for a specific round. The model supports both 2-person and 3-person pairings
    (when there's an odd number of members, extraId is used for the third person).

    Attributes:
        organization: Foreign key to the organization
        id1: Email of the first member in the pair
        id2: Email of the second member in the pair
        extraId: Optional email of a third member (for odd-numbered groups)
        round: Round ID when this pairing occurred
    """

    __tablename__ = "pairs"

    organization = Column(
        String,
        ForeignKey("organizations.name"),
        primary_key=True,
        nullable=False,
    )
    """Organization name (foreign key, part of composite primary key)"""

    id1 = Column(
        String,
        primary_key=True,
        nullable=False,
    )
    """Email of first member in the pair (part of composite primary key)"""

    id2 = Column(
        String,
        primary_key=True,
        nullable=False,
    )
    """Email of second member in the pair (part of composite primary key)"""

    extraId = Column(
        String,
        primary_key=True,
        nullable=True,
    )
    """Optional email of third member (for groups of 3, part of composite primary key)"""

    round = Column(
        Integer,
        primary_key=True,
        nullable=False,
    )
    """Round ID when this pairing occurred (part of composite primary key)"""

    # Add check constraints to match schema.sql
    # Add foreign key constraints
    __table_args__ = (
        CheckConstraint("length(id1) > 0", name="pairs_id1_check"),
        CheckConstraint("length(id2) > 0", name="pairs_id2_check"),
        CheckConstraint("round >= 0", name="pairs_round_check"),
        # Foreign key to rounds table (organization, round) -> rounds(organization, id)
        ForeignKeyConstraint(
            ["organization", "round"],
            ["rounds.organization", "rounds.id"],
            name="pairs_round_fkey",
        ),
        # Foreign key to members table for id1
        ForeignKeyConstraint(
            ["organization", "id1"],
            ["members.organization", "members.email"],
            name="pairs_id1_fkey",
        ),
        # Foreign key to members table for id2
        ForeignKeyConstraint(
            ["organization", "id2"],
            ["members.organization", "members.email"],
            name="pairs_id2_fkey",
        ),
    )

    def __repr__(self) -> str:
        """Return string representation of Pair for debugging."""
        if self.extraId:
            return f"<Pair(org={self.organization!r}, round={self.round}, members=[{self.id1!r}, {self.id2!r}, {self.extraId!r}])>"
        return f"<Pair(org={self.organization!r}, round={self.round}, members=[{self.id1!r}, {self.id2!r}])>"
