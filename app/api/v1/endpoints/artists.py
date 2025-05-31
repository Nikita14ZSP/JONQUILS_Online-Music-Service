from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.artist import Artist, ArtistCreate, ArtistUpdate
from app.services.artist_service import ArtistService
from app.db.database import get_db

router = APIRouter()

async def get_artist_service(db: AsyncSession = Depends(get_db)) -> ArtistService:
    return ArtistService(db)

@router.get("/", response_model=List[Artist], summary="Получить список исполнителей")
async def read_artists(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    artist_service: ArtistService = Depends(get_artist_service)
):
    """
    Получить список исполнителей с пагинацией.
    """
    artists = await artist_service.get_artists(skip=skip, limit=limit)
    return artists

@router.post("/", response_model=Artist, status_code=201, summary="Создать нового исполнителя")
async def create_artist(
    artist_in: ArtistCreate = Body(...),
    artist_service: ArtistService = Depends(get_artist_service)
):
    """
    Создать нового исполнителя.
    """
    return await artist_service.create_artist(artist_data=artist_in)

@router.get("/search/", response_model=List[Artist], summary="Поиск исполнителей")
async def search_artists(
    query: str = Query(..., min_length=1, description="Поисковый запрос по имени исполнителя"),
    limit: int = Query(default=10, ge=1, le=50),
    artist_service: ArtistService = Depends(get_artist_service)
):
    """
    Поиск исполнителей по имени.
    """
    results = await artist_service.search_artists(query=query, limit=limit)
    return results

@router.get("/{artist_id}", response_model=Artist, summary="Получить исполнителя по ID")
async def read_artist(
    artist_id: int = Path(..., title="ID исполнителя", ge=1),
    artist_service: ArtistService = Depends(get_artist_service)
):
    """
    Получить информацию о конкретном исполнителе по его ID.
    """
    db_artist = await artist_service.get_artist_by_id(artist_id=artist_id)
    if db_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    return db_artist

@router.put("/{artist_id}", response_model=Artist, summary="Обновить исполнителя")
async def update_artist(
    artist_id: int = Path(..., title="ID исполнителя", ge=1),
    artist_update: ArtistUpdate = Body(...),
    artist_service: ArtistService = Depends(get_artist_service)
):
    """
    Обновить информацию об исполнителе.
    """
    updated_artist = await artist_service.update_artist(artist_id=artist_id, artist_data=artist_update)
    if updated_artist is None:
        raise HTTPException(status_code=404, detail="Artist not found")
    return updated_artist

@router.delete("/{artist_id}", status_code=204, summary="Удалить исполнителя")
async def delete_artist(
    artist_id: int = Path(..., title="ID исполнителя", ge=1),
    artist_service: ArtistService = Depends(get_artist_service)
):
    """
    Удалить исполнителя.
    """
    deleted = await artist_service.delete_artist(artist_id=artist_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Artist not found")

@router.get("/{artist_id}/tracks", response_model=List[dict], summary="Получить треки исполнителя")
async def get_artist_tracks(
    artist_id: int = Path(..., title="ID исполнителя", ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    artist_service: ArtistService = Depends(get_artist_service)
):
    """
    Получить треки конкретного исполнителя.
    """
    tracks = await artist_service.get_artist_tracks(artist_id=artist_id, limit=limit)
    return tracks

@router.get("/{artist_id}/albums", response_model=List[dict], summary="Получить альбомы исполнителя")
async def get_artist_albums(
    artist_id: int = Path(..., title="ID исполнителя", ge=1),
    artist_service: ArtistService = Depends(get_artist_service)
):
    """
    Получить альбомы конкретного исполнителя.
    """
    albums = await artist_service.get_artist_albums(artist_id=artist_id)
    return albums

@router.get("/popular/", response_model=List[Artist], summary="Получить популярных исполнителей")
async def get_popular_artists(
    limit: int = Query(default=20, ge=1, le=100),
    artist_service: ArtistService = Depends(get_artist_service)
):
    """
    Получить список популярных исполнителей.
    """
    return await artist_service.get_popular_artists(limit=limit) 