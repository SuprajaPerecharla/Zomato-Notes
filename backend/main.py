"""
main.py — Zomato Notes FastAPI application.

All endpoints in one file:

  Part 1 — Users
    POST   /users/               create user
    GET    /users/               list users
    GET    /users/{id}           get user

  Part 1 — Notes CRUD
    POST   /notes/               create note
    GET    /notes/               list notes (filter by tag / owner_id / search)
    GET    /notes/{id}           get note
    PUT    /notes/{id}           update note
    DELETE /notes/{id}           delete note
    POST   /notes/bulk-import/json  bulk import
    GET    /notes/report/stats   reporting stats

  Part 2 — Ranking / Search
    GET    /search/              unified search (keyword | semantic | auto)
    GET    /search/tag/{tag}     tag quick-jump
    GET    /search/sort          insertion-sort demo
    GET    /search/by-id/{id}    binary-search demo

  Part 3 — AI
    POST   /ai/ask/{note_id}     ask a question about a note
    POST   /ai/autotag/{note_id} suggest / apply a tag
    POST   /ai/summarise/{id}    one-sentence summary
    POST   /ai/classify          predict tag for raw text
    POST   /ai/runbook/{id}      next-action suggestion

  Meta
    GET    /health
    GET    /tags
"""

from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, init_db
import crud
import schemas
import algorithms
import ai_service
import semantic_search as sem

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Zomato Notes API …")
    init_db()
    sem.warmup()
    logger.info("Ready.")
    yield
    logger.info("Shutting down.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Zomato Notes API",
    description="Personal notes manager — on-call knowledge base.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend — mount at /app so API routes at /notes/, /users/, etc. are never shadowed
_FRONTEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.isdir(_FRONTEND):
    app.mount("/app", StaticFiles(directory=_FRONTEND, html=True), name="frontend")

    @app.get("/", include_in_schema=False)
    def root_redirect():
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/app/")


# ---------------------------------------------------------------------------
# Background embedding
# ---------------------------------------------------------------------------

def _bg_embed(note_id: int):
    from database import SessionLocal
    db = SessionLocal()
    try:
        note = crud.get_note(db, note_id)
        if note:
            sem.compute_and_store(db, note)
    finally:
        db.close()


def _read(note) -> schemas.NoteRead:
    return schemas.NoteRead.from_orm_note(note)


# ===========================================================================
# Users
# ===========================================================================

@app.post("/users/", response_model=schemas.UserRead, status_code=201, tags=["users"])
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    return crud.create_user(db, payload)


@app.get("/users/", response_model=List[schemas.UserRead], tags=["users"])
def list_users(db: Session = Depends(get_db)):
    return crud.list_users(db)


@app.get("/users/{user_id}", response_model=schemas.UserRead, tags=["users"])
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ===========================================================================
# Notes CRUD
# ===========================================================================

@app.post("/notes/", response_model=schemas.NoteRead, status_code=201, tags=["notes"])
async def create_note(
    payload: schemas.NoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create a note.
    If *tag* is empty the AI auto-tagger fires (requires OPENAI_API_KEY).
    Embedding is computed asynchronously.
    """
    note = crud.create_note(db, payload)
    if not note.tag:
        suggested = await ai_service.suggest_tag(note.title, note.content)
        if suggested:
            crud.set_note_tag(db, note, suggested)
    background_tasks.add_task(_bg_embed, note.id)
    return _read(note)


@app.get("/notes/report/stats", tags=["notes"])
def note_stats(db: Session = Depends(get_db)):
    """Reporting: total count, notes per tag, recent notes, daily activity."""
    return {
        "total":              crud.count_notes(db),
        "by_tag":             crud.notes_per_tag(db),
        "recent":             [_read(n) for n in crud.recent_notes(db, 5)],
        "top_tags":           crud.top_tags(db, 10),
        "created_last_7days": crud.notes_created_per_day(db, 7),
    }


@app.get("/notes/", response_model=List[schemas.NoteRead], tags=["notes"])
def list_notes(
    skip:     int           = Query(0,   ge=0),
    limit:    int           = Query(50,  ge=1, le=200),
    tag:      Optional[str] = Query(None, description="Filter by exact tag"),
    owner_id: Optional[int] = Query(None),
    search:   Optional[str] = Query(None, description="Full-text search in title/content"),
    db: Session = Depends(get_db),
):
    notes = crud.list_notes(db, skip=skip, limit=limit,
                            tag=tag, owner_id=owner_id, search=search)
    return [_read(n) for n in notes]


@app.get("/notes/{note_id}", response_model=schemas.NoteRead, tags=["notes"])
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return _read(note)


@app.put("/notes/{note_id}", response_model=schemas.NoteRead, tags=["notes"])
def update_note(
    note_id: int,
    payload: schemas.NoteUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    note = crud.update_note(db, note_id, payload)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    background_tasks.add_task(_bg_embed, note.id)
    return _read(note)


@app.delete("/notes/{note_id}", status_code=204, tags=["notes"])
def delete_note(note_id: int, db: Session = Depends(get_db)):
    if not crud.delete_note(db, note_id):
        raise HTTPException(status_code=404, detail="Note not found")


class BulkImportBody(BaseModel):
    lines:       List[str]
    default_tag: Optional[str] = "imported"


@app.post("/notes/bulk-import/json",
          response_model=schemas.BulkImportResponse, tags=["notes"])
def bulk_import_json(payload: BulkImportBody, db: Session = Depends(get_db)):
    result = crud.bulk_import_notes(db, payload.lines, payload.default_tag or "imported")
    return schemas.BulkImportResponse(
        imported=result["imported"],
        skipped=result["skipped"],
        notes=[_read(n) for n in result["notes"]],
    )


# ===========================================================================
# Tags
# ===========================================================================

@app.get("/tags", tags=["tags"])
def list_tags(db: Session = Depends(get_db)):
    """All distinct tags with usage counts."""
    return crud.top_tags(db, n=200)


# ===========================================================================
# Part 2 — Ranking / Search
# ===========================================================================

@app.get("/search/", response_model=schemas.SearchResponse, tags=["search"])
def search_notes(
    q:     str = Query(..., min_length=1),
    mode:  str = Query("auto", description="keyword | semantic | auto"),
    top_k: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Unified search.
    - keyword  — BM25 + exact-title + prefix (always available)
    - semantic — cosine similarity over embeddings
    - auto     — keyword + semantic merged
    """
    all_notes = crud.get_all_notes(db)
    results: List[schemas.SearchResult] = []

    if mode in ("keyword", "auto"):
        raw = algorithms.ranked_keyword_search(all_notes, q, top_k=top_k)
        seen_ids: set = set()
        for note, score, match_type in raw:
            results.append(schemas.SearchResult(note=_read(note), score=score, match_type=match_type))
            seen_ids.add(note.id)

        if mode == "auto":
            for note, sim in sem.semantic_search(db, q, top_k=top_k):
                if note.id not in seen_ids:
                    results.append(schemas.SearchResult(note=_read(note), score=sim, match_type="semantic"))
                    seen_ids.add(note.id)
            results.sort(key=lambda r: r.score, reverse=True)
            results = results[:top_k]

    elif mode == "semantic":
        results = [
            schemas.SearchResult(note=_read(n), score=s, match_type="semantic")
            for n, s in sem.semantic_search(db, q, top_k=top_k)
        ]
    else:
        raise HTTPException(status_code=400, detail=f"Unknown mode '{mode}'")

    return schemas.SearchResponse(query=q, results=results, total=len(results))


@app.get("/search/tag/{tag_name}", tags=["search"])
def tag_quick_jump(tag_name: str, db: Session = Depends(get_db)):
    """Tag quick-jump using hand-written linear scan."""
    all_notes = crud.get_all_notes(db)
    matched = algorithms.tag_quick_jump(all_notes, tag_name)
    return {"tag": tag_name, "notes": [_read(n) for n in matched], "total": len(matched)}


@app.get("/search/sort", tags=["search"])
def sorted_notes(
    sort_by: str = Query("created_at", description="created_at | title | tag"),
    order:   str = Query("desc", description="asc | desc"),
    db: Session = Depends(get_db),
):
    """Insertion-sort demo endpoint."""
    all_notes = crud.get_all_notes(db)
    key_map = {
        "created_at": lambda n: n.created_at,
        "title":      lambda n: n.title.lower(),
        "tag":        lambda n: n.tag or "",
    }
    if sort_by not in key_map:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {list(key_map)}")
    reverse = order.lower() == "desc"
    return [_read(n) for n in algorithms.insertion_sort(list(all_notes), key=key_map[sort_by], reverse=reverse)]


@app.get("/search/by-id/{note_id}", tags=["search"])
def search_by_id(note_id: int, db: Session = Depends(get_db)):
    """Binary-search by ID demo."""
    all_notes = crud.get_all_notes(db)
    id_sorted = algorithms.insertion_sort(list(all_notes), key=lambda n: n.id)
    found = algorithms.binary_search_by_id(id_sorted, note_id)
    if not found:
        raise HTTPException(status_code=404, detail="Note not found")
    return _read(found)


# ===========================================================================
# Part 3 — AI
# ===========================================================================

@app.post("/ai/ask/{note_id}", response_model=schemas.AIResponse, tags=["ai"])
async def ai_ask(
    note_id:  int,
    question: str = Query(..., min_length=3),
    db: Session = Depends(get_db),
):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    answer = await ai_service.get_ai_response(note, question)
    return schemas.AIResponse(answer=answer, note_id=note_id, model_used=ai_service.OPENAI_MODEL)


@app.post("/ai/autotag/{note_id}", response_model=schemas.AutoTagResponse, tags=["ai"])
async def ai_autotag(
    note_id: int,
    apply:   bool = Query(False),
    db: Session = Depends(get_db),
):
    """Suggest a tag for the note. Optionally apply it."""
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    suggested = await ai_service.suggest_tag(note.title, note.content)
    if apply and suggested:
        crud.set_note_tag(db, note, suggested)
    return schemas.AutoTagResponse(suggested_tag=suggested or "", applied=apply and bool(suggested))


@app.post("/ai/summarise/{note_id}", tags=["ai"])
async def ai_summarise(note_id: int, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"note_id": note_id, "summary": await ai_service.summarise_note(note)}


class ClassifyRequest(BaseModel):
    title:   str
    content: str


@app.post("/ai/classify", tags=["ai"])
async def ai_classify(payload: ClassifyRequest):
    """Predict the best tag for a note given its title and content."""
    tag = await ai_service.classify_tag(payload.title, payload.content)
    return {"predicted_tag": tag, "model_used": ai_service.OPENAI_MODEL}


@app.post("/ai/runbook/{note_id}", tags=["ai"])
async def ai_runbook(note_id: int, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    step = await ai_service.generate_next_action(note)
    return {"note_id": note_id, "next_action": step}


# ===========================================================================
# Meta
# ===========================================================================

@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "service": "zomato-notes", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
