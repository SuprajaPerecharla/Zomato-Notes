"""
Notes CRUD router — /api/notes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas
from ..services import intelligence

router = APIRouter(prefix="/api/notes", tags=["notes"])


def _background_embed_and_autotag(db: Session, note_id: int):
    """Run after note creation: compute embedding."""
    from ..database import SessionLocal
    bg_db = SessionLocal()
    try:
        note = crud.get_note(bg_db, note_id)
        if note:
            intelligence.compute_and_store_embedding(bg_db, note)
    finally:
        bg_db.close()


@router.post("/", response_model=schemas.NoteRead, status_code=201)
async def create_note(
    payload: schemas.NoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    note = crud.create_note(db, payload)

    # Fire auto-tagger if tags were not provided
    if not payload.tags:
        suggested = await intelligence.auto_tag(note.title, note.body)
        if suggested:
            crud.set_note_tags(db, note, suggested)
            db.refresh(note)

    # Compute embedding in background (non-blocking)
    background_tasks.add_task(_background_embed_and_autotag, db, note.id)

    return note


@router.get("/", response_model=List[schemas.NoteRead])
def list_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    severity: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return crud.list_notes(db, skip=skip, limit=limit, severity=severity, tag=tag)


@router.get("/count")
def count_notes(
    severity: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return {"count": crud.count_notes(db, severity=severity, tag=tag)}


@router.get("/{note_id}", response_model=schemas.NoteRead)
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.put("/{note_id}", response_model=schemas.NoteRead)
def update_note(
    note_id: int,
    payload: schemas.NoteUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    note = crud.update_note(db, note_id, payload)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    # Re-compute embedding after update
    background_tasks.add_task(_background_embed_and_autotag, db, note.id)
    return note


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    if not crud.delete_note(db, note_id):
        raise HTTPException(status_code=404, detail="Note not found")


@router.post("/{note_id}/autotag", response_model=schemas.AutoTagResponse)
async def autotag_note(
    note_id: int,
    apply: bool = Query(False, description="Apply suggested tags to the note"),
    db: Session = Depends(get_db),
):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    suggested = await intelligence.auto_tag(note.title, note.body)
    if apply and suggested:
        crud.set_note_tags(db, note, suggested)

    return schemas.AutoTagResponse(suggested_tags=suggested, applied=apply and bool(suggested))
