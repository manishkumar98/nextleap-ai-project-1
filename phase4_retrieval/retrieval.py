from __future__ import annotations

from typing import List, Optional

from sqlalchemy import and_, create_engine, select, or_
from sqlalchemy.orm import Session

from phase1_data_ingestion.models import Restaurant
from phase2_feature_engineering.models import RestaurantFeatures
from phase3_llm_orchestration.orchestrator import LLMOrchestrator
from phase3_llm_orchestration.types import CandidateRestaurant, LLMRecommendation, UserPreferences
from .config import settings


def get_engine():
    """
    Create a SQLAlchemy engine pointing at the main DB.
    """
    return create_engine(settings.db_url, future=True)


def init_schema(engine) -> None:
    """
    Placeholder for any retrieval-specific schema (e.g. specialized indexes).
    Currently just ensuring Base is created is handled by phase5_api or ingest.
    """
    pass


def _build_candidate_from_row(rest: Restaurant, feats: Optional[RestaurantFeatures]) -> CandidateRestaurant:
    """
    Map raw ORM models to the CandidateRestaurant representation.
    """
    cuisines = []
    if rest.cuisines:
        cuisines = [c.strip() for c in rest.cuisines.split(",") if c.strip()]

    return CandidateRestaurant(
        id=rest.id,
        name=rest.name,
        location=rest.location,
        cuisines=cuisines,
        rating=rest.rating,
        votes=rest.votes or 0,
        approx_cost_for_two=rest.approx_cost_for_two,
        popularity_score=feats.popularity_score if feats else None,
        has_buffet=feats.has_buffet if feats else None,
        is_cafe=feats.is_cafe if feats else None,
        supports_online_order=rest.online_order,
        supports_table_booking=rest.book_table,
    )


def search_candidates(
    prefs: UserPreferences,
    limit: int = 20,
    engine=None,
) -> List[CandidateRestaurant]:
    """
    Core retrieval logic:
    - Query DB for restaurants matching hard filters from prefs.
    - Joins RestaurantFeatures for scoring data.
    """
    if engine is None:
        engine = get_engine()

    candidates: List[CandidateRestaurant] = []
    with Session(engine) as session:
        stmt = (
            select(Restaurant, RestaurantFeatures)
            .join(
                RestaurantFeatures,
                Restaurant.id == RestaurantFeatures.restaurant_id,
                isouter=True,
            )
        )

        conditions = []
        if prefs.location:
            from sqlalchemy import func
            conditions.append(func.lower(Restaurant.location) == prefs.location.lower())
            
        if prefs.cuisines:
            cuisine_filters = [
                Restaurant.cuisines.icontains(cuisine) for cuisine in prefs.cuisines
            ]
            conditions.append(or_(*cuisine_filters))
            
        if prefs.min_rating is not None:
            conditions.append(Restaurant.rating >= prefs.min_rating)
        if prefs.max_rating is not None:
            conditions.append(Restaurant.rating <= prefs.max_rating)
            
        if prefs.min_price_for_two is not None:
            conditions.append(Restaurant.approx_cost_for_two >= prefs.min_price_for_two)
        if prefs.max_price_for_two is not None:
            conditions.append(Restaurant.approx_cost_for_two <= prefs.max_price_for_two)
            
        if prefs.wants_online_order:
            conditions.append(Restaurant.online_order.is_(True))
        if prefs.wants_table_booking:
            conditions.append(Restaurant.book_table.is_(True))
        if prefs.wants_buffet:
            conditions.append(RestaurantFeatures.has_buffet.is_(True))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Deduplicate by grouping by name and location
        stmt = stmt.group_by(Restaurant.name, Restaurant.location)

        # Baseline ordering by feature popularity, then rating and votes
        stmt = stmt.order_by(
            RestaurantFeatures.popularity_score.desc().nullslast(),
            Restaurant.rating.desc().nullslast(),
            Restaurant.votes.desc(),
        ).limit(limit)

        results = session.execute(stmt).all()
        for rest, feats in results:
            candidates.append(_build_candidate_from_row(rest, feats))

    return candidates


def get_distinct_locations(engine=None) -> List[str]:
    """
    Fetch all unique location names currently in the database.
    """
    if engine is None:
        engine = get_engine()

    with Session(engine) as session:
        stmt = select(Restaurant.location).distinct().order_by(Restaurant.location)
        results = session.execute(stmt).scalars().all()
        return [loc for loc in results if loc]


def get_distinct_cuisines(engine=None) -> List[str]:
    """
    Fetch all unique cuisines currently in the database.
    """
    if engine is None:
        engine = get_engine()

    with Session(engine) as session:
        stmt = select(Restaurant.cuisines).distinct()
        results = session.execute(stmt).scalars().all()
        
        all_cuisines = set()
        for c_str in results:
            if c_str:
                for c in c_str.split(","):
                    all_cuisines.add(c.strip())
        
        return sorted(list(all_cuisines))


async def get_recommendations(
    prefs: UserPreferences,
    limit: int = 10,
    engine=None,
    orchestrator: Optional[LLMOrchestrator] = None,
) -> List[LLMRecommendation]:
    """
    High-level helper:
    - Fetch candidates via hard filters.
    - Ask Phase 3 orchestrator to re-rank and generate reasons.
    """
    if engine is None:
        engine = get_engine()

    if orchestrator is None:
        orchestrator = LLMOrchestrator()

    candidates = search_candidates(prefs, limit=limit, engine=engine)
    if not candidates:
        return []

    recs = await orchestrator.rerank_candidates(prefs, candidates)
    return recs[:limit]


__all__ = [
    "search_candidates", 
    "get_recommendations", 
    "get_engine", 
    "init_schema", 
    "get_distinct_locations", 
    "get_distinct_cuisines"
]
