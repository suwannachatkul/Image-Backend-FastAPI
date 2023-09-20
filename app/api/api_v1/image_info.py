from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import cast, Date
from sqlalchemy.sql import func

from app.db import session
from app.db.models import ImageInfo, Tag
from app.schemas import image_info as schemas

router = APIRouter()

@router.get("/image/", response_model=list[schemas.ImageInfo])
def get_image_infos(
    offset: int = 0,
    limit: int = None,
    tags: List[str] = Query(None),
    created_date: str = None,
    created_date__after: str = None,
    created_date__before: str = None,
    random: bool = False,
    db: Session = Depends(session.get_db)
):
    query = db.query(ImageInfo)

    # Filter by tags
    if tags:
        query = query.join(ImageInfo.tags).filter(Tag.name.in_(tags))

    # Filter by created_date, created_date__after, and created_date__before
    if created_date:
        date = datetime.strptime(created_date, '%Y%m%d').date()
        query = query.filter(cast(ImageInfo.created_at, Date) == date)
    else:
        if created_date__after:
            date_after = datetime.strptime(created_date__after, '%Y%m%d').date()
            query = query.filter(ImageInfo.created_at >= date_after)
        if created_date__before:
            date_before = datetime.strptime(created_date__before, '%Y%m%d').date()
            query = query.filter(ImageInfo.created_at <= date_before)

    # Order by random
    if random:
        query = query.order_by(func.random())

    # Apply offset and limit
    query = query.offset(offset)
    if limit:
        query = query.limit(limit)

    images = query.all()
    return images

@router.get("/image/{image_info_id}", response_model=schemas.ImageInfo)
def get_image_info(image_info_id: int, db: Session = Depends(session.get_db)):
    image = db.query(ImageInfo).filter(ImageInfo.id == image_info_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image
