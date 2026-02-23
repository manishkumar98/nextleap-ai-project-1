from __future__ import annotations

from typing import Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from phase1_data_ingestion.models import Base, Restaurant
from .config import settings
from .embedding import compute_embedding, vector_to_string
from .models import RestaurantFeatures


def compute_price_bucket(approx_cost_for_two: Optional[int]) -> Optional[int]:
    """
    Compute a simple price bucket:
    - 0: unknown
    - 1: low (<= low_price_max)
    - 2: medium (<= mid_price_max)
    - 3: high (> mid_price_max)
    """
    if approx_cost_for_two is None:
        return None
    if approx_cost_for_two <= settings.low_price_max:
        return 1
    if approx_cost_for_two <= settings.mid_price_max:
        return 2
    return 3


def compute_rating_bucket(rating: Optional[float]) -> Optional[int]:
    """
    Compute rating bucket:
    - 0: unknown
    - 1: low (< rating_medium_min)
    - 2: medium (>= rating_medium_min and < rating_high_min)
    - 3: high (>= rating_high_min)
    """
    if rating is None:
        return None
    if rating < settings.rating_medium_min:
        return 1
    if rating < settings.rating_high_min:
        return 2
    return 3


def compute_popularity_score(rating: Optional[float], votes: Optional[int]) -> Optional[float]:
    """
    Combine rating and votes into a single score.

    Simple heuristic: (rating or 0) * log10(1 + votes).
    """
    if rating is None and votes is None:
        return None
    r = rating or 0.0
    v = votes or 0
    # Delay import to avoid global dependency
    import math

    return r * math.log10(1 + v)


def has_keyword(value: Optional[str], keyword: str) -> Optional[bool]:
    if value is None:
        return None
    return keyword.lower() in value.lower()


def infer_has_buffet(rest: Restaurant) -> Optional[bool]:
    """
    Detect buffet-oriented restaurants based on rest_type or listed_in_type.
    """
    flagged = any(
        has_keyword(field, "buffet")
        for field in [rest.rest_type, rest.listed_in_type]
    )
    # If we couldn't find any evidence, return None instead of False.
    if not flagged and all(f is None for f in [rest.rest_type, rest.listed_in_type]):
        return None
    return flagged


def infer_is_cafe(rest: Restaurant) -> Optional[bool]:
    flagged = any(
        has_keyword(field, "cafe") for field in [rest.rest_type, rest.listed_in_type]
    )
    if not flagged and all(f is None for f in [rest.rest_type, rest.listed_in_type]):
        return None
    return flagged


def build_search_text(rest: Restaurant) -> str:
    """
    Compose a unified search text field from multiple restaurant attributes.
    """
    parts = [
        rest.name or "",
        rest.location or "",
        rest.listed_in_city or "",
        rest.listed_in_type or "",
        rest.rest_type or "",
        rest.cuisines or "",
        rest.dish_liked or "",
    ]
    return " | ".join(p for p in parts if p)


def build_features_for_restaurant(rest: Restaurant) -> RestaurantFeatures:
    """
    Construct a RestaurantFeatures object from a Restaurant row.
    """
    rating_bucket = compute_rating_bucket(rest.rating)
    price_bucket = compute_price_bucket(rest.approx_cost_for_two)
    popularity_score = compute_popularity_score(rest.rating, rest.votes)
    has_buffet = infer_has_buffet(rest)
    is_cafe = infer_is_cafe(rest)
    supports_online_order = rest.online_order
    supports_table_booking = rest.book_table
    search_text = build_search_text(rest)

    # Simple deterministic embedding for now
    embedding_vec = compute_embedding(search_text, settings.embedding_dim)
    embedding_str = vector_to_string(embedding_vec)

    return RestaurantFeatures(
        restaurant_id=rest.id,
        rating_bucket=rating_bucket,
        price_bucket=price_bucket,
        popularity_score=popularity_score,
        has_buffet=has_buffet,
        is_cafe=is_cafe,
        supports_online_order=supports_online_order,
        supports_table_booking=supports_table_booking,
        search_text=search_text,
        embedding=embedding_str,
    )


def get_engine():
    """
    Create a SQLAlchemy engine pointing at the main DB.
    """
    return create_engine(settings.db_url, future=True)


def init_feature_schema(engine=None) -> None:
    """
    Ensure both the base and feature tables exist.
    """
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(bind=engine)


def generate_features_for_all(engine=None) -> int:
    """
    Generate features for all restaurants that do not yet have a features row.

    Returns the number of feature rows created.
    """
    if engine is None:
        engine = get_engine()

    init_feature_schema(engine)

    created = 0
    with Session(engine) as session:
        # Find restaurants that do not yet have features
        existing_ids = {
            rid
            for rid in session.execute(select(RestaurantFeatures.restaurant_id)).scalars()
        }

        restaurants = (
            session.execute(select(Restaurant).order_by(Restaurant.id)).scalars().all()
        )
        for rest in restaurants:
            if rest.id in existing_ids:
                continue
            features = build_features_for_restaurant(rest)
            session.add(features)
            created += 1

        session.commit()
    return created


__all__ = [
    "compute_price_bucket",
    "compute_rating_bucket",
    "compute_popularity_score",
    "build_search_text",
    "build_features_for_restaurant",
    "init_feature_schema",
    "generate_features_for_all",
]

