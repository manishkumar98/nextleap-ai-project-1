from typing import Dict, Any, List

from sqlalchemy import create_engine, select, inspect
from sqlalchemy.orm import Session

from phase1_data_ingestion.ingest import (
    init_db,
    iter_clean_restaurants,
    bulk_insert_restaurants,
)
from phase1_data_ingestion.models import Base, Restaurant


def _make_in_memory_engine():
    return create_engine("sqlite:///:memory:", future=True)


def test_iter_clean_restaurants_skips_missing_name():
    rows: List[Dict[str, Any]] = [
        {"name": "Valid", "rate": "4.0/5", "votes": 10, "approx_cost(for two people)": "500"},
        {"name": "", "rate": "4.0/5", "votes": 5, "approx_cost(for two people)": "400"},
    ]
    restaurants = list(iter_clean_restaurants(rows))
    assert len(restaurants) == 1
    assert restaurants[0].name == "Valid"


def test_bulk_insert_restaurants_inserts_into_db():
    engine = _make_in_memory_engine()
    Base.metadata.create_all(bind=engine)

    rows: List[Dict[str, Any]] = [
        {
            "name": "R1",
            "rate": "4.0/5",
            "votes": 10,
            "approx_cost(for two people)": "500",
            "online_order": "Yes",
            "book_table": "No",
            "location": "Banashankari",
        },
        {
            "name": "R2",
            "rate": "3.5/5",
            "votes": 5,
            "approx_cost(for two people)": "400",
            "online_order": "No",
            "book_table": "No",
            "location": "Basavanagudi",
        },
    ]

    with Session(engine) as session:
        restaurants = list(iter_clean_restaurants(rows))
        count = bulk_insert_restaurants(session, restaurants)
        assert count == 2

        result = session.execute(select(Restaurant).order_by(Restaurant.name)).scalars().all()
        assert len(result) == 2
        assert result[0].name == "R1"
        assert result[1].name == "R2"
        # Ensure key fields have been parsed
        assert result[0].rating is not None
        assert result[0].approx_cost_for_two == 500


def test_init_db_creates_tables():
    engine = _make_in_memory_engine()
    # Before calling init_db, tables should not exist
    inspector = inspect(engine)
    assert "restaurants" not in inspector.get_table_names()

    init_db(engine)
    inspector = inspect(engine)
    assert "restaurants" in inspector.get_table_names()

