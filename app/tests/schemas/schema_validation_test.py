from json import JSONDecodeError

import pytest
from pydantic import ValidationError

from app.schemas import image_info as image_schemas


class TestImageInfoSchemas:
    def test_validate_to_json_str_value(self):
        test_data = '{"title": "Test Image", "description": "Test Description", "tags": ["tag1", "tag2"]}'
        img_info = image_schemas.ImageInfoCreate.validate_to_json(test_data)
        assert isinstance(img_info, image_schemas.ImageInfoCreate)
        assert img_info.title == "Test Image"
        assert img_info.description == "Test Description"
        assert img_info.tags == ["tag1", "tag2"]


    def test_validate_to_json_not_json_string(self):
        with pytest.raises(JSONDecodeError) as e_info:
            test_data = '["image": "path/to/image.jpg", "title": "Test Image", "description": "Test Description", "tags": ["tag1", "tag2"]]'
            img_info = image_schemas.ImageInfoCreate.validate_to_json(test_data)


    def test_validate_to_json_missing_require_param(self):
        with pytest.raises(ValidationError) as e_info:
            test_data = '{"description": "Test Description", "tags": ["tag1", "tag2"]}'
            img_info = image_schemas.ImageInfoCreate.validate_to_json(test_data)


    def test_validate_to_json_invalid_tags(self):
        with pytest.raises(ValidationError) as e_info:
            test_data = '{"image": "path/to/image.jpg", "title": "Test Image", "description": "Test Description", "tags": "tag1"}'
            img_info = image_schemas.ImageInfoCreate.validate_to_json(test_data)


    def test_validate_date_format_valid(self):
        valid_date_str = "20230901"
        result = image_schemas.ImageInfoFilters.validate_date_format(valid_date_str)
        assert result == valid_date_str


    def test_validate_date_format_invalid(self):
        invalid_date_str = "2023-09-01"
        with pytest.raises(ValueError) as e_info:
            image_schemas.ImageInfoFilters.validate_date_format(invalid_date_str)


    def test_validate_date_conflict_only_created_date(self):
        filter_data = image_schemas.ImageInfoFilters(created_date="20230920")
        result = filter_data.validate_date_conflict()
        assert result == filter_data


    def test_validate_date_conflict_created_date_and_after(self):
        with pytest.raises(ValidationError) as e_info:
            filter_data = image_schemas.ImageInfoFilters(created_date="20230920", created_date__after="20230901")


    def test_validate_date_conflict_created_date_and_before(self):
        with pytest.raises(ValidationError) as e_info:
            filter_data = image_schemas.ImageInfoFilters(created_date="20230920", created_date__before="20230901")
