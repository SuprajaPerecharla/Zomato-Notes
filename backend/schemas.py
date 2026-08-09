"""
schemas.py — Pydantic v2 request/response schemas.
Matches the seed data: User(name, email, password) + Note(title, content, tag, owner_id).
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    name:     str = Field(..., min_length=1, max_length=64)
    email:    str = Field(..., min_length=3, max_length=128)
    password: str = Field(..., min_length=4)


class UserRead(BaseModel):
    id:         int
    name:       str
    email:      str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Note schemas
# ---------------------------------------------------------------------------

class NoteCreate(BaseModel):
    title:    str           = Field(..., min_length=1, max_length=256)
    content:  str           = Field(..., min_length=1)
    tag:      str           = Field(default="", max_length=64)
    owner_id: Optional[int] = None

    model_config = {"str_strip_whitespace": True}


class NoteUpdate(BaseModel):
    title:   Optional[str] = Field(None, min_length=1, max_length=256)
    content: Optional[str] = Field(None, min_length=1)
    tag:     Optional[str] = Field(None, max_length=64)

    model_config = {"str_strip_whitespace": True}


class NoteRead(BaseModel):
    id:         int
    title:      str
    content:    str
    tag:        str
    owner_id:   Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_note(cls, note) -> "NoteRead":
        return cls(
            id=note.id,
            title=note.title,
            content=note.content,
            tag=note.tag or "",
            owner_id=note.owner_id,
            created_at=note.created_at,
            updated_at=note.updated_at,
        )


# ---------------------------------------------------------------------------
# Search / ranking
# ---------------------------------------------------------------------------

class SearchResult(BaseModel):
    note:       NoteRead
    score:      float = Field(..., description="Relevance score 0–1")
    match_type: str   = Field(..., description="exact_title | keyword | semantic")


class SearchResponse(BaseModel):
    query:   str
    results: List[SearchResult]
    total:   int


# ---------------------------------------------------------------------------
# Bulk import
# ---------------------------------------------------------------------------

class BulkImportResponse(BaseModel):
    imported: int
    skipped:  int
    notes:    List[NoteRead]


# ---------------------------------------------------------------------------
# AI
# ---------------------------------------------------------------------------

class AutoTagResponse(BaseModel):
    suggested_tag: str
    applied:       bool = False


class AIResponse(BaseModel):
    answer:     str
    note_id:    Optional[int] = None
    model_used: str
