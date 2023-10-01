from fastapi import APIRouter

from app.api.api_v1 import image_info, tags

router = APIRouter()

router.include_router(image_info.router, prefix="/image_api/image", tags=["image"])
router.include_router(tags.router, prefix="/image_api/tag", tags=["tag"])