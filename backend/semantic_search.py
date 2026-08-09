"""
semantic_search.py — Part 3: dense-vector semantic search.

Uses sentence-transformers (all-MiniLM-L6-v2) to encode notes into
384-dimensional unit-norm vectors.  Cosine similarity is computed with
plain numpy — no vector database required.

Embeddings are stored as JSON text in Note.embedding so they survive
application restarts without recomputation.

Public API
----------
warmup()                        — load model at startup (call once)
embed_text(text)                — encode a string → List[float] | None
compute_and_store(db, note)     — embed a note and persist it
semantic_search(db, query, k)   — return top-k notes by cosine similarity
"""

from __future__ import annotations

import json
import logging
import os
from typing import List, Optional, Tuple

import numpy as np
from sqlalchemy.orm import Session

import crud
from models import Note

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Module-level singleton — loaded once at startup
_embedder = None   # SentenceTransformer instance or False (unavailable sentinel)


# ---------------------------------------------------------------------------
# Model lifecycle
# ---------------------------------------------------------------------------

def warmup() -> None:
    """
    Load the sentence-transformer model once in the main thread before any
    concurrent requests arrive.  Forces CPU to avoid MPS hang on macOS / Python 3.14.
    """
    global _embedder
    if _embedder is not None:
        return
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        _embedder = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
        logger.info("Semantic search model loaded: %s (cpu)", EMBEDDING_MODEL)
    except Exception as exc:
        logger.warning("Could not load embedding model (%s): %s", EMBEDDING_MODEL, exc)
        _embedder = False


def _get_embedder():
    return _embedder if _embedder not in (None, False) else None


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def _note_text(note: Note) -> str:
    """Concatenate note fields into a single string for embedding."""
    return f"{note.title} {note.content} {note.tag}".strip()


def embed_text(text: str) -> Optional[List[float]]:
    """
    Encode *text* into a unit-norm embedding vector.
    Returns None if the model is unavailable.
    """
    embedder = _get_embedder()
    if embedder is None:
        return None
    try:
        vec = embedder.encode(text, normalize_embeddings=True)
        return vec.tolist()
    except Exception as exc:
        logger.warning("embed_text failed: %s", exc)
        return None


def compute_and_store(db: Session, note: Note) -> bool:
    """
    Compute the embedding for *note* and persist it to the database.
    Returns True on success, False if the model is unavailable.
    """
    vec = embed_text(_note_text(note))
    if vec is None:
        return False
    crud.update_note_embedding(db, note.id, json.dumps(vec))
    return True


# ---------------------------------------------------------------------------
# Cosine similarity (plain numpy)
# ---------------------------------------------------------------------------

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """
    Cosine similarity between two pre-normalised vectors.
    Both vectors are assumed to be unit-norm (from SentenceTransformer
    with normalize_embeddings=True), so dot product == cosine similarity.
    Clamps to [-1, 1] to guard against floating-point noise.
    """
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    dot = float(np.dot(va, vb))
    return max(-1.0, min(1.0, dot))


# ---------------------------------------------------------------------------
# Semantic search
# ---------------------------------------------------------------------------

def semantic_search(
    db: Session,
    query: str,
    top_k: int = 10,
    threshold: float = 0.25,
) -> List[Tuple[Note, float]]:
    """
    Encode *query* and rank all notes with stored embeddings by cosine similarity.

    Parameters
    ----------
    db        : SQLAlchemy session
    query     : natural-language search string
    top_k     : maximum results to return
    threshold : minimum similarity score to include in results

    Returns a list of (Note, similarity_score) sorted descending.
    Notes without a stored embedding are skipped silently.
    """
    query_vec = embed_text(query)
    if query_vec is None:
        logger.warning("Semantic search unavailable — model not loaded.")
        return []

    notes = crud.get_all_notes_with_embeddings(db)
    scored: List[Tuple[Note, float]] = []

    for note in notes:
        try:
            stored_vec = json.loads(note.embedding)
            sim = _cosine_similarity(query_vec, stored_vec)
            if sim >= threshold:
                scored.append((note, round(sim, 4)))
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            logger.debug("Bad embedding for note %d: %s", note.id, exc)

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
