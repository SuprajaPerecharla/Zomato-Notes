"""
algorithms.py — Part 2: hand-written sort and search algorithms.

Functions
---------
insertion_sort(notes, key)          — sort a list of Note objects in-place
binary_search_by_id(notes, target)  — O(log n) search on a sorted-by-id list
binary_search_by_title(notes, q)    — O(log n) prefix search on sorted-by-title list
linear_search(notes, query)         — O(n) full-text scan across title + body + tags

All functions operate on plain Python lists of Note ORM objects.
No third-party search/sort library is used.
"""

from __future__ import annotations

import re
from typing import List, Optional, Callable, Any

from models import Note


# ---------------------------------------------------------------------------
# Insertion Sort
# ---------------------------------------------------------------------------

def insertion_sort(notes: List[Note], key: Callable[[Note], Any], reverse: bool = False) -> List[Note]:
    """
    Sort *notes* in-place using insertion sort.

    Parameters
    ----------
    notes   : list of Note ORM objects (mutated in-place)
    key     : callable that extracts the sort key from a Note
    reverse : if True, sort descending

    Returns the same list (sorted in-place) for convenience.

    Complexity: O(n²) time, O(1) extra space.
    """
    for i in range(1, len(notes)):
        current = notes[i]
        current_key = key(current)
        j = i - 1
        if not reverse:
            while j >= 0 and key(notes[j]) > current_key:
                notes[j + 1] = notes[j]
                j -= 1
        else:
            while j >= 0 and key(notes[j]) < current_key:
                notes[j + 1] = notes[j]
                j -= 1
        notes[j + 1] = current
    return notes


# ---------------------------------------------------------------------------
# Binary Search by ID
# ---------------------------------------------------------------------------

def binary_search_by_id(notes: List[Note], target_id: int) -> Optional[Note]:
    """
    Binary search for a Note with id == target_id.

    Precondition: *notes* must be sorted ascending by .id.
    Returns the matching Note, or None if not found.

    Complexity: O(log n) time.
    """
    lo, hi = 0, len(notes) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        mid_id = notes[mid].id
        if mid_id == target_id:
            return notes[mid]
        elif mid_id < target_id:
            lo = mid + 1
        else:
            hi = mid - 1
    return None


# ---------------------------------------------------------------------------
# Binary Search by Title (prefix)
# ---------------------------------------------------------------------------

def binary_search_by_title(notes: List[Note], query: str) -> List[Note]:
    """
    Find all notes whose normalised title starts with the normalised *query*.

    Precondition: *notes* must be sorted ascending by .title (case-insensitive).
    Uses binary search to locate the leftmost match, then scans forward.

    Returns a list of matching Note objects (may be empty).
    Complexity: O(log n + k) where k is the number of matches.
    """
    target = query.strip().lower()
    if not target:
        return []

    lo, hi = 0, len(notes) - 1
    # Find leftmost index where title >= target
    left = len(notes)
    while lo <= hi:
        mid = (lo + hi) // 2
        if notes[mid].title.lower() >= target:
            left = mid
            hi = mid - 1
        else:
            lo = mid + 1

    # Scan forward collecting all prefix matches
    results = []
    i = left
    while i < len(notes) and notes[i].title.lower().startswith(target):
        results.append(notes[i])
        i += 1
    return results


# ---------------------------------------------------------------------------
# Linear Search (full-text)
# ---------------------------------------------------------------------------

def linear_search(notes: List[Note], query: str) -> List[Note]:
    """
    O(n) scan — returns all notes where *query* appears (case-insensitive) in
    the title, body, or tags.

    No sorting assumption required.
    Returns matches in the original list order.
    """
    if not query:
        return []
    needle = query.strip().lower()
    results = []
    for note in notes:
        haystack = f"{note.title} {note.content} {note.tag}".lower()
        if needle in haystack:
            results.append(note)
    return results


# ---------------------------------------------------------------------------
# Tag quick-jump
# ---------------------------------------------------------------------------

def tag_quick_jump(notes: List[Note], tag_name: str) -> List[Note]:
    """
    Return all notes whose tag field exactly matches *tag_name*,
    sorted by created_at descending.  O(n) linear scan.
    """
    target = tag_name.strip().lower()
    matched = [n for n in notes if (n.tag or "").strip().lower() == target]
    matched.sort(key=lambda n: n.created_at, reverse=True)
    return matched


# ---------------------------------------------------------------------------
# Convenience: ranked_search (ties together the algorithms above)
# ---------------------------------------------------------------------------

def ranked_keyword_search(notes: List[Note], query: str, top_k: int = 20) -> List[tuple]:
    """
    BM25-inspired keyword ranking built on top of the hand-written primitives.

    Pipeline
    --------
    1. Exact title match via linear scan → score 1.0
    2. Prefix title match via binary search on title-sorted copy → score 0.9
    3. Full-text linear search → BM25-style TF score

    Returns list of (Note, score, match_type) sorted descending by score.
    """
    import math

    _STOP = frozenset(
        "a an the is are was were be been have has had do does did will would "
        "shall should may might can could not and or but if in on at to for of "
        "with by from as this that it its we they you he she i am".split()
    )

    def tokenise(text: str) -> List[str]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        return [t for t in tokens if t not in _STOP and len(t) > 1]

    query_tokens = tokenise(query)
    if not query_tokens:
        return []

    results: List[tuple] = []
    seen_ids: set = set()

    # 1. Exact title match
    for note in notes:
        if note.title.strip().lower() == query.strip().lower():
            results.append((note, 1.0, "exact_title"))
            seen_ids.add(note.id)
            break

    # 2. Prefix title match (binary search on sorted copy)
    title_sorted = sorted(notes, key=lambda n: n.title.lower())
    prefix_matches = binary_search_by_title(title_sorted, query)
    for note in prefix_matches:
        if note.id not in seen_ids:
            results.append((note, 0.9, "title_prefix"))
            seen_ids.add(note.id)

    # 3. BM25 keyword scoring on remaining notes
    remaining = [n for n in notes if n.id not in seen_ids]
    if remaining and query_tokens:
        # Build token frequency map
        N = len(remaining)
        df: dict = {}
        doc_tokens = []
        for note in remaining:
            tokens = tokenise(f"{note.title} {note.title} {note.title} {note.content} {note.tag}")
            doc_tokens.append(tokens)
            for term in set(tokens):
                df[term] = df.get(term, 0) + 1

        avg_len = sum(len(t) for t in doc_tokens) / N if N else 1
        K1, B = 1.5, 0.75

        scored = []
        # Build token frequency map — title weighted 3×, content weighted 1×, tag weighted 2×
        for note, tokens in zip(remaining, doc_tokens):
            tf_map: dict = {}
            for t in tokens:
                tf_map[t] = tf_map.get(t, 0) + 1
            score = 0.0
            doc_len = len(tokens)
            for term in query_tokens:
                if term not in tf_map:
                    continue
                f = tf_map[term]
                n_t = df.get(term, 0)
                idf = math.log((N - n_t + 0.5) / (n_t + 0.5) + 1)
                tf_score = (f * (K1 + 1)) / (f + K1 * (1 - B + B * doc_len / avg_len))
                score += idf * tf_score
            if score > 0:
                scored.append((note, score, "keyword"))

        if scored:
            max_s = max(s for _, s, _ in scored)
            for note, s, mt in scored:
                results.append((note, round(s / max_s, 4), mt))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]
