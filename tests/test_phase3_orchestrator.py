from phase3_llm_orchestration.orchestrator import LLMOrchestrator
from phase3_llm_orchestration.types import CandidateRestaurant


def test_parse_preferences_basic_extraction():
    orch = LLMOrchestrator()
    prefs = orch.parse_preferences(
        "Looking for a cheap North Indian buffet in Banashankari rated above 4",
        location_hint="Banashankari",
    )

    assert prefs.location == "Banashankari"
    assert "north indian" in [c.lower() for c in prefs.cuisines]
    assert prefs.max_price_for_two == 500
    assert prefs.min_rating is not None and prefs.min_rating >= 4.0
    assert prefs.wants_buffet is True


def test_rerank_candidates_prefers_higher_score_and_generates_reason():
    orch = LLMOrchestrator()
    prefs = orch.parse_preferences(
        "North Indian under 800 with good rating in Banashankari",
        location_hint="Banashankari",
    )

    candidates = [
        CandidateRestaurant(
            id=1,
            name="Average Place",
            location="Banashankari",
            cuisines=["North Indian"],
            rating=3.5,
            votes=20,
            approx_cost_for_two=700,
            popularity_score=None,
            has_buffet=False,
            is_cafe=False,
            supports_online_order=True,
            supports_table_booking=False,
        ),
        CandidateRestaurant(
            id=2,
            name="Better Place",
            location="Banashankari",
            cuisines=["North Indian"],
            rating=4.5,
            votes=150,
            approx_cost_for_two=750,
            popularity_score=None,
            has_buffet=True,
            is_cafe=False,
            supports_online_order=True,
            supports_table_booking=True,
        ),
    ]

    results = orch.rerank_candidates(prefs, candidates)
    assert len(results) == 2
    # The better-rated, more popular candidate should come first
    assert results[0].restaurant_id == 2
    # Reason should mention the restaurant name and location/rating info
    assert "Better Place" in results[0].reason
    assert "rated" in results[0].reason
    assert "Banashankari" in results[0].reason

