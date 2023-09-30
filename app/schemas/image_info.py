import json
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator, model_validator

from .tag import TagBase


class ImageInfoBase(BaseModel):
    title: str
    description: str = None


class ImageInfoCreateQuery(BaseModel):
    ext: Optional[str] = "jpg"


class ImageInfoCreate(ImageInfoBase):
    tags: List[str] = []

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value):
        if isinstance(value, str):
            return cls(**json.loads(value))
        return value


class ImageInfoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class ImageInfo(ImageInfoBase):
    id: int
    height: int
    width: int
    file_size: int
    created_at: datetime
    tags: List[TagBase] = []

    class Config:
        from_attributes = True


class ImageInfoFilters(BaseModel):
    offset: Optional[int] = 0
    limit: Optional[int] = None
    created_date: Optional[str] = None
    created_date__after: Optional[str] = None
    created_date__before: Optional[str] = None
    random: Optional[bool] = False

    @field_validator("created_date", "created_date__after", "created_date__before", mode="before")
    @classmethod
    def validate_date_format(cls, date_str: str):
        if date_str:
            try:
                datetime.strptime(date_str, "%Y%m%d")
                return date_str
            except ValueError:
                raise ValueError("Invalid date format. Expected YYYYMMDD.")
        return date_str

    @model_validator(mode="after")
    def validate_date_conflict(self):
        created_date = self.created_date
        created_date__after = self.created_date__after
        created_date__before = self.created_date__before

        if created_date and (created_date__after or created_date__before):
            raise ValueError("created_date cannot be used with created_date__after or created_date__before.")

        return self
