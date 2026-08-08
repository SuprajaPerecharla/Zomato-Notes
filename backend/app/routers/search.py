"""
Search & ranking router — /api/search

Exposes three search modes:
  GET /api/search?q=...&mode=keyword   → ranked keyword (BM25) results
  GET /api/search?q=...&mode=semantic  → semantic (embedding) results
  GET /api/search/tag/{tag}            → tag quick-jump
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas
from ..services import ranking, intelligence

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/", response_model=schemas.SearchResponse)
def search_notes(
    q: str = Query(..., min_length=1, description="Search query"),
    mode: str = Query("keyword", description="keyword | semantic | auto"),
    top_k: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Unified search endpoint.

    - mode=keyword  → hand-written BM25 ranking (always available)
    - mode=semantic → cosine similarity over stored embeddings
    - mode=auto     → tries semantic first; falls back to keyword if no embeddings
    """
    notes = crud.get_all_notes(db)

    if mode in ("keyword", "auto"):
        raw = ranking.ranked_search(notes, q, top_k=top_k)
        results = [
            schemas.SearchResult(
                note=schemas.NoteRead.model_validate(n),
                score=round(s, 4),
                match_type=mt,
            )
            for n, s, mt in raw
        ]

        # For "auto", try to augment with semantic if embeddings exist
        if mode == "auto":
            semantic_raw = intelligence.semantic_search(db, q, top_k=top_k)
            if semantic_raw:
                seen_ids = {r.note.id for r in results}
                for note, sim in semantic_raw:
                    if note.id not in seen_ids:
                        results.append(
                            schemas.SearchResult(
                                note=schemas.NoteRead.model_validate(note),
                                score=round(sim, 4),
                                match_type="semantic",
                            )
                        )
                        seen_ids.add(note.id)
                results.sort(key=lambda r: r.score, reverse=True)
                results = results[:top_k]

    elif mode == "semantic":
        semantic_raw = intelligence.semantic_search(db, q, top_k=top_k)
        results = [
            schemas.SearchResult(
                note=schemas.NoteRead.model_validate(n),
                score=round(s, 4),
                match_type="semantic",
            )
            for n, s in semantic_raw
        ]
    else:
        raise HTTPException(status_code=400, detail=f"Unknown mode: {mode!r}. Use keyword, semantic, or auto.")

    return schemas.SearchResponse(query=q, results=results, total=len(results))


@router.get("/tag/{tag_name}", response_model=schemas.TagJumpResult)
def tag_quick_jump(tag_name: str, db: Session = Depends(get_db)):
    """
    Returns all notes tagged with *tag_name*, sorted newest-first.
    Uses the hand-written tag_quick_jump algorithm from the ranking module.
    """
    all_notes = crud.get_all_notes(db)
    matched = ranking.tag_quick_jump(all_notes, tag_name)
    return schemas.TagJumpResult(
        tag=tag_name,
        notes=[schemas.NoteRead.model_validate(n) for n in matched],
        total=len(matched),
    )
