from pydantic import BaseModel, model_validator, validator
from datetime import datetime
import json
from typing import List, Optional

from .tag import TagBase


class ImageInfoBase(BaseModel):
    image: str
    title: str
    description: str


class ImageInfoCreate(ImageInfoBase):
    tags: List[str] = []

    @model_validator(mode='before')
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class ImageInfo(ImageInfoBase):
    id: int
    height: int
    width: int
    created_at: datetime
    tags: List[TagBase] = []

    class Config:
        from_attributes = True


class ImageInfoFilters(BaseModel):
    offset: Optional[int] = 0
    limit: Optional[int] = None
    tags: Optional[List[str]] = None
    created_date: Optional[str] = None
    created_date__after: Optional[str] = None
    created_date__before: Optional[str] = None
    random: Optional[bool] = False

    @validator("created_date", "created_date__after", "created_date__before", pre=True, always=True)
    def validate_date_format(cls, date_str: str):
        if date_str:
            try:
                datetime.strptime(date_str, "%Y%m%d")
                return date_str
            except ValueError:
                raise ValueError("Invalid date format. Expected YYYYMMDD.")
        return date_str
