from typing import Generator, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    TIMESTAMP,
    create_engine,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, sessionmaker

from mealbot.config import get_settings

# SQLAlchemy metadata for table definitions
metadata = MetaData()

# Organizations table
# Primary key is the organization name (VARCHAR)
organizations = Table(
    "organizations",
    metadata,
    Column("name", String, primary_key=True),
    Column("admin", String, nullable=False),
    Column("cross_match_trait", String, nullable=True),
    CheckConstraint("length(admin) > 0", name="organizations_admin_check"),
)

# Members table
# Composite primary key: (organization, email)
members = Table(
    "members",
    metadata,
    Column(
        "organization",
        String,
        ForeignKey("organizations.name"),
        nullable=False,
    ),
    Column("email", String, nullable=False),
    Column("name", String, nullable=False),
    Column("metadata", JSONB, nullable=True),
    Column("pair_counts", JSONB, nullable=False),
    Column("active", Boolean, nullable=False),
    PrimaryKeyConstraint("organization", "email"),
    CheckConstraint("length(email) > 0", name="members_email_check"),
    CheckConstraint("length(name) > 0", name="members_name_check"),
)

# Rounds table
# Composite primary key: (organization, id)
rounds = Table(
    "rounds",
    metadata,
    Column(
        "organization",
        String,
        ForeignKey("organizations.name"),
        nullable=False,
    ),
    Column("id", Integer, nullable=False),
    Column("scheduled_date", TIMESTAMP, nullable=False),
    Column("done", Boolean, nullable=False),
    PrimaryKeyConstraint("organization", "id"),
    CheckConstraint("id >= 0", name="rounds_id_check"),
)

# Pairs table
# Composite primary key: (organization, id1, id2, extraId, round)
pairs = Table(
    "pairs",
    metadata,
    Column(
        "organization",
        String,
        ForeignKey("organizations.name"),
        nullable=False,
    ),
    Column("id1", String, nullable=False),
    Column("id2", String, nullable=False),
    Column("extraid", String, nullable=True),  # Note: lowercase to match schema.sql
    Column("round", Integer, nullable=False),
    PrimaryKeyConstraint("organization", "id1", "id2", "extraid", "round"),
    ForeignKeyConstraint(
        ["organization", "round"],
        ["rounds.organization", "rounds.id"],
    ),
    ForeignKeyConstraint(
        ["organization", "id1"],
        ["members.organization", "members.email"],
    ),
    ForeignKeyConstraint(
        ["organization", "id2"],
        ["members.organization", "members.email"],
    ),
    CheckConstraint("length(id1) > 0", name="pairs_id1_check"),
    CheckConstraint("length(id2) > 0", name="pairs_id2_check"),
    CheckConstraint("round >= 0", name="pairs_round_check"),
)


def get_engine():
    """Create and return the SQLAlchemy engine with connection pooling."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )


# Create engine and sessionmaker
# Note: Engine creation is deferred to avoid issues during import when settings aren't available
_engine: Optional[object] = None
_SessionLocal: Optional[sessionmaker] = None


def _get_session_factory() -> sessionmaker:
    """Get or create the session factory."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    assert _SessionLocal is not None
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.

    Usage in route handlers:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...

    The session is automatically closed when the request completes.
    """
    SessionLocal = _get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
