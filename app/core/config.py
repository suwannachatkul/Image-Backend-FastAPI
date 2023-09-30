from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from uvicorn.logging import DefaultFormatter, AccessFormatter


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="IMAGEFASTAPI_")
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "myimage_fastapi"

    MAX_IMG_SIZE: int = 2 * 1024 * 1024  # 2MB as default
    MEDIA_FOLDER: str = Field("app/media/")

    LOGGING_CONFIG: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": "%(levelname)s [%(asctime)s] %(message)s", "datefmt": "%d-%m-%Y %H:%M:%S"},
            "access": {"format": "%(levelname)s [%(asctime)s] %(message)s", "datefmt": "%d-%m-%Y %H:%M:%S"},
        },
        "root": {
            "level": "INFO",
            "handlers": ["default"],
        },
        "handlers": {
            "default": {"formatter": "default", "class": "logging.StreamHandler", "stream": "ext://sys.stderr"},
            "access": {"formatter": "access", "class": "logging.StreamHandler", "stream": "ext://sys.stdout"},
        },
        "loggers": {
            "uvicorn": {"level": "INFO", "handlers": ["default"], "propagate": False},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"level": "INFO", "handlers": ["access"], "propagate": False},
        },
    }

    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings()
