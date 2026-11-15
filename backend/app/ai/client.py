import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

# Loads backend/.env
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _get_client() -> OpenAI:
    key = os.getenv("LLM_API_KEY")
    if not key:
        raise RuntimeError("LLM_API_KEY is missing. Add it to backend/.env")
    return OpenAI(api_key=key, base_url=os.getenv("LLM_BASE_URL"))


def ask_llm(system: str, user: str, temperature: float = 0.2) -> str:
    model = os.getenv("LLM_MODEL")
    if not model:
        raise RuntimeError("LLM_MODEL is missing. Add it to backend/.env")

    response = _get_client().chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""