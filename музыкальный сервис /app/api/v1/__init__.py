from fastapi import APIRouter

from app.api.v1.endpoints import tracks, analytics #, artists, albums # Раскомментируем по мере добавления

api_router = APIRouter()
api_router.include_router(tracks.router, prefix="/tracks", tags=["Tracks"])
# api_router.include_router(artists.router, prefix="/artists", tags=["Artists"]) # Заглушка
# api_router.include_router(albums.router, prefix="/albums", tags=["Albums"]) # Заглушка
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"]) 