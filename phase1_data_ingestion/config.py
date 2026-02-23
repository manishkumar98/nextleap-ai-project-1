import os
from dataclasses import dataclass


@dataclass
class Settings:
    """
    Configuration for Phase 1 ingestion.

    Values can be overridden via environment variables.
    """

    # Hugging Face dataset identifier
    hf_dataset_name: str = os.getenv(
        "HF_DATASET_NAME", "ManikaSaini/zomato-restaurant-recommendation"
    )
    hf_dataset_split: str = os.getenv("HF_DATASET_SPLIT", "train")

    # Database URL – defaults to a local SQLite file for development.
    db_url: str = os.getenv("DB_URL", "sqlite:///./zomato_restaurants.db")

    # Batch size for bulk inserts
    ingest_batch_size: int = int(os.getenv("INGEST_BATCH_SIZE", "1000"))


settings = Settings()

