from fastapi import APIRouter

from app.api.v1.endpoints import (  # noqa
    albums,
    artists,
    auth,
    genres,
    homepage,
    me,
    search,
    tracks,
    upload,
)

api_router = APIRouter()
api_router.include_router(auth.router, tags=["Auth"], prefix="/auth")
api_router.include_router(homepage.router, tags=["Homepage"])
api_router.include_router(tracks.router, tags=["Tracks"], prefix="/tracks")
api_router.include_router(artists.router, tags=["Artists"], prefix="/artists")
api_router.include_router(albums.router, tags=["Albums"], prefix="/albums")
api_router.include_router(genres.router, tags=["Genres"], prefix="/genres")
api_router.include_router(search.router, tags=["Search"], prefix="/search")
api_router.include_router(upload.router, tags=["Upload"], prefix="/upload")