"""
Shared Gemini client: primary model with automatic fallback to a secondary
model on quota/availability errors (429/403/503), plus a JSON-mode helper
that strips markdown fences defensively before parsing.
"""
import json
import logging
import os
import time

from src.config import GEMINI_FALLBACK_MODEL, GEMINI_PRIMARY_MODEL

log = logging.getLogger(__name__)

_RETRYABLE_STATUS_HINTS = ("429", "403", "503", "quota", "unavailable", "rate limit")


def _get_client():
    from google import genai

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")
    return genai.Client(api_key=api_key)


def _is_retryable(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(hint in msg for hint in _RETRYABLE_STATUS_HINTS)


def generate_text(prompt: str, *, temperature: float = 0.9, max_retries: int = 3) -> str:
    """Call Gemini primary, falling back to secondary model on retryable errors."""
    client = _get_client()
    models_to_try = [GEMINI_PRIMARY_MODEL, GEMINI_FALLBACK_MODEL]
    last_err = None

    for model in models_to_try:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"temperature": temperature},
                )
                text = getattr(response, "text", None)
                if text:
                    return text
                raise ValueError("Empty response from Gemini")
            except Exception as e:
                last_err = e
                if _is_retryable(e) and attempt < max_retries - 1:
                    wait = 2 ** attempt
                    log.warning(
                        "Gemini call failed on %s (attempt %d/%d): %s — retrying in %ds",
                        model, attempt + 1, max_retries, e, wait,
                    )
                    time.sleep(wait)
                    continue
                log.warning("Gemini model %s failed: %s", model, e)
                break  # move to next model in the fallback chain

    raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def generate_json(prompt: str, *, temperature: float = 0.8, max_retries: int = 3):
    """Generate JSON content from Gemini. Prompt should explicitly ask for JSON only."""
    full_prompt = prompt.strip() + "\n\nRespond with ONLY valid JSON. No markdown fences."
    last_err = None
    for attempt in range(max_retries):
        raw = generate_text(full_prompt, temperature=temperature, max_retries=1)
        cleaned = _strip_fences(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            last_err = e
            log.warning("JSON parse failed (attempt %d/%d): %s", attempt + 1, max_retries, e)
            time.sleep(1)
    raise ValueError(f"Could not parse JSON from Gemini after {max_retries} attempts: {last_err}")
