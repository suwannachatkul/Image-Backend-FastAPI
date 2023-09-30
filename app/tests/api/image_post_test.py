import json
import os
import pytest
from fastapi import status
from PIL import Image
from io import BytesIO
from app.db.models import ImageInfo
from app.core.config import settings


class TestPostImageAPI:
    """
    Test cases for the image GET
    """

    def gen_img_n_payload(self, name: str = None, invalid_img: bool = False, size: int = None, format: str = "JPEG"):
        img_byte_array = BytesIO()

        if invalid_img:
            img_byte_array.write(b"invalid image data")
        else:
            img = Image.new("RGB", (100, 100), color=(255, 255, 255))
            img.save(img_byte_array, format=format)

        if size:
            img_byte_array.size = size

        img_byte_array.seek(0)

        image_data_payload = {
            "title": "test_image",
            "description": "test description",
            "tags": ["test_tag1", "test_tag2"],
        }

        return img_byte_array, image_data_payload

    def test_valid_upload_image(self, test_client, test_db_session):
        try:
            img_byte_array, image_data_payload = self.gen_img_n_payload()
            image_data_str = json.dumps(image_data_payload)

            response = test_client.post(
                "image_api/image/",
                files={"file": ("mock_image.jpg", img_byte_array)},
                data={"image_data": image_data_str},
            )

            assert response.status_code == status.HTTP_201_CREATED
            response_data = response.json()
            assert response_data["title"] == image_data_payload["title"]

            new_image = test_db_session.query(ImageInfo).filter(ImageInfo.id == response_data["id"]).first()
            assert new_image is not None

        finally:
            if os.path.exists(os.path.join(settings.MEDIA_FOLDER, "mock_image.jpg")):
                os.remove(os.path.join(settings.MEDIA_FOLDER, "mock_image.jpg"))

    def test_invalid_upload_image(self, test_client, test_db_session):
        try:
            img_byte_array, image_data_payload = self.gen_img_n_payload(invalid_img=True)
            image_data_str = json.dumps(image_data_payload)

            response = test_client.post(
                "image_api/image/",
                files={"file": ("mock_image.jpg", img_byte_array)},
                data={"image_data": image_data_str},
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST

        finally:
            if os.path.exists(os.path.join(settings.MEDIA_FOLDER, "mock_image.jpg")):
                os.remove(os.path.join(settings.MEDIA_FOLDER, "mock_image.jpg"))

    def test_large_upload_image(self, test_client, test_db_session):
        try:
            img_byte_array, image_data_payload = self.gen_img_n_payload(size=settings.MAX_IMG_SIZE + 100)
            image_data_str = json.dumps(image_data_payload)

            response = test_client.post(
                "image_api/image/",
                files={"file": ("mock_image.jpg", img_byte_array)},
                data={"image_data": image_data_str},
            )

            assert response.status_code == status.HTTP_201_CREATED
            response_data = response.json()

            new_image = test_db_session.query(ImageInfo).filter(ImageInfo.id == response_data["id"]).first()
            assert new_image is not None
            assert new_image.file_size < img_byte_array.size

        finally:
            if os.path.exists(os.path.join(settings.MEDIA_FOLDER, "mock_image.jpg")):
                os.remove(os.path.join(settings.MEDIA_FOLDER, "mock_image.jpg"))

    def test_upload_image_w_ext(self, test_client, test_db_session):
        try:
            img_byte_array, image_data_payload = self.gen_img_n_payload()
            image_data_str = json.dumps(image_data_payload)

            response = test_client.post(
                "image_api/image/?ext=png",
                files={"file": ("mock_image.jpg", img_byte_array)},
                data={"image_data": image_data_str},
            )

            assert response.status_code == status.HTTP_201_CREATED
            response_data = response.json()
            assert response_data["title"] == image_data_payload["title"]

            new_image = test_db_session.query(ImageInfo).filter(ImageInfo.id == response_data["id"]).first()
            assert new_image is not None
            assert new_image.image.split(".")[-1] == "png"

            saved_img = Image.open(os.path.join(settings.MEDIA_FOLDER, "mock_image.png"))
            saved_img.close()
            assert saved_img.format == 'PNG'


        finally:
            if os.path.exists(os.path.join(settings.MEDIA_FOLDER, "mock_image.png")):
                os.remove(os.path.join(settings.MEDIA_FOLDER, "mock_image.png"))
