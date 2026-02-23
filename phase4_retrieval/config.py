import os
from dataclasses import dataclass


@dataclass
class RetrievalSettings:
    """
    Configuration for Phase 4 retrieval.
    """

    # Database URL – must match Phases 1 & 2
    db_url: str = os.getenv("DB_URL", "sqlite:///./zomato_restaurants.db")


settings = RetrievalSettings()

