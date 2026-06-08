"""
openrouter_client.py — Thin OpenRouter wrapper (OpenAI-compatible).

One helper used by every LLM step. OpenRouter routes a single API key to many
models (Gemini, Grok, ...). Append ":online" to a model id to enable web search.
"""

import logging

from openai import OpenAI

import config

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if not config.OPENROUTER_API_KEY:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Get a key at https://openrouter.ai/keys"
        )
    if _client is None:
        _client = OpenAI(
            base_url=config.OPENROUTER_BASE_URL,
            api_key=config.OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": config.OPENROUTER_REFERER,
                "X-Title": config.OPENROUTER_TITLE,
            },
        )
    return _client


def chat(model: str, system: str, user: str,
         json_mode: bool = False, temperature: float = 0.4,
         max_tokens: int = 4096) -> str:
    """Single chat completion. Returns the raw assistant text."""
    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        resp = _get_client().chat.completions.create(**kwargs)
    except Exception as exc:
        raise RuntimeError(f"OpenRouter call failed ({model}): {exc}") from exc

    content = resp.choices[0].message.content or ""
    return content.strip()
