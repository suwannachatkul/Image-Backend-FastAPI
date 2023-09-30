from datetime import datetime, timedelta

import pytest
from fastapi import status
from starlette.responses import Response

from app.db.models import ImageInfo, Tag


def assert_image_response(response: Response, expected_length: int, expected_status: int = status.HTTP_200_OK):
    """
    Check the response for common image assertions.
    """
    assert response.status_code == expected_status
    images = response.json()
    assert isinstance(images, list)
    assert len(images) == expected_length


class TestGetImageAPI:
    """
    Test cases for the image GET
    """

    @pytest.fixture(autouse=True, scope="class")
    def setup_data(self, test_db_session):
        tags = [Tag(name="tag1"), Tag(name="tag2"), Tag(name="tag3")]
        for tag in tags:
            test_db_session.add(tag)

        today = datetime.now().date()
        images = [
            ImageInfo(
                image="path/to/image1.jpg",
                title="image1",
                description="description1",
                height=400,
                width=300,
                file_size=10000,
                tags=tags,
            ),
            ImageInfo(
                image="path/to/image2.jpg",
                title="image2",
                description="description3",
                height=600,
                width=500,
                file_size=10000,
                created_at=today + timedelta(days=1),
            ),
            ImageInfo(
                image="path/to/image3.jpg",
                title="image3",
                description="description4",
                height=700,
                width=600,
                file_size=10000,
                created_at=today + timedelta(days=7),
            ),
            ImageInfo(
                image="path/to/image4.jpg",
                title="image4",
                description="description5",
                height=800,
                width=700,
                file_size=10000,
                created_at=today + timedelta(days=30),
            ),
        ]
        for image_info in images:
            test_db_session.add(image_info)
        test_db_session.commit()

    def test_get_all_images_without_filters(self, test_client):
        response = test_client.get("image_api/image/")
        assert_image_response(response, 4, status.HTTP_200_OK)

    def test_get_images_with_tag_filter(self, test_client):
        tag_filter = ["tag1"]
        response = test_client.get(f"image_api/image/?tags={tag_filter[0]}")
        assert_image_response(response, 1, status.HTTP_200_OK)
        assert response.json()[0]["title"] == "image1"

    def test_get_images_with_created_date_filter(self, test_client):
        created_date = (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")
        response = test_client.get(f"image_api/image/?created_date={created_date}")
        assert_image_response(response, 1, status.HTTP_200_OK)
        assert response.json()[0]["title"] == "image2"

    def test_get_images_created_date_after_filter(self, test_client):
        after_date = (datetime.now() + timedelta(days=30)).strftime("%Y%m%d")
        response = test_client.get(f"image_api/image/?created_date__after={after_date}")
        assert_image_response(response, 1, status.HTTP_200_OK)
        assert response.json()[0]["title"] == "image4"

    def test_get_images_created_date_before_filter(self, test_client):
        before_date = (datetime.now() + timedelta(days=7)).strftime("%Y%m%d")
        response = test_client.get(f"image_api/image/?created_date__before={before_date}")
        assert_image_response(response, 3, status.HTTP_200_OK)

    def test_get_images_error_with_combined_date_filters(self, test_client):
        created_date = datetime.now().strftime("%Y%m%d")
        response = test_client.get(f"image_api/image/?created_date={created_date}&created_date__after={created_date}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
