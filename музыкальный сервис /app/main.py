from fastapi import FastAPI

from app.api.v1 import api_router as api_router_v1
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(api_router_v1, prefix=settings.API_V1_STR)

@app.get("/ping", summary="Check if the API is alive")
def pong():
    """
    Sanity check for the API.
    """
    return {"ping": "pong!"} 