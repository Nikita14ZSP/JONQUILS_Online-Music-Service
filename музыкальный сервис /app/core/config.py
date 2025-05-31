from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Онлайн-музыкальный сервис API"
    API_V1_STR: str = "/api/v1"

    # Настройки для базы данных (пока не используются, но добавим для будущего)
    # POSTGRES_SERVER: str = "localhost"
    # POSTGRES_USER: str = "postgres"
    # POSTGRES_PASSWORD: str = "password"
    # POSTGRES_DB: str = "music_service_db"
    # DATABASE_URL: str | None = None

    # @validator("DATABASE_URL", pre=True)
    # def assemble_db_connection(cls, v: str | None, values: dict[str, any]) -> any:
    #     if isinstance(v, str):
    #         return v
    #     return (
    #         f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:"
    #         f"{values.get('POSTGRES_PASSWORD')}@"
    #         f"{values.get('POSTGRES_SERVER')}/"
    #         f"{values.get('POSTGRES_DB') or ''}"
    #     )

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 