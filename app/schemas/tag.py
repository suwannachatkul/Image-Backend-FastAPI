from pydantic import BaseModel
from typing import List

class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int
    name_slug: str

    class Config:
        from_attributes = True
