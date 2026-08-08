"""
Intelligence Layer — auto-tagging + semantic search.

Auto-tagger
-----------
* Calls OpenAI chat completions to suggest up to 5 tags for a note.
* Falls back gracefully (returns empty list) if the API key is missing or
  the call fails, so the app stays functional without credentials.

Semantic search
---------------
* Uses sentence-transformers (all-MiniLM-L6-v2 by default) to embed
  note text into dense vectors.
* Cosine similarity computed with plain numpy — no vector DB required.
* Embeddings are stored as JSON text in the notes table so they persist
  across restarts without a separate store.
"""

from __future__ import annotations

import json
import logging
from typing import List, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Note
from .. import crud

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy-load the sentence-transformer model so startup is fast
# ---------------------------------------------------------------------------

_embedder = None
_embedder_lock = None  # initialised in warmup_embedder


def _get_embedder():
    """Return the cached embedder, or None if unavailable."""
    return _embedder if _embedder is not False else None


def warmup_embedder() -> None:
    """
    Load the sentence-transformer model once at application startup.
    Called from main.py lifespan so it runs in the main thread before any
    concurrent requests arrive.  Forces CPU device to avoid MPS hang on
    Python 3.14 / macOS.
    """
    global _embedder
    if _embedder is not None:
        return
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        # Force CPU — MPS can hang on Python 3.14 free-threaded build on macOS
        _embedder = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")
        logger.info("Embedding model loaded at startup: %s (cpu)", settings.EMBEDDING_MODEL)
    except Exception as exc:
        logger.warning("Could not load embedding model: %s", exc)
        _embedder = False  # sentinel — don't retry on every call


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def _note_text(note: Note) -> str:
    tag_str = " ".join(t.name for t in note.tags) if note.tags else ""
    return f"{note.title} {note.body} {tag_str}".strip()


def embed_text(text: str) -> Optional[List[float]]:
    """Return a unit-norm embedding vector or None if unavailable."""
    embedder = _get_embedder()
    if embedder is None:
        return None
    try:
        vec = embedder.encode(text, normalize_embeddings=True)
        return vec.tolist()
    except Exception as exc:
        logger.warning("Embedding failed: %s", exc)
        return None


def compute_and_store_embedding(db: Session, note: Note) -> bool:
    """
    Compute the embedding for *note* and persist it.
    Returns True on success.
    """
    vec = embed_text(_note_text(note))
    if vec is None:
        return False
    crud.update_note_embedding(db, note.id, json.dumps(vec))
    return True


# ---------------------------------------------------------------------------
# Semantic search
# ---------------------------------------------------------------------------

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Pure numpy cosine similarity between two already-normalised vectors."""
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    dot = float(np.dot(va, vb))
    # Clamp to [-1, 1] to guard against fp noise
    return max(-1.0, min(1.0, dot))


def semantic_search(
    db: Session,
    query: str,
    top_k: int = 10,
    threshold: float = 0.25,
) -> List[Tuple[Note, float]]:
    """
    Embed *query* and return the top-k notes ranked by cosine similarity.

    Notes without a stored embedding are skipped.
    Results with similarity below *threshold* are excluded.

    Returns list of (Note, similarity_score) sorted descending.
    """
    query_vec = embed_text(query)
    if query_vec is None:
        logger.warning("Semantic search unavailable — embedding model not loaded.")
        return []

    notes = crud.get_all_notes_with_embeddings(db)
    scored: List[Tuple[Note, float]] = []

    for note in notes:
        try:
            stored_vec = json.loads(note.embedding)
            sim = _cosine_similarity(query_vec, stored_vec)
            if sim >= threshold:
                scored.append((note, sim))
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.debug("Could not decode embedding for note %d: %s", note.id, exc)

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]


# ---------------------------------------------------------------------------
# Auto-tagger
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are an expert on-call engineering assistant for Zomato.
Given an incident note, suggest up to 5 short, lowercase, hyphenated tags that would help engineers
find this note later. Focus on: service names, error types, infrastructure components, severity indicators,
and action types (e.g. rollback, hotfix, investigation).

Respond with ONLY a JSON array of strings, no explanation. Example:
["payment-service", "timeout", "database", "p0", "rollback"]"""


async def auto_tag(title: str, body: str) -> List[str]:
    """
    Call OpenAI to suggest tags for the given note content.
    Returns an empty list if the API key is not configured or the call fails.
    """
    if not settings.OPENAI_API_KEY:
        logger.info("OPENAI_API_KEY not set — auto-tagging disabled.")
        return []

    try:
        from openai import AsyncOpenAI  # type: ignore

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        user_content = f"Title: {title}\n\nBody: {body}"

        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
            max_tokens=128,
        )

        raw = response.choices[0].message.content.strip()
        tags = json.loads(raw)
        if isinstance(tags, list):
            # Sanitise: keep strings, lowercase, max 64 chars, max 5 tags
            return [
                str(t).strip().lower().replace(" ", "-")[:64]
                for t in tags
                if isinstance(t, str)
            ][:5]
        return []

    except Exception as exc:
        logger.warning("Auto-tag failed: %s", exc)
        return []
