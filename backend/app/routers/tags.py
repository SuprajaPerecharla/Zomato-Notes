"""
Tags router — /api/tags
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .. import crud, schemas

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("/", response_model=List[schemas.TagRead])
def list_tags(db: Session = Depends(get_db)):
    return crud.list_tags(db)
