import json
import pytest
from fastapi import status
from app.db.models import ImageInfo, Tag



class TestPatchImageAPI:
    """
    Test cases for the image GET
    """

    @pytest.fixture(autouse=True, scope="class")
    def setup_data(self, test_db_session):
        tags = [Tag(name="tag1"), Tag(name="tag2"), Tag(name="tag3")]
        for tag in tags:
            test_db_session.add(tag)

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
        ]
        for image_info in images:
            test_db_session.add(image_info)
        test_db_session.commit()

    def test_patch(self, test_client, test_db_session):
        old_data = test_db_session.query(ImageInfo).filter(ImageInfo.id == 1).first()
        old_data_dict = {
            "title": old_data.title,
            "description": old_data.description,
            "tags": old_data.tags
        }

        image_data_payload = {
            "title": "test_image",
            "description": "test description",
            "tags": ["test_tag1"],
        }
        image_data_str = json.dumps(image_data_payload)

        response = test_client.patch(
            "image_api/image/1/",
            json=image_data_payload,
        )

        response_data = response.json()
        assert response.status_code == status.HTTP_200_OK

        new_data = test_db_session.query(ImageInfo).filter(ImageInfo.id == 1).first()
        assert new_data.title != old_data_dict["title"]
        assert new_data.title == "test_image"
        assert new_data.description != old_data_dict["description"]
        assert new_data.description == "test description"
        assert len(new_data.tags) == 1
        assert new_data.tags[0].name != old_data_dict["tags"][0].name
        assert new_data.tags[0].name == "test_tag1"

    def test_patch_notexist(self, test_client, test_db_session):
        image_data_payload = {
            "title": "test_image",
            "description": "test description",
            "tags": ["test_tag1"],
        }
        image_data_str = json.dumps(image_data_payload)

        response = test_client.patch(
            "image_api/image/99999/",
            json=image_data_payload,
        )

        response_data = response.json()
        assert response.status_code == status.HTTP_404_NOT_FOUND

