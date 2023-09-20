from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas import image_info as schemas
from app.db import session
from app.db.models import ImageInfo

router = APIRouter()


@router.get("/image/", response_model=list[schemas.ImageInfo])
def get_image_infos(offset: int = 0, limit: int = None, db: Session = Depends(session.get_db)):
    query = db.query(ImageInfo).offset(offset)
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
