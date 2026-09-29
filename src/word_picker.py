"""
Picks a fresh word for the week via Gemini, excluding already-used words
(exact match) and semantically similar ones (embedding cosine similarity).
Falls back to a static reserve list if Gemini fails repeatedly.
"""
import json
import logging
import random

from src.config import (
    EMBEDDING_MODEL,
    MAX_RECENT_WORDS_FOR_PROMPT,
    RESERVE_WORDS,
    SEMANTIC_DEDUP_THRESHOLD,
)
from src.database import get_all_used_words, is_word_used
from src.llm_client import generate_json

log = logging.getLogger(__name__)

WORD_PICK_PROMPT = """You are a psychology-and-etymology content strategist for a
YouTube channel called "WordsThatSpeaks". Each episode picks ONE word that has
real psychological depth (an emotion, trait, or concept — not a plain object
noun) and can support a 5-10 minute mystery/suspense/thriller-style
etymology + psychology story.

Words already used (do not repeat, do not pick close synonyms of these):
{used_words}

Return exactly 5 candidate words as a JSON array of objects, most promising
first, in this exact schema:
[
  {{"word": "ego", "richness_score": 9, "angle": "one-sentence psychological hook"}},
  ...
]
Rules:
- richness_score is 1-10, how much psychological/etymological depth the word has.
- Words must be single common English words, lowercase.
- No proper nouns. No repeats of the used list. No near-duplicates of used words.
- Return ONLY the JSON array, no markdown fences, no commentary.
"""


def _load_embedder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def _max_similarity(candidate: str, used_words: list[str], embedder) -> float:
    if not used_words:
        return 0.0
    import numpy as np

    vecs = embedder.encode([candidate] + used_words, normalize_embeddings=True)
    cand_vec, used_vecs = vecs[0], vecs[1:]
    sims = used_vecs @ cand_vec
    return float(np.max(sims))


def pick_word() -> dict:
    """Returns {"word": str, "angle": str, "richness_score": int}."""
    all_used = get_all_used_words()
    sample_used = (
        random.sample(all_used, MAX_RECENT_WORDS_FOR_PROMPT)
        if len(all_used) > MAX_RECENT_WORDS_FOR_PROMPT
        else all_used
    )

    try:
        prompt = WORD_PICK_PROMPT.format(used_words=", ".join(sample_used) or "(none yet)")
        candidates = generate_json(prompt)
        if not isinstance(candidates, list) or not candidates:
            raise ValueError("Gemini returned no candidates")
    except Exception as e:
        log.warning("Word-picker LLM call failed (%s); falling back to reserve list", e)
        candidates = [{"word": w, "richness_score": 5, "angle": ""} for w in RESERVE_WORDS]

    candidates.sort(key=lambda c: c.get("richness_score", 0), reverse=True)

    try:
        embedder = _load_embedder()
    except Exception as e:
        log.warning("Embedding model unavailable (%s); skipping semantic dedup", e)
        embedder = None

    for cand in candidates:
        word = str(cand.get("word", "")).strip().lower()
        if not word or is_word_used(word):
            continue
        if embedder is not None:
            try:
                sim = _max_similarity(word, all_used, embedder)
                if sim > SEMANTIC_DEDUP_THRESHOLD:
                    log.info("Rejecting '%s' — semantic similarity %.2f too high", word, sim)
                    continue
            except Exception as e:
                log.warning("Semantic similarity check failed (%s); accepting word anyway", e)
        return {
            "word": word,
            "angle": cand.get("angle", ""),
            "richness_score": cand.get("richness_score", 5),
        }

    # Absolute fallback: reserve words not yet used, ignoring semantic check.
    for word in RESERVE_WORDS:
        if not is_word_used(word):
            log.warning("All candidates exhausted; using reserve word '%s'", word)
            return {"word": word, "angle": "", "richness_score": 5}

    raise RuntimeError("No fresh word available — reserve list and Gemini candidates exhausted")
