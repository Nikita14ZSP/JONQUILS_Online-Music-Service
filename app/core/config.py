from pydantic_settings import BaseSettings
from functools import lru_cache
from pydantic import field_validator
from typing import Optional
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "JONQUILS - Онлайн-музыкальный сервис"
    API_V1_STR: str = "/api/v1"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "API для онлайн-музыкального сервиса с аналитикой и рекомендациями"

    # PostgreSQL настройки
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "erik"
    POSTGRES_PASSWORD: str = "2004"
    POSTGRES_DB: str = "music_service_db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        if isinstance(v, str):
            return v
        values = info.data
        return (
            f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_SERVER')}:{values.get('POSTGRES_PORT')}/"
            f"{values.get('POSTGRES_DB')}"
        )

    # ClickHouse настройки для аналитики
    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 9000
    CLICKHOUSE_USER: str = "admin"
    CLICKHOUSE_PASSWORD: str = "admin123"
    CLICKHOUSE_DATABASE: str = "jonquils_analytics"

    # Elasticsearch настройки для поиска
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_USERNAME: Optional[str] = None
    ELASTICSEARCH_PASSWORD: Optional[str] = None

    # Redis настройки для кеширования
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    # S3/MinIO настройки для хранения файлов
    S3_ENDPOINT_URL: str = "http://localhost:9002"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin123"
    S3_REGION: str = "us-east-1"
    S3_TRACKS_BUCKET: str = "tracks"
    S3_COVERS_BUCKET: str = "covers"
    S3_PLAYLISTS_BUCKET: str = "playlists"
    S3_TEMP_BUCKET: str = "temp"

    # Настройки безопасности
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Настройки для файлов
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB для треков
    MAX_COVER_SIZE: int = 10 * 1024 * 1024  # 10MB для обложек

    # ETL и Airflow настройки
    AIRFLOW_WEBSERVER_URL: str = "http://localhost:8080"
    AIRFLOW_USERNAME: str = "admin"
    AIRFLOW_PASSWORD: str = "admin123"
    ETL_BATCH_SIZE: int = 1000
    ETL_RETRY_ATTEMPTS: int = 3

    # CORS настройки
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "allow"  # Разрешаем дополнительные поля

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 