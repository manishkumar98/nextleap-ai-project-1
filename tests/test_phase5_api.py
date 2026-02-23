from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from phase1_data_ingestion.models import Base, Restaurant
from phase2_feature_engineering.models import RestaurantFeatures
from phase4_retrieval import retrieval as retrieval_module
from phase5_api.main import app


def _make_in_memory_engine():
    # Use a file-based SQLite to ensure persistence across sessions in the test
    return create_engine("sqlite:///./test_api.db", future=True)


def _seed_sample_data(engine):
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        r1 = Restaurant(
            name="API Buffet Place",
            location="Banashankari",
            listed_in_city="Banashankari",
            approx_cost_for_two=400,
            rating=4.3,
            votes=120,
            cuisines="North Indian, Chinese",
            online_order=True,
            book_table=True,
        )
        r2 = Restaurant(
            name="API Average Diner",
            location="Banashankari",
            listed_in_city="Banashankari",
            approx_cost_for_two=1500,
            rating=3.0,
            votes=10,
            cuisines="North Indian",
            online_order=False,
            book_table=False,
        )
        session.add_all([r1, r2])
        session.commit()

        f1 = RestaurantFeatures(
            restaurant_id=r1.id,
            rating_bucket=3,
            price_bucket=2,
            popularity_score=8.0,
            has_buffet=True,
            is_cafe=False,
            supports_online_order=True,
            supports_table_booking=True,
            search_text="API Buffet Place Banashankari North Indian buffet",
            embedding="0.1,0.2,0.3",
        )
        f2 = RestaurantFeatures(
            restaurant_id=r2.id,
            rating_bucket=1,
            price_bucket=2,
            popularity_score=2.0,
            has_buffet=False,
            is_cafe=False,
            supports_online_order=False,
            supports_table_booking=False,
            search_text="API Average Diner Banashankari",
            embedding="0.1,0.2,0.3",
        )
        session.add_all([f1, f2])
        session.commit()


def test_health_endpoint():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_recommendations_endpoint_returns_ranked_results(monkeypatch):
    # Use an in-memory engine for this test and patch retrieval.get_engine
    engine = _make_in_memory_engine()
    _seed_sample_data(engine)

    def fake_get_engine():
        return engine

    monkeypatch.setattr("phase5_api.main.get_retrieval_engine", fake_get_engine)

    client = TestClient(app)

    payload = {
        "query_text": "cheap north indian buffet in Banashankari",
        "location": "Banashankari",
        "limit": 5,
    }
    resp = client.post("/recommendations", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    recs = data["recommendations"]

    # Should return at least one recommendation
    assert recs
    # The best buffet place should be first
    assert recs[0]["name"] == "API Buffet Place"
    # Reason should mention the name
    assert "API Buffet Place" in recs[0]["reason"]

