from __future__ import annotations

from typing import List, Dict, Any

import json
import requests

from .config import settings


class GroqClient:
    """
    Minimal Groq client wrapper.

    This is intentionally very small; core orchestration logic is tested
    via deterministic fallbacks so unit tests do not rely on the network.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model
        self.base_url = base_url or settings.groq_base_url

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: List[Dict[str, str]], max_tokens: int = 512) -> str:
        """
        Call Groq chat completion API and return the assistant content.
        """
        if not self.is_configured():
            raise RuntimeError("GroqClient is not configured with an API key.")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        # OpenAI-compatible schema
        return data["choices"][0]["message"]["content"]


__all__ = ["GroqClient"]

