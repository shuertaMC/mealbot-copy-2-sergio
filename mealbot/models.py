"""Data classes for Mealbot domain objects."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Organization:
    """Represents an organization in the system."""

    name: str
    admin: str
    cross_match_trait: Optional[str] = None
