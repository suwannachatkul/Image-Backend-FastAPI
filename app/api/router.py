from fastapi import APIRouter

from app.api.api_v1 import image_info

router = APIRouter()

router.include_router(image_info.router, prefix="/image_api", tags=["image_api"])