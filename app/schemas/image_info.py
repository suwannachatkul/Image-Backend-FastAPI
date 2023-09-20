from pydantic import BaseModel
from datetime import datetime
from typing import List

class ImageInfoBase(BaseModel):
    image: str
    title: str
    description: str
    height: int
    width: int

class ImageInfoCreate(ImageInfoBase):
    pass

class ImageInfo(ImageInfoBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True