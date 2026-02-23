from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    query_text: str = Field(
        ...,
        description="Free-form text describing what the user wants.",
    )
    location: Optional[str] = Field(
        None,
        description="Preferred location name, e.g. 'Banashankari'.",
    )
    cuisines: List[str] = Field(
        default_factory=list,
        description="Preferred cuisines (overrides those inferred from query_text).",
    )
    min_rating: Optional[float] = Field(
        None,
        ge=0.0,
        le=5.0,
        description="Minimum acceptable rating.",
    )
    max_rating: Optional[float] = Field(
        None,
        ge=0.0,
        le=5.0,
        description="Maximum acceptable rating.",
    )
    min_price_for_two: Optional[int] = Field(
        None,
        ge=0,
        description="Minimum approximate cost for two people.",
    )
    max_price_for_two: Optional[int] = Field(
        None,
        ge=0,
        description="Maximum approximate cost for two people.",
    )
    wants_online_order: Optional[bool] = None
    wants_table_booking: Optional[bool] = None
    wants_buffet: Optional[bool] = None
    limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of recommendations to return.",
    )


class RecommendationItem(BaseModel):
    id: int
    name: str
    location: Optional[str]
    cuisines: List[str]
    rating: Optional[float]
    approx_cost_for_two: Optional[int]
    score: float
    reason: str


class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem]


class HealthResponse(BaseModel):
    status: str


__all__ = [
    "RecommendationRequest",
    "RecommendationItem",
    "RecommendationResponse",
    "HealthResponse",
]

