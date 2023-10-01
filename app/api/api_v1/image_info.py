import logging
from typing import List

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from starlette import status

from app.db import session
from app.schemas import image_info as image_schemas
from app.services.image_service import ImageService, ImageServiceNotFoundError
from app.services.tag_service import TagService
from app.utils.get_image_size import UnknownImageFormat


logger = logging.getLogger(__name__)

router = APIRouter()


def get_image_service(db: Session = Depends(session.get_db)):
    return ImageService(db)


@router.get("/", response_model=list[image_schemas.ImageInfo], status_code=status.HTTP_200_OK)
def get_image_infos(
    param: image_schemas.ImageInfoFilters = Depends(),
    tags: List[str] = Query(default=None),
    image_service: ImageService = Depends(get_image_service),
):
    return image_service.get_images(param, tags)


@router.get("/{image_info_id}", response_model=image_schemas.ImageInfo, status_code=status.HTTP_200_OK)
def get_image_info(image_info_id: int, image_service: ImageService = Depends(get_image_service)):
    image = image_service.get_image_by_id(image_info_id)
    if not image:
        logger.warning(f"Image with id {image_info_id} not found")
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@router.post("/", response_model=image_schemas.ImageInfo, status_code=status.HTTP_201_CREATED)
async def upload_image(
    param: image_schemas.ImageInfoCreateQuery = Depends(),
    image_data: image_schemas.ImageInfoCreate = Body(...),
    file: UploadFile = File(...),
    image_service: ImageService = Depends(get_image_service),
):
    try:
        img_contents = await file.read()
        file.file.seek(0)
        file_bytes = file.file
        new_image = image_service.create_image(param, image_data, img_contents, file.filename, file_bytes)
        logger.info(
            f"New image uploaded: ID={new_image.id}, Title={new_image.title}, Path={new_image.image}, Size={new_image.file_size}, Tags={[tag.name for tag in new_image.tags]}"
        )
        return new_image

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except UnknownImageFormat as ue:
        raise HTTPException(status_code=400, detail="Invalid file")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/{image_info_id}/", response_model=image_schemas.ImageInfo, status_code=status.HTTP_200_OK)
def update_image_info(
    image_info_id: int,
    update_data: image_schemas.ImageInfoUpdate,
    image_service: ImageService = Depends(get_image_service),
):
    try:
        updated_image = image_service.update_image(image_info_id, update_data)
        logger.info(
            f"Image updated: ID={image_info_id}, Title={updated_image.title}, Description={updated_image.description}, Tags={[tag.name for tag in updated_image.tags]}"
        )
        return updated_image

    except ImageServiceNotFoundError:
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{image_info_id}/", status_code=status.HTTP_204_NO_CONTENT)
def delete_image_info(image_info_id: int, image_service: ImageService = Depends(get_image_service)):
    try:
        deleted_image = image_service.delete_image_by_id(image_info_id)
        logger.info(f"Image deleted: ID={image_info_id}, Path={deleted_image.image}")

        return None

    except ImageServiceNotFoundError:
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
