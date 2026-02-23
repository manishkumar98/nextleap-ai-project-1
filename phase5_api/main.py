from __future__ import annotations
import os
from typing import List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from phase1_data_ingestion.models import Restaurant, Base
from phase3_llm_orchestration.orchestrator import LLMOrchestrator
from phase3_llm_orchestration.types import UserPreferences
from phase4_retrieval.retrieval import (
    get_engine as get_retrieval_engine,
    get_recommendations,
    init_schema,
    get_distinct_locations,
    get_distinct_cuisines,
)
from .schemas import (
    RecommendationRequest,
    RecommendationResponse,
    RecommendationItem,
    HealthResponse,
)

app = FastAPI(title="AI Restaurant Recommendation Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Host static files (CSS, JS, images)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    index_path = os.path.join(frontend_path, "index.html")
    with open(index_path, "r") as f:
        return f.read()


@app.on_event("startup")
def on_startup() -> None:
    """
    Ensure DB schema is present on startup.
    """
    engine = get_retrieval_engine()
    Base.metadata.create_all(bind=engine)
    init_schema(engine)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/locations", response_model=List[str])
def list_locations() -> List[str]:
    return get_distinct_locations()


@app.get("/cuisines", response_model=List[str])
def list_cuisines() -> List[str]:
    return get_distinct_cuisines()


async def _build_prefs_from_request(body: RecommendationRequest) -> UserPreferences:
    """
    Separate Prompt-based and Filter-based search modes.
    """
    # If a query text is provided, use LLM-based parsing (Prompt Mode)
    if body.query_text and body.query_text.strip() and body.query_text != "recommend restaurants":
        orch = LLMOrchestrator()
        # In Prompt Mode, we only use the location hint if provided, and the LLM-parsed prefs
        base_prefs = await orch.parse_preferences(
            query_text=body.query_text, location_hint=body.location
        )
        print(f"DEBUG: Using PROMPT mode for query: '{body.query_text}'")
        return base_prefs

    # Otherwise, use explicit filters (Filter Mode)
    print("DEBUG: Using FILTER mode")
    return UserPreferences(
        query_text=body.query_text or "Scouting based on filters",
        location=body.location,
        cuisines=body.cuisines or [],
        min_rating=body.min_rating,
        max_rating=body.max_rating,
        min_price_for_two=body.min_price_for_two,
        max_price_for_two=body.max_price_for_two,
        wants_online_order=body.wants_online_order,
        wants_table_booking=body.wants_table_booking,
        wants_buffet=body.wants_buffet,
    )


@app.post("/recommendations", response_model=RecommendationResponse)
async def create_recommendations(body: RecommendationRequest) -> RecommendationResponse:
    """
    Main recommendations endpoint.
    """
    prefs = await _build_prefs_from_request(body)
    print(f"DEBUG: Prefs: {prefs}")
    engine = get_retrieval_engine()

    # Get ranked recommendations (id + score + reason)
    recs = await get_recommendations(
        prefs,
        limit=body.limit,
        engine=engine,
        orchestrator=LLMOrchestrator(),
    )
    print(f"DEBUG: Recs found: {len(recs)}")

    if not recs:
        return RecommendationResponse(recommendations=[])

    # Expand restaurant details for API response
    items: List[RecommendationItem] = []
    with Session(engine) as session:
        ids = [r.restaurant_id for r in recs]
        q = session.query(Restaurant).filter(Restaurant.id.in_(ids)).all()
        rest_by_id = {r.id: r for r in q}

    for r in recs:
        rest = rest_by_id.get(r.restaurant_id)
        if rest is None:
            continue
        cuisines: List[str] = []
        if rest.cuisines:
            cuisines = [c.strip() for c in rest.cuisines.split(",") if c.strip()]
        items.append(
            RecommendationItem(
                id=rest.id,
                name=rest.name,
                location=rest.location,
                cuisines=cuisines,
                rating=rest.rating,
                approx_cost_for_two=rest.approx_cost_for_two,
                score=r.score,
                reason=r.reason,
            )
        )

    return RecommendationResponse(recommendations=items)


def main() -> None:
    import uvicorn
    uvicorn.run("phase5_api.main:app", host="0.0.0.0", port=8001, reload=False)


if __name__ == "__main__":
    main()
