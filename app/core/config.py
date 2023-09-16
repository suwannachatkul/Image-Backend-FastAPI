from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    DB_USER: str = Field(env='IMAGEFASTAPI_DB_USER')
    DB_PASS: str = Field(env='IMAGEFASTAPI_DB_PASSWORD')
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "myimage_fastapi"

    @property
    def DATABASE_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()