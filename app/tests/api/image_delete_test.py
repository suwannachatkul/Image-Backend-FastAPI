import pytest
from fastapi import status
from app.db.models import ImageInfo, Tag



class TestDeleteImageAPI:
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
            ImageInfo(
                image="path/to/image2.jpg",
                title="image2",
                description="description3",
                height=600,
                width=500,
                file_size=10000,
            ),
        ]
        for image_info in images:
            test_db_session.add(image_info)
        test_db_session.commit()

    def test_delete(self, test_client, test_db_session):
        img_count_before = test_db_session.query(ImageInfo).count()
        delete_id = 1
        response = test_client.delete(
            f"image_api/image/{delete_id}/"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        all_data = test_db_session.query(ImageInfo).all()
        assert len(all_data) == img_count_before - 1
        assert all_data[0].id != delete_id

    def test_delete_not_exist(self, test_client, test_db_session):
        img_count_before = test_db_session.query(ImageInfo).count()
        print(img_count_before)
        delete_id = 9999
        response = test_client.delete(
            f"image_api/image/{delete_id}/"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        all_data = test_db_session.query(ImageInfo).all()
        assert len(all_data) == img_count_before
