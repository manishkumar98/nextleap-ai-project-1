import os
from dataclasses import dataclass

@dataclass
class RetrievalSettings:
    """
    Configuration for Phase 4 retrieval.
    """
    # Database URL – must match Phases 1 & 2
    # Use absolute path to ensure Vercel and local runs find it reliably
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _default_db_path = os.path.join(BASE_DIR, "zomato_restaurants.db")
    db_url: str = os.getenv("DB_URL", f"sqlite:///{_default_db_path}")

settings = RetrievalSettings()


