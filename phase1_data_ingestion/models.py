from __future__ import annotations

from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Restaurant(Base):
    """
    Core restaurant table based on the Zomato dataset fields.

    This covers the raw/cleaned data needed for later phases.
    """

    __tablename__ = "restaurants"

    id: int = Column(Integer, primary_key=True, autoincrement=True)

    # Core identifiers
    name: str = Column(String(255), nullable=False)
    url: Optional[str] = Column(String(512), nullable=True)
    address: Optional[str] = Column(String(512), nullable=True)

    # Meta
    location: Optional[str] = Column(String(255), nullable=True)
    listed_in_city: Optional[str] = Column(String(255), nullable=True)
    listed_in_type: Optional[str] = Column(String(255), nullable=True)
    rest_type: Optional[str] = Column(String(255), nullable=True)

    # Binary flags
    online_order: Optional[bool] = Column(Boolean, nullable=True)
    book_table: Optional[bool] = Column(Boolean, nullable=True)

    # Ratings & popularity
    rating: Optional[Float] = Column(Float, nullable=True)
    votes: Optional[int] = Column(Integer, nullable=True)

    # Pricing
    approx_cost_for_two: Optional[int] = Column(Integer, nullable=True)

    # Multi-valued / text fields
    cuisines: Optional[str] = Column(String(512), nullable=True)  # comma-separated
    dish_liked: Optional[str] = Column(Text, nullable=True)
    reviews_list: Optional[str] = Column(Text, nullable=True)
    menu_item: Optional[str] = Column(Text, nullable=True)
    phone: Optional[str] = Column(String(255), nullable=True)


__all__ = ["Base", "Restaurant"]

