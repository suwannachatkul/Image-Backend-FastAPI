from sqlalchemy import (Column, DateTime, ForeignKey, Integer, String, Table, func)
from sqlalchemy.orm import relationship

from app.db.base_class import Base

# Create an association table for many-to-many relationship between ImageInfo and Tag
image_tags_association = Table(
    'image_tags', Base.metadata,
    Column('image_id', Integer, ForeignKey('images.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    name_slug = Column(String(50), unique=True, index=True)  # For slug, consider adding a utility function or package.

    images = relationship("ImageInfo", secondary=image_tags_association, back_populates="tags")

class ImageInfo(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    image = Column(String)  # This will be a path to the uploaded image.
    title = Column(String(255), index=True)
    description = Column(String, index=True)
    height = Column(Integer)
    width = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tags = relationship("Tag", secondary=image_tags_association, back_populates="images")