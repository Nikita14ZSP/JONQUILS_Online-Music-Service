from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.track import Track, TrackCreate, TrackUpdate, TrackSearchResults
from app.services.track_service import TrackService
from app.services.analytics_service import AnalyticsService
from app.services.search_service import SearchService
from app.db.database import get_db

router = APIRouter()

async def get_track_service(db: AsyncSession = Depends(get_db)) -> TrackService:
    return TrackService(db)

async def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)

async def get_search_service(db: AsyncSession = Depends(get_db)) -> SearchService:
    return SearchService(db)

@router.get("/", response_model=List[Track], summary="Получить список треков")
async def read_tracks(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    track_service: TrackService = Depends(get_track_service)
):
    """
    Получить список треков с пагинацией.
    """
    tracks = await track_service.get_tracks(skip=skip, limit=limit)
    return tracks

@router.post("/", response_model=Track, status_code=201, summary="Создать новый трек")
async def create_track(
    track_in: TrackCreate = Body(...),
    track_service: TrackService = Depends(get_track_service)
):
    """
    Создать новый трек.
    """
    return await track_service.create_track(track_data=track_in)

@router.get("/search/", response_model=TrackSearchResults, summary="Поиск треков")
async def search_tracks_endpoint(
    query: str = Query(..., min_length=1, description="Поисковый запрос по названию или исполнителю"),
    genre: Optional[str] = Query(None, description="Фильтр по жанру"),
    year: Optional[int] = Query(None, description="Фильтр по году выпуска"),
    artist: Optional[str] = Query(None, description="Фильтр по исполнителю"),
    album: Optional[str] = Query(None, description="Фильтр по альбому"),
    limit: int = Query(default=10, ge=1, le=50),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Поиск треков по названию, исполнителю, с фильтрацией по жанру и году.
    """
    results = await search_service.search_tracks(
        query=query, 
        genre=genre, 
        year=year,
        artist=artist,
        album=album,
        limit=limit
    )
    return TrackSearchResults(results=results, total=len(results))

@router.get("/{track_id}", response_model=Track, summary="Получить трек по ID")
async def read_track(
    track_id: int = Path(..., title="ID трека", ge=1),
    track_service: TrackService = Depends(get_track_service)
):
    """
    Получить информацию о конкретном треке по его ID.
    """
    db_track = await track_service.get_track_by_id(track_id=track_id)
    if db_track is None:
        raise HTTPException(status_code=404, detail="Track not found")
    return db_track

@router.put("/{track_id}", response_model=Track, summary="Обновить трек")
async def update_track(
    track_id: int = Path(..., title="ID трека", ge=1),
    track_update: TrackUpdate = Body(...),
    track_service: TrackService = Depends(get_track_service)
):
    """
    Обновить информацию о треке.
    """
    updated_track = await track_service.update_track(track_id=track_id, track_data=track_update)
    if updated_track is None:
        raise HTTPException(status_code=404, detail="Track not found")
    return updated_track

@router.delete("/{track_id}", status_code=204, summary="Удалить трек")
async def delete_track(
    track_id: int = Path(..., title="ID трека", ge=1),
    track_service: TrackService = Depends(get_track_service)
):
    """
    Удалить трек.
    """
    deleted = await track_service.delete_track(track_id=track_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Track not found")

@router.post("/{track_id}/listen", status_code=204, summary="Записать прослушивание трека")
async def record_track_listen(
    track_id: int = Path(..., title="ID трека", ge=1),
    user_id: int = Body(..., embed=True),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Записать событие прослушивания трека для аналитики.
    """
    await analytics_service.record_listening_event(
        user_id=user_id,
        track_id=track_id
    )

@router.get("/popular/", response_model=List[Track], summary="Получить популярные треки")
async def get_popular_tracks(
    limit: int = Query(default=20, ge=1, le=100),
    track_service: TrackService = Depends(get_track_service)
):
    """
    Получить список популярных треков на основе количества прослушиваний.
    """
    return await track_service.get_popular_tracks(limit=limit)

@router.get("/recommendations/{user_id}", response_model=List[Track], summary="Получить рекомендации для пользователя")
async def get_track_recommendations(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    track_service: TrackService = Depends(get_track_service)
):
    """
    Получить персональные рекомендации треков для пользователя.
    """
    recommendations = await track_service.get_recommendations_for_user(user_id=user_id, limit=limit)
    return recommendations