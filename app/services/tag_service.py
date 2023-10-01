import logging

from slugify import slugify
from sqlalchemy.orm import Session

from app.db.models import Tag

logger = logging.getLogger(__name__)

class TagService:

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_tag(self, tag_name: str) -> Tag:
        tag_instance = self.db.query(Tag).filter_by(name=tag_name).first()
        if not tag_instance:
            tag_instance = Tag(name=tag_name, name_slug=slugify(tag_name))
            self.db.add(tag_instance)
            self.db.flush()
            logger.info(f"New tag created: {tag_name}")
        return tag_instance

    def get_all_tags(self):
        return self.db.query(Tag).all()