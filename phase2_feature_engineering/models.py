from __future__ import annotations

from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    Float,
    Boolean,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from phase1_data_ingestion.models import Base, Restaurant


class RestaurantFeatures(Base):
    """
    Derived features for each restaurant.

    This keeps feature engineering concerns separate from the raw data table.
    """

    __tablename__ = "restaurant_features"

    restaurant_id: int = Column(
        Integer,
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Buckets
    rating_bucket: Optional[int] = Column(Integer, nullable=True)
    price_bucket: Optional[int] = Column(Integer, nullable=True)

    # Aggregate popularity score (combines rating and votes)
    popularity_score: Optional[Float] = Column(Float, nullable=True)

    # Flags
    has_buffet: Optional[bool] = Column(Boolean, nullable=True)
    is_cafe: Optional[bool] = Column(Boolean, nullable=True)
    supports_online_order: Optional[bool] = Column(Boolean, nullable=True)
    supports_table_booking: Optional[bool] = Column(Boolean, nullable=True)

    # Text for semantic search
    search_text: Optional[str] = Column(Text, nullable=True)

    # Simple deterministic embedding stored as comma-separated floats
    embedding: Optional[str] = Column(Text, nullable=True)

    # Relationship back to the base restaurant
    restaurant = relationship(Restaurant, backref="features", lazy="joined")


__all__ = ["RestaurantFeatures"]

