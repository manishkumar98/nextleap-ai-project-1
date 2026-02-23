from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from phase1_data_ingestion.models import Base, Restaurant
from phase2_feature_engineering.models import RestaurantFeatures
from phase3_llm_orchestration.orchestrator import LLMOrchestrator
from phase3_llm_orchestration.types import UserPreferences
from phase4_retrieval.retrieval import search_candidates, get_recommendations


def _make_in_memory_engine():
    return create_engine("sqlite:///:memory:", future=True)


def _seed_sample_data(engine):
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        # Restaurant 1: strong match
        r1 = Restaurant(
            name="Buffet Palace",
            location="Banashankari",
            listed_in_city="Banashankari",
            approx_cost_for_two=600,
            rating=4.5,
            votes=200,
            cuisines="North Indian, Chinese",
            online_order=True,
            book_table=True,
        )

        # Restaurant 2: weaker match (higher price, lower rating)
        r2 = Restaurant(
            name="Average Diner",
            location="Banashankari",
            listed_in_city="Banashankari",
            approx_cost_for_two=1800,
            rating=3.2,
            votes=20,
            cuisines="North Indian",
            online_order=False,
            book_table=False,
        )

        # Restaurant 3: different location
        r3 = Restaurant(
            name="Far Away Cafe",
            location="Basavanagudi",
            listed_in_city="Basavanagudi",
            approx_cost_for_two=500,
            rating=4.0,
            votes=50,
            cuisines="Cafe",
            online_order=True,
            book_table=False,
        )

        session.add_all([r1, r2, r3])
        session.commit()

        # Fetch IDs after commit
        r1_id = r1.id
        r2_id = r2.id
        r3_id = r3.id

        f1 = RestaurantFeatures(
            restaurant_id=r1_id,
            rating_bucket=3,
            price_bucket=2,
            popularity_score=10.0,
            has_buffet=True,
            is_cafe=False,
            supports_online_order=True,
            supports_table_booking=True,
            search_text="Buffet Palace Banashankari North Indian buffet",
            embedding="0.1,0.2,0.3",
        )
        f2 = RestaurantFeatures(
            restaurant_id=r2_id,
            rating_bucket=2,
            price_bucket=3,
            popularity_score=3.0,
            has_buffet=False,
            is_cafe=False,
            supports_online_order=False,
            supports_table_booking=False,
            search_text="Average Diner Banashankari",
            embedding="0.1,0.2,0.3",
        )
        f3 = RestaurantFeatures(
            restaurant_id=r3_id,
            rating_bucket=3,
            price_bucket=1,
            popularity_score=5.0,
            has_buffet=False,
            is_cafe=True,
            supports_online_order=True,
            supports_table_booking=False,
            search_text="Far Away Cafe Basavanagudi",
            embedding="0.1,0.2,0.3",
        )

        session.add_all([f1, f2, f3])
        session.commit()


def test_search_candidates_applies_location_and_price_and_rating_filters():
    engine = _make_in_memory_engine()
    _seed_sample_data(engine)

    prefs = UserPreferences(
        query_text="cheap north indian buffet in Banashankari rated 4+",
        location="Banashankari",
        cuisines=["north indian"],
        min_rating=4.0,
        max_price_for_two=800,
        wants_buffet=True,
        wants_online_order=True,
        wants_table_booking=True,
    )

    candidates = search_candidates(prefs, limit=10, engine=engine)
    # Only Buffet Palace should match all filters
    assert len(candidates) == 1
    assert candidates[0].name == "Buffet Palace"
    assert "North Indian" in candidates[0].cuisines


def test_get_recommendations_integration_with_orchestrator():
    engine = _make_in_memory_engine()
    _seed_sample_data(engine)

    prefs = UserPreferences(
        query_text="north indian in Banashankari under 1000 with good rating",
        location="Banashankari",
        cuisines=["north indian"],
        min_rating=3.0,
        max_price_for_two=1000,
        wants_buffet=None,
        wants_online_order=None,
        wants_table_booking=None,
    )

    orch = LLMOrchestrator()
    recs = get_recommendations(prefs, limit=5, engine=engine, orchestrator=orch)

    # Should recommend at least one place in Banashankari
    assert recs
    # Buffet Palace should be the top recommendation due to higher rating and popularity
    top_id = recs[0].restaurant_id

    with Session(engine) as session:
        top_rest = session.execute(
            select(Restaurant).where(Restaurant.id == top_id)
        ).scalar_one()
        assert top_rest.name == "Buffet Palace"

