from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from starlette.routing import Mount
import uvicorn
import logging
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1 import api_router as api_router_v1
from app.core.config import settings
from app.services.clickhouse_service import ClickHouseService
from app.core.analytics_middleware import AnalyticsMiddleware

logger = logging.getLogger(__name__)

# Добавляем инструментор Prometheus перед созданием FastAPI app
# Он автоматически зарегистрирует метрики по умолчанию
instrumentator = Instrumentator()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Онлайн музыкальный сервис с аналитикой и рекомендациями",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(AnalyticsMiddleware)


app.mount("/static", StaticFiles(directory="app/static"), name="static")


async def initialize_clickhouse():
    """Инициализация таблиц ClickHouse при запуске приложения."""
    try:
        from app.services.clickhouse_service import clickhouse_service
        
        # Создаем таблицы ClickHouse
        await clickhouse_service.create_tables()
        logger.info("ClickHouse tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ClickHouse: {e}")
        
@app.on_event("startup")
async def startup_event():
    """События при запуске приложения."""
    await initialize_clickhouse()
    instrumentator.expose(app, include_in_schema=False, tags=['metrics'])

# Инструментируем приложение ПОСЛЕ добавления всех роутов и middleware, но ДО app.on_event("startup")
# чтобы метрики middleware тоже собирались, если это возможно.
# Однако, если expose вызывается в startup, то instrument нужно вызвать до startup.
# Для простоты, пока разместим instrument перед startup.
# Если будут проблемы с тем, что expose не находит метрики, можно попробовать instrument(app).expose(app) в startup_event
# или instrument(app) перед startup_event, а expose(app) - в startup_event.
# Наиболее безопасный вариант - instrument перед включением роутов, expose - в startup
instrumentator.instrument(app)

app.include_router(api_router_v1, prefix=settings.API_V1_STR)

@app.get("/", summary="Главная страница API")
def root():
    """
    Главная страница API музыкального сервиса.
    """
    return {
        "message": "JONQUILS Online Music Service API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", summary="Проверка состояния API")
def health_check():
    """
    Проверка работоспособности API.
    """
    return {"status": "healthy", "service": "music-api"}

@app.get("/ping", summary="Check if the API is alive")
def pong():
    """
    Sanity check for the API.
    """
    return {"ping": "pong!"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)