"""Groq-only LLM integration."""

from __future__ import annotations

from typing import Any


class GroqClientError(RuntimeError):
    """An actionable Groq request or response error."""


def _client(api_key: str) -> Any:
    try:
        from groq import Groq
    except ImportError as exc:
        raise GroqClientError("The Groq package is not installed. Run pip install -r requirements.txt.") from exc
    return Groq(api_key=api_key)


def generate(prompt: str, api_key: str, model: str = "llama-3.1-8b-instant") -> str:
    if not api_key.strip():
        raise GroqClientError("Add a Groq API key in Settings before generating test cases.")
    try:
        response = _client(api_key).chat.completions.create(
            model=model,
            temperature=0.1,
            max_tokens=5000,
            messages=[
                {"role": "system", "content": "You generate precise QA test cases and follow the supplied format exactly."},
                {"role": "user", "content": prompt},
            ],
        )
        content = response.choices[0].message.content or ""
    except Exception as exc:
        raise GroqClientError(f"Groq generation failed: {exc}") from exc
    if not content.strip():
        raise GroqClientError("Groq returned an empty response.")
    return content.strip()


def test_connection(api_key: str, model: str = "llama-3.1-8b-instant") -> None:
    generate("Reply with exactly: CONNECTION_OK", api_key, model=model)