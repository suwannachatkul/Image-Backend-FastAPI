import logging.config
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError

from app.api.router import router as api_router
from app.core.config import settings

logging.config.dictConfig(settings.LOGGING_CONFIG)

app = FastAPI()

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(
            {"detail": exc.errors()}
        ),
    )


app.include_router(api_router)