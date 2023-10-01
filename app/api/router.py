from fastapi import APIRouter

from app.api.image import image_info
from app.api.tag import tags

router = APIRouter()

router.include_router(image_info.router, prefix="/image_api/image", tags=["image"])
router.include_router(tags.router, prefix="/image_api/tag", tags=["tag"])