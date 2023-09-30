import os
from datetime import datetime
import logging
from typing import Annotated, Dict, List

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, Response, UploadFile, Request
from pydantic import ValidationError
from slugify import slugify
from starlette import status
from sqlalchemy import Date, cast
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.core.config import settings
from app.db import session
from app.db.models import ImageInfo, Tag
from app.schemas import image_info as image_schemas, tag as tag_schemas
from app.utils.get_image_size import get_image_metadata_from_bytesio, UnknownImageFormat
from app.utils.image_util import ImageUtil


logger = logging.getLogger(__name__)

router = APIRouter()


def get_or_create_tag(db: Session, tag_name: str) -> Tag:
    tag_instance = db.query(Tag).filter_by(name=tag_name).first()
    if not tag_instance:
        tag_instance = Tag(name=tag_name, name_slug=slugify(tag_name))
        db.add(tag_instance)
        db.flush()
        logger.info(f"New tag created: {tag_name}")
    return tag_instance


@router.get("/tags/", response_model=List[tag_schemas.Tag], status_code=status.HTTP_200_OK)
def get_tags(db: Session = Depends(session.get_db)):
    tags = db.query(Tag).all()
    return tags


@router.get("/image/", response_model=list[image_schemas.ImageInfo], status_code=status.HTTP_200_OK)
def get_image_infos(
    param: image_schemas.ImageInfoFilters = Depends(),
    tags: List[str] = Query(default=None),
    db: Session = Depends(session.get_db),
):
    query = db.query(ImageInfo)

    # Filter by tags
    if tags:
        query = query.join(ImageInfo.tags).filter(Tag.name.in_(tags))

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
        logger.warning(f"Image with id {image_info_id} not found")
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@router.post("/image/", response_model=image_schemas.ImageInfo, status_code=status.HTTP_201_CREATED)
async def upload_image(
    param: image_schemas.ImageInfoCreateQuery = Depends(),
    image_data: image_schemas.ImageInfoCreate = Body(...),
    file: UploadFile = File(...),
    db: Session = Depends(session.get_db),
):
    try:
        img_contents = await file.read()
        file_size = len(img_contents)

        # size exceeded do resize
        if file_size > settings.MAX_IMG_SIZE:
            img = ImageUtil.optimize_image_bytes_size(img_contents, param.ext, settings.MAX_IMG_SIZE)
            img_contents = img.getbuffer()
            file_size = img_contents.nbytes
            img_meta = get_image_metadata_from_bytesio(img, file_size)
        else:
            # size not exceeded but image ext needed to covert
            if param.ext and not file.filename.endswith("." + param.ext):
                converted_image = ImageUtil.convert_image_type(img_contents, param.ext)
                img_contents = ImageUtil.PIL_to_bytes(converted_image, param.ext).getbuffer()

            file.file.seek(0)
            img_meta = get_image_metadata_from_bytesio(file.file, file_size)

        # Write the uploaded file's content to this path
        image_name = file.filename.replace(file.filename.split(".")[-1], param.ext, 1)
        image_path = os.path.join(settings.MEDIA_FOLDER, image_name)
        with open(image_path, "wb+") as buffer:
            buffer.write(img_contents)

        new_image = ImageInfo(
            image=image_path,
            title=image_data.title,
            description=image_data.description,
            height=img_meta.height,
            width=img_meta.width,
            file_size=file_size,
        )
        db.add(new_image)
        db.flush()

        # Check each tag. If it doesn't exist, create it.
        for tag_data in image_data.tags:
            tag_instance = get_or_create_tag(db, tag_data)
            new_image.tags.append(tag_instance)

        db.commit()
        logger.info(f"New image uploaded: ID={new_image.id}, Title={new_image.title}, Path={new_image.image}, Size={file_size}, Tags={[tag.name for tag in new_image.tags]}")

    except ValueError as ve:
        logger.error(f"Value error on image upload: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except UnknownImageFormat as ue:
        logger.error(f"Unknown image format on upload: {ue}")
        raise HTTPException(status_code=400, detail="Invalid file")
    except Exception as e:
        logger.error(f"Unexpected error on image upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return new_image


@router.patch("/image/{image_info_id}/", response_model=image_schemas.ImageInfo, status_code=status.HTTP_200_OK)
def update_image_info(
    image_info_id: int, update_data: image_schemas.ImageInfoUpdate, db: Session = Depends(session.get_db)
):
    image = db.query(ImageInfo).filter(ImageInfo.id == image_info_id).first()
    if not image:
        logger.warning(f"Attempt to update non-existent image with id {image_info_id}")
        raise HTTPException(status_code=404, detail="Image not found")

    if update_data.title is not None:
        image.title = update_data.title
    if update_data.description is not None:
        image.description = update_data.description

    if update_data.tags is not None:
        image.tags = []

        for tag_data in update_data.tags:
            tag_instance = get_or_create_tag(db, tag_data)
            image.tags.append(tag_instance)

    db.commit()
    logger.info(f"Image updated: ID={image_info_id}, Title={image.title}, Description={image.description}, Tags={[tag.name for tag in image.tags]}")

    return image


@router.delete("/image/{image_info_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_image_info(image_info_id: int, db: Session = Depends(session.get_db)):
    image = db.query(ImageInfo).filter(ImageInfo.id == image_info_id).first()
    if not image:
        logger.warning(f"Attempt to delete non-existent image with id {image_info_id}")
        raise HTTPException(status_code=404, detail="Image not found")

    db.delete(image)
    db.commit()
    logger.info(f"Image deleted: ID={image_info_id}, Path={image.image}")

    return None
