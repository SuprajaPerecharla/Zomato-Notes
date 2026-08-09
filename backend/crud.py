"""
crud.py — CRUD operations + reporting queries.
Matches updated models: User(name/email/password) + Note(title/content/tag/owner_id).
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter

import models
import schemas


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

def create_user(db: Session, payload: schemas.UserCreate) -> models.User:
    user = models.User(
        name=payload.name,
        email=payload.email,
        hashed_password=models.User.hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def list_users(db: Session) -> List[models.User]:
    return db.query(models.User).order_by(models.User.name).all()


# ---------------------------------------------------------------------------
# Note CRUD
# ---------------------------------------------------------------------------

def create_note(db: Session, payload: schemas.NoteCreate) -> models.Note:
    note = models.Note(
        title=payload.title,
        content=payload.content,
        tag=payload.tag.strip().lower() if payload.tag else "",
        owner_id=payload.owner_id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def get_note(db: Session, note_id: int) -> Optional[models.Note]:
    return db.query(models.Note).filter(models.Note.id == note_id).first()


def list_notes(
    db: Session,
    skip:     int           = 0,
    limit:    int           = 50,
    tag:      Optional[str] = None,
    owner_id: Optional[int] = None,
    search:   Optional[str] = None,
) -> List[models.Note]:
    q = db.query(models.Note)
    if tag:
        q = q.filter(models.Note.tag == tag.strip().lower())
    if owner_id:
        q = q.filter(models.Note.owner_id == owner_id)
    if search:
        needle = f"%{search.strip().lower()}%"
        q = q.filter(
            models.Note.title.ilike(needle) | models.Note.content.ilike(needle)
        )
    return q.order_by(models.Note.created_at.desc()).offset(skip).limit(limit).all()


def count_notes(db: Session, tag: Optional[str] = None) -> int:
    q = db.query(models.Note)
    if tag:
        q = q.filter(models.Note.tag == tag.strip().lower())
    return q.count()


def update_note(db: Session, note_id: int, payload: schemas.NoteUpdate) -> Optional[models.Note]:
    note = get_note(db, note_id)
    if not note:
        return None
    if payload.title   is not None: note.title   = payload.title
    if payload.content is not None: note.content = payload.content
    if payload.tag     is not None: note.tag      = payload.tag.strip().lower()
    note.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note_id: int) -> bool:
    note = get_note(db, note_id)
    if not note:
        return False
    db.delete(note)
    db.commit()
    return True


def set_note_tag(db: Session, note: models.Note, tag: str) -> models.Note:
    note.tag = tag.strip().lower()
    note.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)
    return note


def update_note_embedding(db: Session, note_id: int, embedding_json: str) -> None:
    note = get_note(db, note_id)
    if note:
        note.embedding = embedding_json
        db.commit()


def get_all_notes(db: Session) -> List[models.Note]:
    return db.query(models.Note).all()


def get_all_notes_with_embeddings(db: Session) -> List[models.Note]:
    return db.query(models.Note).filter(models.Note.embedding.isnot(None)).all()


# ---------------------------------------------------------------------------
# Bulk import
# ---------------------------------------------------------------------------

def bulk_import_notes(
    db: Session,
    lines: List[str],
    default_tag: str = "imported",
) -> Dict[str, Any]:
    """
    Import one note per non-empty line.
    Each line becomes the note title; content defaults to the same text.
    Duplicate titles are skipped.
    """
    imported, skipped, created = 0, 0, []
    existing_titles = {n.title.strip().lower() for n in get_all_notes(db)}

    for raw in lines:
        line = raw.strip()
        if not line:
            skipped += 1
            continue
        if line.lower() in existing_titles:
            skipped += 1
            continue
        note = models.Note(title=line, content=line, tag=default_tag)
        db.add(note)
        existing_titles.add(line.lower())
        imported += 1
        created.append(note)

    db.commit()
    for n in created:
        db.refresh(n)
    return {"imported": imported, "skipped": skipped, "notes": created}


# ---------------------------------------------------------------------------
# Reporting queries
# ---------------------------------------------------------------------------

def notes_per_tag(db: Session) -> List[Dict[str, Any]]:
    rows = (
        db.query(models.Note.tag, func.count(models.Note.id).label("count"))
        .group_by(models.Note.tag)
        .order_by(func.count(models.Note.id).desc())
        .all()
    )
    return [{"tag": row.tag, "count": row.count} for row in rows]


def recent_notes(db: Session, n: int = 5) -> List[models.Note]:
    return db.query(models.Note).order_by(models.Note.created_at.desc()).limit(n).all()


def top_tags(db: Session, n: int = 10) -> List[Dict[str, Any]]:
    """Return the n most-used tags."""
    all_notes = get_all_notes(db)
    counter: Counter = Counter(note.tag for note in all_notes if note.tag)
    return [{"tag": tag, "count": cnt} for tag, cnt in counter.most_common(n)]


def notes_created_per_day(db: Session, days: int = 7) -> List[Dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    notes = (
        db.query(models.Note)
        .filter(models.Note.created_at >= cutoff)
        .order_by(models.Note.created_at)
        .all()
    )
    counts: Dict[str, int] = {}
    for note in notes:
        day = note.created_at.strftime("%Y-%m-%d")
        counts[day] = counts.get(day, 0) + 1
    return [{"date": d, "count": c} for d, c in sorted(counts.items())]
