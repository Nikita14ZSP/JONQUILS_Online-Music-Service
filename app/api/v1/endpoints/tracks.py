from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Path

from app.schemas.track import Track, TrackCreate, TrackUpdate, TrackSearchResults
from app.services.track_service import track_service

router = APIRouter()

@router.get("/", response_model=List[Track], summary="Получить список треков")
def read_tracks(
    skip: int = 0, 
    limit: int = Query(default=10, ge=1, le=100)
):
    """
    Получить список треков с пагинацией.
    """
    tracks = track_service.get_all_tracks(skip=skip, limit=limit)
    return tracks

@router.post("/", response_model=Track, status_code=201, summary="Создать новый трек")
def create_track(track_in: TrackCreate = Body(...)):
    """
    Создать новый трек.
    """
    return track_service.create_track(track_in=track_in)

@router.get("/search/", response_model=TrackSearchResults, summary="Поиск треков")
def search_tracks_endpoint(
    query: str = Query(..., min_length=1, description="Поисковый запрос по названию или исполнителю"),
    genre: Optional[str] = Query(None, description="Фильтр по жанру"),
    year: Optional[int] = Query(None, description="Фильтр по году выпуска"),
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    Поиск треков по названию, исполнителю, с фильтрацией по жанру и году.
    """
    results = track_service.search_tracks(query=query, genre=genre, year=year, limit=limit)
    return {"results": results}

@router.get("/{track_id}", response_model=Track, summary="Получить трек по ID")
def read_track(
    track_id: int = Path(..., title="ID трека", ge=1)
):
    """
    Получить информацию о конкретном треке по его ID.
    """
    db_track = track_service.get_track_by_id(track_id=track_id)
    if db_track is None:
        raise HTTPException(status_code=404, detail="Track not found")
    return db_track

@router.put("/{track_id}", response_model=Track, summary="Обновить трек")
def update_track(
    track_id: int = Path(..., title="ID трека", ge=1),
    track_in: TrackUpdate = Body(...)
):
    """
    Обновить информацию о треке.
    """
    updated_track = track_service.update_track(track_id=track_id, track_in=track_in)
    if updated_track is None:
        raise HTTPException(status_code=404, detail="Track not found")
    return updated_track

@router.delete("/{track_id}", response_model=Track, summary="Удалить трек")
def delete_track(
    track_id: int = Path(..., title="ID трека", ge=1)
):
    """
    Удалить трек по ID.
    """
    deleted_track = track_service.delete_track(track_id=track_id)
    if deleted_track is None:
        raise HTTPException(status_code=404, detail="Track not found")
    return deleted_track 