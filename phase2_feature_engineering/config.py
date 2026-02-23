import os
from dataclasses import dataclass


@dataclass
class FeatureSettings:
    """
    Configuration for Phase 2 feature engineering.
    """

    # Database URL – should match Phase 1 by default
    db_url: str = os.getenv("DB_URL", "sqlite:///./zomato_restaurants.db")

    # Approx cost buckets (rupees for two)
    low_price_max: int = int(os.getenv("LOW_PRICE_MAX", "500"))
    mid_price_max: int = int(os.getenv("MID_PRICE_MAX", "1500"))

    # Rating buckets
    rating_medium_min: float = float(os.getenv("RATING_MEDIUM_MIN", "3.0"))
    rating_high_min: float = float(os.getenv("RATING_HIGH_MIN", "4.0"))

    # Embedding settings
    embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "16"))


settings = FeatureSettings()

