from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class UserPreferences:
    """
    Structured representation of user preferences as understood by the system.
    """

    query_text: str
    location: Optional[str] = None
    cuisines: List[str] = field(default_factory=list)
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None
    min_price_for_two: Optional[int] = None
    max_price_for_two: Optional[int] = None
    wants_online_order: Optional[bool] = None
    wants_table_booking: Optional[bool] = None
    wants_buffet: Optional[bool] = None


@dataclass
class CandidateRestaurant:
    """
    Lightweight view of a restaurant plus key features needed for ranking.
    """

    id: int
    name: str
    location: Optional[str]
    cuisines: List[str]
    rating: Optional[float]
    votes: int
    approx_cost_for_two: Optional[int]
    popularity_score: Optional[float] = None
    has_buffet: Optional[bool] = None
    is_cafe: Optional[bool] = None
    supports_online_order: Optional[bool] = None
    supports_table_booking: Optional[bool] = None


@dataclass
class LLMRecommendation:
    """
    Final recommendation item returned by the LLM orchestrator.
    """

    restaurant_id: int
    score: float
    reason: str


__all__ = ["UserPreferences", "CandidateRestaurant", "LLMRecommendation"]

