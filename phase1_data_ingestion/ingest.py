from __future__ import annotations

"""
Phase 1 ingestion script.

Responsibilities:
- Create the database schema.
- Load the Zomato dataset from Hugging Face.
- Clean/normalize each record.
- Persist restaurants into the database in batches.
"""

from typing import Iterable, Mapping

from datasets import load_dataset
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .cleaning import clean_record
from .config import settings
from .models import Base, Restaurant


def get_engine():
    """
    Create a SQLAlchemy engine using configuration from settings.
    """
    return create_engine(settings.db_url, future=True)


def init_db(engine=None) -> None:
    """
    Create database tables if they do not exist.
    """
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(bind=engine)


def iter_clean_restaurants(rows: Iterable[Mapping]) -> Iterable[Restaurant]:
    """
    Yield Restaurant ORM instances from raw dataset rows.
    """
    for row in rows:
        cleaned = clean_record(row)
        if not cleaned["name"]:
            # Skip rows without a valid name
            continue
        yield Restaurant(**cleaned)


def bulk_insert_restaurants(session: Session, restaurants: Iterable[Restaurant]) -> int:
    """
    Insert a batch of Restaurant objects and return count inserted.
    """
    batch = list(restaurants)
    if not batch:
        return 0
    session.add_all(batch)
    session.commit()
    return len(batch)


def ingest_from_huggingface(max_records: int = 1000) -> int:
    """
    Main ingestion routine:
    - Loads the configured HF dataset using streaming to save disk space.
    - Cleans and inserts rows until max_records is reached.
    """
    engine = get_engine()
    init_db(engine)

    # Use streaming=True to avoid downloading the entire 1GB+ dataset
    ds = load_dataset(settings.hf_dataset_name, split=settings.hf_dataset_split, streaming=True)

    total_inserted = 0
    batch_size = settings.ingest_batch_size
    
    with Session(engine) as session:
        batch = []
        for row in ds:
            if total_inserted >= max_records:
                break
                
            cleaned = clean_record(row)
            if not cleaned["name"]:
                continue
                
            batch.append(Restaurant(**cleaned))
            
            if len(batch) >= batch_size:
                session.add_all(batch)
                session.commit()
                total_inserted += len(batch)
                batch = []
                
        if batch:
            session.add_all(batch)
            session.commit()
            total_inserted += len(batch)

    return total_inserted


def main() -> None:
    """
    CLI entrypoint for running Phase 1 ingestion.
    """
    total = ingest_from_huggingface()
    print(f"Ingestion complete. Inserted {total} restaurants.")


if __name__ == "__main__":
    main()

