import os
from datetime import datetime
import logging
import traceback
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import Date, cast, func
from slugify import slugify

from app.core.config import settings
from app.db.models import ImageInfo, Tag
from app.services.tag_service import TagService
from app.utils.get_image_size import get_image_metadata_from_bytesio, UnknownImageFormat
from app.utils.image_util import ImageUtil


logger = logging.getLogger(__name__)


class ImageServiceError(Exception):
    pass

class ImageServiceNotFoundError(Exception):
    pass


class ImageService:
    def __init__(self, db: Session):
        self.db = db

    def get_images(self, param, tags=None):
        query = self.db.query(ImageInfo)

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

    def get_image_by_id(self, image_info_id: int):
        query = self.db.query(ImageInfo)
        return query.filter(ImageInfo.id == image_info_id).first()

    def create_image(self, param, image_data, img_contents, filename, file_bytes) -> ImageInfo:
        try:
            file_size = len(img_contents)

            # Size exceeded: do resize
            if file_size > settings.MAX_IMG_SIZE:
                img = ImageUtil.optimize_image_bytes_size(img_contents, param.ext, settings.MAX_IMG_SIZE)
                img_contents = img.getbuffer()
                file_size = img_contents.nbytes
                img_meta = get_image_metadata_from_bytesio(img, file_size)
            else:
                if param.ext and not filename.endswith("." + param.ext):
                    converted_image = ImageUtil.convert_image_type(img_contents, param.ext)
                    img_contents = ImageUtil.PIL_to_bytes(converted_image, param.ext).getbuffer()

                img_meta = get_image_metadata_from_bytesio(file_bytes, file_size)

            # Write the uploaded file's content to the path
            image_name = filename.replace(filename.split(".")[-1], param.ext, 1)
            image_path = os.path.join(settings.MEDIA_FOLDER, image_name)
            if not os.path.exists(settings.MEDIA_FOLDER):
                os.mkdir(settings.MEDIA_FOLDER)
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
            self.db.add(new_image)
            self.db.flush()

            # Check each tag. If it doesn't exist, create it.
            tag_service = TagService(self.db)
            for tag_data in image_data.tags:
                tag_instance = tag_service.get_or_create_tag(tag_data)
                new_image.tags.append(tag_instance)

            self.db.commit()

            return new_image

        except ValueError as ve:
            logger.error(f"Value error on image upload: {ve}")
            raise ValueError(f"Value error on image upload: {ve}")
        except UnknownImageFormat as ue:
            logger.error(f"Unknown image format on upload: {ue}")
            raise UnknownImageFormat(f"Unknown image format on upload: {ue}")
        except Exception as e:
            error_info = traceback.format_exc()
            logger.error(f"Unexpected error on image upload:\n{error_info}")
            raise ImageServiceError(f"Unexpected error on image upload:\n{error_info}")

    def update_image(self, image_info_id: int, update_data) -> ImageInfo:
        try:
            image = self.db.query(ImageInfo).filter(ImageInfo.id == image_info_id).one()

            if update_data.title is not None:
                image.title = update_data.title
            if update_data.description is not None:
                image.description = update_data.description

            if update_data.tags is not None:
                image.tags = []

                for tag_data in update_data.tags:
                    tag_instance = TagService(self.db).get_or_create_tag(tag_data)
                    image.tags.append(tag_instance)

            self.db.commit()
            return image

        except NoResultFound:
            logger.warning(f"Image with id {image_info_id} not found")
            raise ImageServiceNotFoundError(f"Image ID: {image_info_id} not found")
        except Exception as e:
            error_info = traceback.format_exc()
            logger.error(f"Unexpected error on image update:\n{error_info}")
            raise ImageServiceError(f"Unexpected error on image update: {str(e)}")

    def delete_image_by_id(self, image_info_id: int) -> None:
        try:
            image = self.db.query(ImageInfo).filter(ImageInfo.id == image_info_id).one()
            self.db.delete(image)
            self.db.commit()
            return image

        except NoResultFound:
            raise ImageServiceNotFoundError(f"Image with id {image_info_id} not found")
        except Exception as e:
            error_info = traceback.format_exc()
            logger.error(f"Unexpected error on image update:\n{error_info}")
            raise ImageServiceError(str(e))
