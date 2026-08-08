"""
Ranking Engine — hand-written algorithms, no third-party search library.

Three modes
-----------
1. exact_title  – O(n) linear scan; normalised string equality; score = 1.0
2. keyword      – custom TF-IDF-style scoring over title + body tokens
3. tag_jump     – returns all notes that carry a specific tag, sorted by recency

Design notes
------------
* No external search engine (Elasticsearch, Whoosh, etc.) is used.
* Tokenisation, IDF weights, and BM25-style scoring are implemented from scratch.
* The ranker operates on plain Python lists; callers pass ORM objects.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from ..models import Note


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did "
    "will would shall should may might can could not and or but if in "
    "on at to for of with by from as this that it its we they you he she "
    "i am all any each every some such no nor so yet both either neither "
    "than though while about above after before between during into through "
    "under over also just very too more most less least one two three".split()
)


def _tokenise(text: str) -> List[str]:
    """Lowercase, split on non-alphanumeric, drop stop-words and short tokens."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


# ---------------------------------------------------------------------------
# Exact-title lookup
# ---------------------------------------------------------------------------

def exact_title_search(notes: List[Note], query: str) -> Optional[Note]:
    """
    O(n) scan — returns the first note whose normalised title exactly matches
    the normalised query, or None.
    """
    target = _normalise(query)
    for note in notes:
        if _normalise(note.title) == target:
            return note
    return None


# ---------------------------------------------------------------------------
# Keyword ranking (hand-written BM25-inspired)
# ---------------------------------------------------------------------------

# BM25 parameters
_K1 = 1.5   # term frequency saturation
_B = 0.75   # length normalisation factor


@dataclass
class _DocStats:
    note: Note
    tokens: List[str]
    tf: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        for t in self.tokens:
            self.tf[t] = self.tf.get(t, 0) + 1


def _build_index(notes: List[Note]) -> Tuple[List[_DocStats], Dict[str, int], float]:
    """
    Returns:
        docs       – per-document stats
        df         – document frequency per term
        avg_len    – average document token length
    """
    docs: List[_DocStats] = []
    df: Dict[str, int] = {}

    for note in notes:
        # Weight: title tokens appear 3× to boost title matches
        tokens = _tokenise(note.title) * 3 + _tokenise(note.body)
        for tag in note.tags:
            tokens += _tokenise(tag.name) * 2
        ds = _DocStats(note=note, tokens=tokens)
        docs.append(ds)
        for term in set(ds.tf.keys()):
            df[term] = df.get(term, 0) + 1

    avg_len = (sum(len(d.tokens) for d in docs) / len(docs)) if docs else 1.0
    return docs, df, avg_len


def keyword_search(
    notes: List[Note],
    query: str,
    top_k: int = 20,
) -> List[Tuple[Note, float]]:
    """
    BM25-inspired keyword ranking.

    Returns a list of (Note, normalised_score) pairs sorted descending.
    Score is normalised to [0, 1] by dividing by the maximum raw score.
    """
    if not notes:
        return []

    query_tokens = _tokenise(query)
    if not query_tokens:
        return []

    docs, df, avg_len = _build_index(notes)
    N = len(docs)

    raw_scores: List[Tuple[Note, float]] = []

    for ds in docs:
        score = 0.0
        doc_len = len(ds.tokens)
        for term in query_tokens:
            if term not in ds.tf:
                continue
            f = ds.tf[term]
            n_t = df.get(term, 0)
            # IDF (add-1 smoothing)
            idf = math.log((N - n_t + 0.5) / (n_t + 0.5) + 1)
            # BM25 TF component
            tf_score = (f * (_K1 + 1)) / (f + _K1 * (1 - _B + _B * doc_len / avg_len))
            score += idf * tf_score

        if score > 0:
            raw_scores.append((ds.note, score))

    if not raw_scores:
        return []

    # Normalise scores
    max_score = max(s for _, s in raw_scores)
    normalised = [(note, s / max_score) for note, s in raw_scores]

    # Sort descending and return top_k
    normalised.sort(key=lambda x: x[1], reverse=True)
    return normalised[:top_k]


# ---------------------------------------------------------------------------
# Recency boost (optional post-processing)
# ---------------------------------------------------------------------------

def _recency_factor(note: Note, now: datetime, half_life_days: float = 30.0) -> float:
    """
    Exponential decay: factor = 0.5^(age_days / half_life_days).
    A note created today has factor ≈ 1.0; one from 30 days ago ≈ 0.5.
    """
    created = note.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    age_days = (now - created).total_seconds() / 86400
    return 0.5 ** (age_days / half_life_days)


def ranked_search(
    notes: List[Note],
    query: str,
    top_k: int = 20,
    recency_weight: float = 0.15,
) -> List[Tuple[Note, float, str]]:
    """
    Unified ranking pipeline:
      1. Check for exact title match → return it first with score 1.0
      2. Run keyword (BM25) ranking
      3. Blend with a recency signal

    Returns list of (Note, blended_score, match_type).
    """
    results: List[Tuple[Note, float, str]] = []
    now = datetime.now(timezone.utc)

    # 1. Exact title match
    exact = exact_title_search(notes, query)
    if exact:
        results.append((exact, 1.0, "exact_title"))
        # Remove from keyword pool to avoid duplicate
        remaining = [n for n in notes if n.id != exact.id]
    else:
        remaining = notes

    # 2. Keyword BM25
    kw_results = keyword_search(remaining, query, top_k=top_k)

    for note, kw_score in kw_results:
        rec = _recency_factor(note, now)
        blended = (1 - recency_weight) * kw_score + recency_weight * rec
        results.append((note, blended, "keyword"))

    # Re-sort (exact match is already at the top with score 1.0, but be safe)
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


# ---------------------------------------------------------------------------
# Tag quick-jump
# ---------------------------------------------------------------------------

def tag_quick_jump(notes: List[Note], tag_name: str) -> List[Note]:
    """
    Returns all notes carrying the given tag, sorted by created_at descending.
    O(n × avg_tags_per_note) — no index required.
    """
    target = tag_name.strip().lower().replace(" ", "-")
    matched = [n for n in notes if any(t.name == target for t in n.tags)]
    matched.sort(key=lambda n: n.created_at, reverse=True)
    return matched
