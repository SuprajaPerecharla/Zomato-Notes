"""
Pydantic v2 schemas for request/response validation.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from .models import Severity


# ---------------------------------------------------------------------------
# Tag schemas
# ---------------------------------------------------------------------------

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)

    @field_validator("name")
    @classmethod
    def normalise_tag(cls, v: str) -> str:
        # lowercase, strip whitespace, replace spaces with hyphens
        return v.strip().lower().replace(" ", "-")


class TagCreate(TagBase):
    pass


class TagRead(TagBase):
    id: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Note schemas
# ---------------------------------------------------------------------------

class NoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    body: str = Field(..., min_length=1)
    severity: Severity = Severity.medium


class NoteCreate(NoteBase):
    tags: List[str] = Field(default_factory=list, description="Tag names to attach")


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=256)
    body: Optional[str] = Field(None, min_length=1)
    severity: Optional[Severity] = None
    tags: Optional[List[str]] = None


class NoteRead(NoteBase):
    id: int
    tags: List[TagRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Search / ranking schemas
# ---------------------------------------------------------------------------

class SearchResult(BaseModel):
    note: NoteRead
    score: float = Field(..., description="Relevance score 0–1")
    match_type: str = Field(..., description="exact_title | keyword | semantic")


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int


class TagJumpResult(BaseModel):
    tag: str
    notes: List[NoteRead]
    total: int


# ---------------------------------------------------------------------------
# Auto-tag response
# ---------------------------------------------------------------------------

class AutoTagResponse(BaseModel):
    suggested_tags: List[str]
    applied: bool = False
