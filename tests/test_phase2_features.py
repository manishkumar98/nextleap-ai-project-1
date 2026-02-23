from typing import List

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from phase1_data_ingestion.models import Base, Restaurant
from phase2_feature_engineering.embedding import (
    compute_embedding,
    vector_to_string,
    string_to_vector,
)
from phase2_feature_engineering.features import (
    compute_price_bucket,
    compute_rating_bucket,
    compute_popularity_score,
    build_search_text,
    build_features_for_restaurant,
    init_feature_schema,
    generate_features_for_all,
)
from phase2_feature_engineering.models import RestaurantFeatures


def _make_in_memory_engine():
    return create_engine("sqlite:///:memory:", future=True)


def test_price_bucket_rules():
    assert compute_price_bucket(None) is None
    assert compute_price_bucket(300) == 1  # low
    assert compute_price_bucket(800) == 2  # medium
    assert compute_price_bucket(2000) == 3  # high


def test_rating_bucket_rules():
    assert compute_rating_bucket(None) is None
    assert compute_rating_bucket(2.5) == 1  # low
    assert compute_rating_bucket(3.5) == 2  # medium
    assert compute_rating_bucket(4.5) == 3  # high


def test_popularity_score_monotonic():
    low_votes = compute_popularity_score(4.0, 10)
    high_votes = compute_popularity_score(4.0, 1000)
    assert low_votes < high_votes


def test_build_search_text_includes_key_fields():
    rest = Restaurant(
        name="Test R",
        location="Banashankari",
        listed_in_city="Banashankari",
        listed_in_type="Buffet",
        rest_type="Casual Dining",
        cuisines="North Indian, Chinese",
        dish_liked="Paneer Tikka",
    )
    text = build_search_text(rest)
    assert "Test R" in text
    assert "Banashankari" in text
    assert "Buffet" in text
    assert "Paneer Tikka" in text


def test_embedding_roundtrip_and_determinism():
    text = "some search text"
    vec1: List[float] = compute_embedding(text, dim=8)
    vec2: List[float] = compute_embedding(text, dim=8)
    assert vec1 == vec2  # deterministic

    s = vector_to_string(vec1)
    vec3 = string_to_vector(s)
    assert len(vec3) == len(vec1)
    # Values should be close (string formatting to 6 decimal places)
    for a, b in zip(vec1, vec3):
        assert abs(a - b) < 1e-5


def test_build_features_for_restaurant_populates_fields():
    rest = Restaurant(
        id=1,
        name="R1",
        location="Banashankari",
        listed_in_city="Banashankari",
        listed_in_type="Buffet",
        rest_type="Casual Dining",
        cuisines="North Indian, Chinese",
        dish_liked="Paneer Tikka",
        rating=4.2,
        votes=150,
        approx_cost_for_two=800,
        online_order=True,
        book_table=False,
    )
    features = build_features_for_restaurant(rest)
    assert features.restaurant_id == 1
    assert features.rating_bucket in (2, 3)
    assert features.price_bucket == 2
    assert features.popularity_score is not None
    assert features.has_buffet is True
    assert features.supports_online_order is True
    assert features.supports_table_booking is False
    assert features.search_text
    assert features.embedding


def test_generate_features_for_all_creates_feature_rows():
    engine = _make_in_memory_engine()
    # Create schema
    Base.metadata.create_all(bind=engine)
    init_feature_schema(engine)

    # Insert some restaurants
    with Session(engine) as session:
        r1 = Restaurant(
            name="R1",
            location="Banashankari",
            listed_in_city="Banashankari",
            approx_cost_for_two=400,
            rating=4.0,
            votes=50,
            rest_type="Cafe",
            listed_in_type="Cafes",
            online_order=True,
            book_table=True,
        )
        r2 = Restaurant(
            name="R2",
            location="Basavanagudi",
            listed_in_city="Basavanagudi",
            approx_cost_for_two=2000,
            rating=3.2,
            votes=10,
            rest_type="Casual Dining",
        )
        session.add_all([r1, r2])
        session.commit()

    created = generate_features_for_all(engine)
    assert created == 2

    with Session(engine) as session:
        rows = session.execute(select(RestaurantFeatures).order_by(RestaurantFeatures.restaurant_id)).scalars().all()
        assert len(rows) == 2
        assert rows[0].search_text is not None
        assert rows[0].embedding is not None
        # Ensure buckets are populated
        assert rows[0].price_bucket is not None
        assert rows[0].rating_bucket is not None

