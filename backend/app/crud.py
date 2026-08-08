"""
Database CRUD helpers — pure SQLAlchemy, no business logic.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from . import models, schemas


# ---------------------------------------------------------------------------
# Tag helpers
# ---------------------------------------------------------------------------

def get_or_create_tag(db: Session, name: str) -> models.Tag:
    name = name.strip().lower().replace(" ", "-")
    tag = db.query(models.Tag).filter(models.Tag.name == name).first()
    if not tag:
        tag = models.Tag(name=name)
        db.add(tag)
        db.flush()  # assign PK before associating with notes
        db.refresh(tag)
    return tag


def list_tags(db: Session) -> List[models.Tag]:
    return db.query(models.Tag).order_by(models.Tag.name).all()


# ---------------------------------------------------------------------------
# Note CRUD
# ---------------------------------------------------------------------------

def create_note(db: Session, payload: schemas.NoteCreate) -> models.Note:
    note = models.Note(
        title=payload.title,
        body=payload.body,
        severity=payload.severity,
    )
    for tag_name in payload.tags:
        tag = get_or_create_tag(db, tag_name)
        note.tags.append(tag)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def get_note(db: Session, note_id: int) -> Optional[models.Note]:
    return db.query(models.Note).filter(models.Note.id == note_id).first()


def list_notes(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    severity: Optional[str] = None,
    tag: Optional[str] = None,
) -> List[models.Note]:
    q = db.query(models.Note)
    if severity:
        q = q.filter(models.Note.severity == severity)
    if tag:
        q = q.join(models.Note.tags).filter(models.Tag.name == tag.lower())
    return q.order_by(models.Note.created_at.desc()).offset(skip).limit(limit).all()


def count_notes(
    db: Session,
    severity: Optional[str] = None,
    tag: Optional[str] = None,
) -> int:
    q = db.query(models.Note)
    if severity:
        q = q.filter(models.Note.severity == severity)
    if tag:
        q = q.join(models.Note.tags).filter(models.Tag.name == tag.lower())
    return q.count()


def update_note(db: Session, note_id: int, payload: schemas.NoteUpdate) -> Optional[models.Note]:
    note = get_note(db, note_id)
    if not note:
        return None
    if payload.title is not None:
        note.title = payload.title
    if payload.body is not None:
        note.body = payload.body
    if payload.severity is not None:
        note.severity = payload.severity
    if payload.tags is not None:
        note.tags.clear()
        for tag_name in payload.tags:
            tag = get_or_create_tag(db, tag_name)
            note.tags.append(tag)
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


def update_note_embedding(db: Session, note_id: int, embedding_json: str) -> None:
    note = get_note(db, note_id)
    if note:
        note.embedding = embedding_json
        db.commit()


def set_note_tags(db: Session, note: models.Note, tag_names: List[str]) -> models.Note:
    note.tags.clear()
    for name in tag_names:
        tag = get_or_create_tag(db, name)
        note.tags.append(tag)
    db.commit()
    db.refresh(note)
    return note


def get_notes_by_tag(db: Session, tag_name: str) -> List[models.Note]:
    return (
        db.query(models.Note)
        .join(models.Note.tags)
        .filter(models.Tag.name == tag_name.lower())
        .order_by(models.Note.created_at.desc())
        .all()
    )


def get_all_notes_with_embeddings(db: Session) -> List[models.Note]:
    return db.query(models.Note).filter(models.Note.embedding.isnot(None)).all()


def get_all_notes(db: Session) -> List[models.Note]:
    return db.query(models.Note).all()
