"""
models.py — SQLAlchemy ORM models.

Tables
------
users  – name, email, hashed_password
notes  – title, content, tag (single string), owner_id FK → users
"""

import hashlib
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(64),  nullable=False)
    email           = Column(String(128), unique=True, nullable=False, index=True)
    hashed_password = Column(String(128), nullable=False)
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        return self.hashed_password == self.hash_password(password)

    def __repr__(self):
        return f"<User id={self.id} name={self.name!r} email={self.email!r}>"


# ---------------------------------------------------------------------------
# Note
# ---------------------------------------------------------------------------

class Note(Base):
    __tablename__ = "notes"

    id         = Column(Integer, primary_key=True, index=True)
    title      = Column(String(256), nullable=False, index=True)
    content    = Column(Text, nullable=False)
    tag        = Column(String(64),  default="", nullable=False, index=True)
    # JSON-serialised float list — populated by semantic_search.py
    embedding  = Column(Text, nullable=True)

    owner_id   = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    owner      = relationship("User", back_populates="notes")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f"<Note id={self.id} title={self.title!r} tag={self.tag!r}>"
