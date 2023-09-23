from sqlalchemy import event
from sqlalchemy.orm import Session
from slugify import slugify
from app.db.models import Tag

def slugify_tag_name(session: Session, flush_context, instances):
    for instance in session.dirty | session.new:
        if isinstance(instance, Tag):
            instance.name_slug = slugify(instance.name)

event.listen(Session, "before_flush", slugify_tag_name)