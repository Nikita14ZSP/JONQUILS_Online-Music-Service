from fastapi import APIRouter

from app.api.v1.endpoints import tracks, analytics, artists, albums, users, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(tracks.router, prefix="/tracks", tags=["Tracks"])
api_router.include_router(artists.router, prefix="/artists", tags=["Artists"])
api_router.include_router(albums.router, prefix="/albums", tags=["Albums"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])