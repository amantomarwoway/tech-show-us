"""
src/collectors/yt_metadata_collector.py
- Fetches title, description, tags, hashtags, transcript from YouTube
- Uses youtube-transcript-api (free, no key, no AI)
"""

import os
import re
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def fetch_transcript(video_id):
    """Fetch transcript from YouTube video (free, no key)."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try manual English
            try:
                t = transcript_list.find_manually_created_transcript(["en", "en-US", "en-GB"])
            except Exception:
                # Auto-generated fallback
                try:
                    t = transcript_list.find_generated_transcript(["en", "en-US", "en-GB"])
                except Exception:
                    # Any language → translate to English
                    t = next(iter(transcript_list))
                    t = t.translate("en")

            data = t.fetch()
            full_text = " ".join(seg["text"] for seg in data)

            # Clean
            full_text = re.sub(r'\[.*?\]', '', full_text)
            full_text = re.sub(r'\(.*?\)', '', full_text)
            full_text = re.sub(r'>>\s*', '', full_text)
            full_text = re.sub(r'\s+', ' ', full_text).strip()

            logger.info(f"Transcript fetched: {len(full_text)} chars")
            return full_text

        except (TranscriptsDisabled, NoTranscriptFound) as e:
            logger.info(f"Transcript not available: {e}")
            return None
        except Exception as e:
            logger.warning(f"Transcript error: {e}")
            return None
    except ImportError:
        logger.warning("youtube-transcript-api not installed")
        return None
    except Exception as e:
        logger.warning(f"Transcript fetch failed: {e}")
        return None


def extract_hashtags(description):
    """Extract hashtags from description."""
    if not description:
        return []
    tags = re.findall(r'#\w+', description)
    # Dedupe preserving order
    seen = set()
    unique = []
    for t in tags:
        if t.lower() not in seen:
            seen.add(t.lower())
            unique.append(t)
    return unique[:10]


def extract_keywords(text, top_n=15):
    """Simple keyword extraction (no AI)."""
    stopwords = {
        "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "must", "can",
        "to", "of", "in", "on", "at", "by", "for", "with", "about", "as",
        "into", "through", "during", "before", "after", "above", "below",
        "from", "up", "down", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "any", "both", "each", "few", "more", "most", "other",
        "some", "such", "no", "nor", "not", "only", "own", "same", "so",
        "than", "too", "very", "s", "t", "just", "don", "now", "i", "you",
        "he", "she", "it", "we", "they", "this", "that", "these", "those",
        "what", "which", "who", "whom", "your", "my", "his", "her", "our",
        "their", "its", "like", "get", "got", "go", "going", "one", "two",
        "know", "think", "want", "see", "make", "made", "way", "well",
        "said", "say", "says", "also", "just", "even", "still", "back",
    }
    words = re.findall(r'\b[a-z]{4,}\b', text.lower())
    freq = {}
    for w in words:
        if w in stopwords:
            continue
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: -x[1])
    return [w for w, _ in sorted_words[:top_n]]
