import pytest
from fastapi import status
from app.db.models import ImageInfo, Tag

# Your other imports, e.g., schemas/models if required


class TestGetTagAPI:
    """
    Test cases for the tag GET.
    """

    @pytest.fixture(autouse=True, scope="class")
    def setup_data(self, test_db_session):
        tags = ["tag1", "tag2", "tag3"]
        for tag_name in tags:
            tag = Tag(name=tag_name)
            test_db_session.add(tag)
        test_db_session.commit()

    def test_get_all_tags(self, test_client):
        response = test_client.get("image_api/tag/tags")

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
        assert len(response.json()) == 3