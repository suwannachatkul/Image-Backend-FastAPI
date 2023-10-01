from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from starlette import status

from app.db import session
from app.db.models import Tag
from app.schemas import tag as tag_schemas
from app.services.tag_service import TagService

router = APIRouter()


@router.get("/tags/", response_model=List[tag_schemas.Tag], status_code=status.HTTP_200_OK)
def get_tags(db: Session = Depends(session.get_db)):
    tag_service = TagService(db)
    return tag_service.get_all_tags()
