from fastapi import APIRouter

from app.api.v1.endpoints import (  # noqa
    albums,
    artists,
    auth,
    search,
    tracks,
    upload,
    users,
    analytics
)

api_router = APIRouter()
api_router.include_router(auth.router, tags=["Auth"], prefix="/auth")
api_router.include_router(tracks.router, tags=["Tracks"], prefix="/tracks")
api_router.include_router(artists.router, tags=["Artists"], prefix="/artists")
api_router.include_router(albums.router, tags=["Albums"], prefix="/albums")
api_router.include_router(search.router, tags=["Search"], prefix="/search")
api_router.include_router(upload.router, tags=["Upload"], prefix="/upload")
api_router.include_router(users.router, tags=["Users"], prefix="/users")
api_router.include_router(analytics.router, tags=["Analytics"], prefix="/analytics")