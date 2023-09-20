from pydantic import BaseModel
from typing import List

class TagBase(BaseModel):
    name: str
    name_slug: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int

    class Config:
        orm_mode = True
