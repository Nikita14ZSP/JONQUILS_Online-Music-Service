from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.album import Album, AlbumCreate, AlbumUpdate
from app.services.album_service import AlbumService
from app.services.artist_service import ArtistService
from app.services.search_service import SearchService
from app.db.database import get_db

router = APIRouter()

async def get_album_service(db: AsyncSession = Depends(get_db)) -> AlbumService:
    return AlbumService(db)

async def get_artist_service(db: AsyncSession = Depends(get_db)) -> ArtistService:
    return ArtistService(db)

async def get_search_service(db: AsyncSession = Depends(get_db)) -> SearchService:
    return SearchService(db)

@router.get("/", response_model=List[Album], summary="Получить список альбомов")
async def read_albums(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    album_service: AlbumService = Depends(get_album_service)
):
    """
    Получить список альбомов с пагинацией.
    """
    albums = await album_service.get_albums(skip=skip, limit=limit)
    return albums

@router.post("/", response_model=Album, status_code=201, summary="Создать новый альбом")
async def create_album(
    album_in: AlbumCreate = Body(...),
    album_service: AlbumService = Depends(get_album_service),
    artist_service: ArtistService = Depends(get_artist_service),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Создать новый альбом.
    """
    created_album = await album_service.create_album(album_data=album_in)
    
    if created_album:
        artist = await artist_service.get_artist_by_id(created_album.artist_id)
        artist_name = artist.name if artist else ""
        await search_service.index_album(album=created_album, artist_name=artist_name)
    
    return created_album

@router.get("/search/", response_model=List[Album], summary="Поиск альбомов")
async def search_albums(
    query: str = Query(..., min_length=1, description="Поисковый запрос по названию альбома"),
    limit: int = Query(default=10, ge=1, le=50),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Поиск альбомов по названию.
    """
    results = await search_service.multi_entity_search(query=query, limit=limit)
    albums_found = results.get("albums", [])
    
    return albums_found

@router.get("/{album_id}", response_model=Album, summary="Получить альбом по ID")
async def read_album(
    album_id: int = Path(..., title="ID альбома", ge=1),
    album_service: AlbumService = Depends(get_album_service)
):
    """
    Получить информацию о конкретном альбоме по его ID.
    """
    db_album = await album_service.get_album_by_id(album_id=album_id)
    if db_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    return db_album

@router.put("/{album_id}", response_model=Album, summary="Обновить альбом")
async def update_album(
    album_id: int = Path(..., title="ID альбома", ge=1),
    album_update: AlbumUpdate = Body(...),
    album_service: AlbumService = Depends(get_album_service),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Обновить информацию об альбоме.
    """
    updated_album = await album_service.update_album(album_id=album_id, album_data=album_update)
    if updated_album is None:
        raise HTTPException(status_code=404, detail="Album not found")
    
    if updated_album:
        artist = await album_service.db.get_artist_by_id(updated_album.artist_id)
        artist_name = artist.name if artist else ""
        await search_service.index_album(album=updated_album, artist_name=artist_name)
    
    return updated_album

@router.delete("/{album_id}", status_code=204, summary="Удалить альбом")
async def delete_album(
    album_id: int = Path(..., title="ID альбома", ge=1),
    album_service: AlbumService = Depends(get_album_service),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Удалить альбом.
    """
    deleted = await album_service.delete_album(album_id=album_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Album not found")
    
    await search_service.delete_entity(index="albums", entity_id=album_id)

@router.get("/{album_id}/tracks", response_model=List[dict], summary="Получить треки альбома")
async def get_album_tracks(
    album_id: int = Path(..., title="ID альбома", ge=1),
    album_service: AlbumService = Depends(get_album_service)
):
    """
    Получить треки конкретного альбома.
    """
    tracks = await album_service.get_album_tracks(album_id=album_id)
    return tracks

@router.get("/artist/{artist_id}", response_model=List[Album], summary="Получить альбомы исполнителя")
async def get_albums_by_artist(
    artist_id: int = Path(..., title="ID исполнителя", ge=1),
    album_service: AlbumService = Depends(get_album_service)
):
    """
    Получить все альбомы конкретного исполнителя.
    """
    albums = await album_service.get_albums_by_artist(artist_id=artist_id)
    return albums

@router.get("/popular/", response_model=List[Album], summary="Получить популярные альбомы")
async def get_popular_albums(
    limit: int = Query(default=20, ge=1, le=100),
    album_service: AlbumService = Depends(get_album_service)
):
    """
    Получить список популярных альбомов.
    """
    return await album_service.get_popular_albums(limit=limit)

@router.get("/recent/", response_model=List[Album], summary="Получить недавние альбомы")
async def get_recent_albums(
    limit: int = Query(default=20, ge=1, le=100),
    album_service: AlbumService = Depends(get_album_service)
):
    """
    Получить недавно выпущенные альбомы.
    """
    return await album_service.get_recent_albums(limit=limit) 
