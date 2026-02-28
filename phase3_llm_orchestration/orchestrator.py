from __future__ import annotations

import json
from typing import List, Optional

from .config import settings
from .groq_client import GroqClient
from .types import UserPreferences, CandidateRestaurant, LLMRecommendation


class LLMOrchestrator:
    """
    High-level interface for Phase 3:
    - Parse user preferences from natural language.
    - Re-rank candidates using deterministic fallback or Groq AI.
    """

    def __init__(self, groq_client: Optional[GroqClient] = None) -> None:
        self.groq_client = groq_client or GroqClient()

    async def parse_preferences(
        self,
        query_text: str,
        location_hint: Optional[str] = None,
    ) -> UserPreferences:
        """
        Extract structured preferences from free-form text.
        If Groq is available, use it for better extraction.
        """
        if settings.use_llm_by_default and self.groq_client.is_configured():
            try:
                return await self._groq_parse_preferences(query_text, location_hint)
            except Exception as e:
                print(f"Groq parse failed: {e}. Falling back to heuristic parsing.")
        
        return self._heuristic_parse_preferences(query_text, location_hint)

    async def _groq_parse_preferences(
        self,
        query_text: str,
        location_hint: Optional[str] = None,
    ) -> UserPreferences:
        system_prompt = (
            "You are a helpful assistant that extracts structured search criteria from a restaurant query. "
            "Return ONLY a JSON object with these keys: "
            "'location' (string or null), 'cuisines' (list of strings), 'min_rating' (float or null), "
            "'max_rating' (float or null), 'min_price_for_two' (int or null), 'max_price_for_two' (int or null), "
            "'wants_online_order' (bool or null), 'wants_table_booking' (bool or null), 'wants_buffet' (bool or null). "
            "Do not explain, do not add extra text."
        )
        
        user_prompt = f"Query: {query_text}\nLocation Hint: {location_hint}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_text = self.groq_client.chat(messages).strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        data = json.loads(response_text)
        
        return UserPreferences(
            query_text=query_text,
            location=data.get("location") or location_hint,
            cuisines=data.get("cuisines") or [],
            min_rating=data.get("min_rating"),
            max_rating=data.get("max_rating"),
            min_price_for_two=data.get("min_price_for_two"),
            max_price_for_two=data.get("max_price_for_two"),
            wants_online_order=data.get("wants_online_order"),
            wants_table_booking=data.get("wants_table_booking"),
            wants_buffet=data.get("wants_buffet"),
        )

    def _heuristic_parse_preferences(
        self,
        query_text: str,
        location_hint: Optional[str] = None,
    ) -> UserPreferences:
        """
        Extract structured preferences from free-form text using simple rules.
        """
        lowered = query_text.lower()
        
        # Location Extraction (Heuristic)
        # We try to find if any known location is mentioned in the query
        detected_location = location_hint
        if not detected_location:
            from phase4_retrieval.retrieval import get_distinct_locations, get_engine
            # Note: In a production environment, you would cache this list
            try:
                known_locations = get_distinct_locations(get_engine())
                for loc in known_locations:
                    if loc.lower() in lowered:
                        detected_location = loc
                        break
            except Exception:
                pass

        # Cuisines (Heuristic)
        cuisines = []
        common_cuisines = ["north indian", "south indian", "chinese", "italian", "thai", "asian", "cafe", "desserts", "continental", "mexican"]
        for word in common_cuisines:
            if word in lowered:
                cuisines.append(word)

        # Price Hints
        min_price_for_two: Optional[int] = None
        max_price_for_two: Optional[int] = None
        
        # Check for range format like "1000-1500" or "1000 to 1500"
        import re
        price_ranges = re.findall(r"(\d{3,})\s*(?:-|to)\s*(\d{3,})", lowered)
        if price_ranges:
            try:
                p1, p2 = map(int, price_ranges[0])
                min_price_for_two = min(p1, p2)
                max_price_for_two = max(p1, p2)
            except ValueError:
                pass
        
        if not max_price_for_two:
            if "cheap" in lowered or "budget" in lowered or "low cost" in lowered:
                max_price_for_two = 500
            elif "mid range" in lowered or "reasonable" in lowered:
                max_price_for_two = 1500
            elif "expensive" in lowered or "fine dining" in lowered:
                max_price_for_two = 3000

        # Rating Hints
        import re
        rating_tokens = re.findall(r"(\d\.\d|\d)", lowered)
        ratings = []
        for t in rating_tokens:
            try:
                val = float(t)
                if 0.0 <= val <= 5.0:
                    ratings.append(val)
            except ValueError:
                continue
        
        min_rating = ratings[0] if ratings else None
        max_rating = ratings[1] if len(ratings) > 1 else None
        
        if "between" in lowered or "to" in lowered or "from" in lowered:
            if len(ratings) >= 2:
                min_rating = min(ratings)
                max_rating = max(ratings)

        wants_online_order = True if any(x in lowered for x in ["delivery", "online order", "zomato"]) else None
        wants_table_booking = True if any(x in lowered for x in ["date", "table booking", "book", "reserve"]) else None
        wants_buffet = True if any(x in lowered for x in ["buffet", "unlimited", "all you can eat"]) else None

        return UserPreferences(
            query_text=query_text,
            location=detected_location,
            cuisines=cuisines,
            min_rating=min_rating,
            max_rating=max_rating,
            min_price_for_two=min_price_for_two,
            max_price_for_two=max_price_for_two,
            wants_online_order=wants_online_order,
            wants_table_booking=wants_table_booking,
            wants_buffet=wants_buffet,
        )


    async def rerank_candidates(
        self,
        prefs: UserPreferences,
        candidates: List[CandidateRestaurant],
    ) -> List[LLMRecommendation]:
        """
        Re-rank candidates using either Groq or deterministic local fallback.
        """
        if settings.use_llm_by_default and self.groq_client.is_configured():
            try:
                return await self._groq_rerank(prefs, candidates)
            except Exception as e:
                print(f"Groq rerank failed: {e}. Falling back to deterministic ranking.")
                return self._fallback_rerank(prefs, candidates)
        
        return self._fallback_rerank(prefs, candidates)

    async def _groq_rerank(
        self,
        prefs: UserPreferences,
        candidates: List[CandidateRestaurant],
    ) -> List[LLMRecommendation]:
        """
        Delegate ranking and explanation to Groq LLM.
        """
        candidate_data = [
            {
                "id": c.id,
                "name": c.name,
                "location": c.location,
                "cuisines": c.cuisines,
                "rating": c.rating,
                "votes": c.votes,
                "approx_cost_for_two": c.approx_cost_for_two,
                "has_buffet": c.has_buffet,
            }
            for c in candidates
        ]
        
        system_prompt = (
            "You are an expert restaurant recommendation assistant. "
            "Given candidate restaurants and user preferences, RANK them from best to worst. "
            "Assign a score (0.0-10.0) and provide a concise, high-quality, catchy reason for each. "
            "Return ONLY a JSON array of objects with keys: 'restaurant_id', 'score', 'reason'."
        )
        
        user_prompt = f"""
        User Query: {prefs.query_text}
        Preferences: {json.dumps(prefs.__dict__, default=str)}
        Candidates: {json.dumps(candidate_data)}
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_text = self.groq_client.chat(messages)
        
        # Clean response
        response_text = response_text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        try:
            results = json.loads(response_text)
            recs = [
                LLMRecommendation(
                    restaurant_id=item["restaurant_id"],
                    score=float(item["score"]),
                    reason=item["reason"]
                )
                for item in results
            ]
            recs.sort(key=lambda x: x.score, reverse=True)
            return recs
        except Exception as e:
            raise RuntimeError(f"Error parsing LLM response: {e}")

    def _fallback_rerank(
        self,
        prefs: UserPreferences,
        candidates: List[CandidateRestaurant],
    ) -> List[LLMRecommendation]:
        """
        Deterministic local scoring logic.
        """
        scored: List[LLMRecommendation] = []
        max_votes = max((c.votes for c in candidates), default=1)

        for c in candidates:
            rating = c.rating or 0.0
            votes = c.votes or 0
            base_score = rating * 2.0 + (votes / max_votes)

            # Simple Match Bonuses
            bonus = 0.0
            if prefs.cuisines and any(cu.lower() in [x.lower() for x in c.cuisines] for cu in prefs.cuisines):
                bonus += 1.0
            if prefs.min_rating and rating >= prefs.min_rating:
                bonus += 0.5
            
            score = base_score + bonus
            reason = self._build_reason(prefs, c)
            scored.append(LLMRecommendation(restaurant_id=c.id, score=score, reason=reason))

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored

    def _build_reason(self, prefs: UserPreferences, c: CandidateRestaurant) -> str:
        parts = []
        if c.rating: parts.append(f"rated {c.rating}/5")
        if c.approx_cost_for_two: parts.append(f"₹{c.approx_cost_for_two} for two")
        if any(cu.lower() in [x.lower() for x in c.cuisines] for cu in prefs.cuisines):
            parts.append("matches your cuisine preference")
        
        return f"{c.name} is a great choice, " + "; ".join(parts)


__all__ = ["LLMOrchestrator"]
