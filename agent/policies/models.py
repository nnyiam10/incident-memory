import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")
REASONING_MODEL = os.getenv("MODEL_REASONING", "openai/gpt-5-mini")
EXTRACTION_MODEL = os.getenv("MODEL_EXTRACTION", "openai/gpt-5-mini")


def model_client() -> OpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is required. Add the hackathon OpenRouter key to .env."
        )
    return OpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        default_headers={"X-Title": "Incident Memory"},
    )
