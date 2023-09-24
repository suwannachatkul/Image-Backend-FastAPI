import os
from datetime import datetime
from typing import List

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from starlette import status
from sqlalchemy import Date, cast
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.config import settings
from app.db import models, session
from app.db.models import ImageInfo, Tag
from app.schemas import image_info as image_schemas, tag as tag_schemas
from app.utils.get_image_size import get_image_metadata_from_bytesio
from app.utils.image_util import ImageUtil

router = APIRouter()


@router.get("/image/", response_model=list[image_schemas.ImageInfo], status_code=status.HTTP_200_OK)
def get_image_infos(
    param: image_schemas.ImageInfoFilters = Depends(),
    db: Session = Depends(session.get_db),
):
    query = db.query(ImageInfo)

    # Filter by tags
    if param.tags:
        query = query.join(ImageInfo.tags).filter(Tag.name.in_(param.tags))

    # Filter by created_date, created_date__after, and created_date__before
    if param.created_date:
        date = datetime.strptime(param.created_date, "%Y%m%d").date()
        query = query.filter(cast(ImageInfo.created_at, Date) == date)
    else:
        if param.created_date__after:
            date_after = datetime.strptime(param.created_date__after, "%Y%m%d").date()
            query = query.filter(ImageInfo.created_at >= date_after)
        if param.created_date__before:
            date_before = datetime.strptime(param.created_date__before, "%Y%m%d").date()
            query = query.filter(ImageInfo.created_at <= date_before)

    # Order by random
    if param.random:
        query = query.order_by(func.random())

    # Apply offset and limit
    query = query.offset(param.offset)
    if param.limit:
        query = query.limit(param.limit)

    images = query.all()
    return images


@router.get("/image/{image_info_id}", response_model=image_schemas.ImageInfo, status_code=status.HTTP_200_OK)
def get_image_info(image_info_id: int, db: Session = Depends(session.get_db)):
    image = db.query(ImageInfo).filter(ImageInfo.id == image_info_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@router.post("/image/", response_model=image_schemas.ImageInfo, status_code=status.HTTP_201_CREATED)
async def upload_image(
    image_data: image_schemas.ImageInfoCreate = Body(...),
    file: UploadFile = File(...),
    db: Session = Depends(session.get_db),
):
    try:
        img_contents = await file.read()
        file_size = len(img_contents)

        # size exceeded do resize
        if file_size > settings.MAX_IMG_SIZE:
            img = ImageUtil.optimize_image_bytes_size(img_contents, 'jpg', settings.MAX_IMG_SIZE)
            img_contents = img.getbuffer()
            file_size = img_contents.nbytes
            img_meta = get_image_metadata_from_bytesio(img, file_size)
        else:
            file.file.seek(0)
            img_meta = get_image_metadata_from_bytesio(file.file, file_size)

        # Write the uploaded file's content to this path
        image_name = file.filename.replace(file.filename.split(".")[-1], 'jpg', 1)
        image_path = os.path.join(settings.MEDIA_FOLDER, image_name)
        with open(image_path, "wb+") as buffer:
            buffer.write(img_contents)

        new_image = models.ImageInfo(
            image=image_path,
            title=image_data.title,
            description=image_data.description,
            height=img_meta.height,
            width=img_meta.width,
        )
        db.add(new_image)
        db.flush()

        # Check each tag. If it doesn't exist, create it.
        for tag_data in image_data.tags:
            tag_instance = db.query(models.Tag).filter_by(name=tag_data.name).first()

            if not tag_instance:
                tag_instance = models.Tag(name=tag_data.name, name_slug=slugify(tag_data.name))
                db.add(tag_instance)
                db.flush()

            new_image.tags.append(tag_instance)

        db.commit()


    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        if os.path.exists(image_path):
            os.remove(image_path)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

    return new_image
