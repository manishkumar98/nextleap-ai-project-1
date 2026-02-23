"""
Phase 3 – LLM orchestration using Groq.

This package is responsible for:
- Representing user preferences and candidate restaurants in a structured way.
- Parsing user queries into structured preferences (LLM-backed in future).
- Re-ranking candidate restaurants and generating natural-language reasons.

The actual HTTP calls to Groq are encapsulated so they can be swapped or
mocked easily in tests. Tests mainly cover the deterministic fallback logic.
"""

