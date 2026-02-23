import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load environment variables for Groq configuration.
# We first try a .env inside the virtualenv (your current setup),
# then fall back to a project-root .env if present.
load_dotenv(".venv/.env")
load_dotenv()


@dataclass
class LLMSettings:
    """
    Configuration for Phase 3 LLM orchestration.
    """

    # Groq configuration
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    groq_base_url: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

    # Fallback behaviour
    use_llm_by_default: bool = bool(int(os.getenv("USE_LLM_BY_DEFAULT", "0")))


settings = LLMSettings()


