"""
Gemini client with quota-aware retries.

PRODUCTION LESSON (a real run exhausted its daily quota inside ONE script):
  * 503 "high demand" is transient — a patient backoff-retry on the SAME model
    genuinely can clear within seconds, so it gets one (5s, 10s, capped 20s).
  * 429 RESOURCE_EXHAUSTED means the free-tier DAILY quota (20 requests/day per
    model on the free tier) is gone. Retrying that model cannot help and every
    retry still burns an already-tiny budget, so it skips STRAIGHT to the
    fallback model with no wait.
  * Retry layers multiply (text x json x writer): keep every layer's count low.
    generate_text: 3 attempts/model; generate_json: 2; write_story: 1 retry.
"""
import json
import logging
import os
import re
import time

from src.config import (
    GEMINI_API_KEY_ENV,
    GEMINI_FALLBACK_MODEL,
    GEMINI_MAX_OUTPUT_TOKENS,
    GEMINI_PRIMARY_MODEL,
)

log = logging.getLogger(__name__)

_TRANSIENT_HINTS = ("503", "unavailable", "high demand")
_QUOTA_EXHAUSTED_HINTS = ("resource_exhausted", "exceeded your current quota", "429")


def _get_client():
    from google import genai

    api_key = os.environ.get(GEMINI_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"{GEMINI_API_KEY_ENV} environment variable is not set")
    return genai.Client(api_key=api_key)


def _is_quota_exhausted(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(h in msg for h in _QUOTA_EXHAUSTED_HINTS)


def _is_transient(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(h in msg for h in _TRANSIENT_HINTS)


def generate_text(
    prompt: str, *, temperature: float = 0.9, max_retries: int = 3, json_mode: bool = False
) -> str:
    """Primary model, then fallback model. Quota exhaustion skips a model at
    once; transient overload backs off and retries it. json_mode asks Gemini
    for strictly valid JSON output."""
    client = _get_client()
    config = {"temperature": temperature, "max_output_tokens": GEMINI_MAX_OUTPUT_TOKENS}
    if json_mode:
        config["response_mime_type"] = "application/json"
    last_err = None

    for model in (GEMINI_PRIMARY_MODEL, GEMINI_FALLBACK_MODEL):
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(model=model, contents=prompt, config=config)
                text = getattr(response, "text", None)
                if text:
                    return text
                raise ValueError("Empty response from Gemini")
            except Exception as e:
                last_err = e
                if _is_quota_exhausted(e):
                    log.warning("Gemini model %s quota exhausted — moving to fallback immediately: %s", model, e)
                    break
                if _is_transient(e) and attempt < max_retries - 1:
                    wait = min(20, 5 * (2 ** attempt))
                    log.warning("Gemini %s overloaded (attempt %d/%d): %s — retrying in %ds",
                                model, attempt + 1, max_retries, e, wait)
                    time.sleep(wait)
                    continue
                log.warning("Gemini model %s failed: %s", model, e)
                break

    raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")


def _parse_json(text: str):
    """Strict JSON first; then strip markdown fences; then the outermost {...}."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fenced = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    try:
        return json.loads(fenced)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start:end + 1])
    raise json.JSONDecodeError("no JSON object found", text, 0)


def generate_json(prompt: str, *, temperature: float = 0.8, max_retries: int = 2):
    """JSON from Gemini. Retries BOTH failure modes (total API failure and
    malformed JSON) — an earlier version only caught JSONDecodeError, so an
    API outage escaped on the first attempt and this loop never ran again."""
    last_err = None
    for attempt in range(max_retries):
        try:
            return _parse_json(generate_text(prompt, temperature=temperature, json_mode=True))
        except Exception as e:
            last_err = e
            log.warning("generate_json attempt %d/%d failed: %s", attempt + 1, max_retries, e)
            if attempt < max_retries - 1 and isinstance(e, RuntimeError):
                time.sleep(10)  # a full API failure: give the service a moment
    raise RuntimeError(f"generate_json failed after {max_retries} attempts: {last_err}")
