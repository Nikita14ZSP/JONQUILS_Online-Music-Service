from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_activity import ListeningEvent, AnalyticsStats
from app.services.analytics_service import AnalyticsService
from app.db.database import get_db

router = APIRouter()

async def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)

@router.post("/listening-events", status_code=201, summary="Записать событие прослушивания")
async def record_listening_event(
    event: ListeningEvent = Body(...),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Записать событие прослушивания трека.
    """
    await analytics_service.record_listening_event(
        user_id=event.user_id,
        track_id=event.track_id,
        listened_at=event.listened_at,
        duration_listened=event.duration_listened,
        source=event.source
    )
    return {"message": "Listening event recorded"}

@router.get("/popular-tracks", summary="Получить популярные треки")
async def get_popular_tracks_analytics(
    period: str = Query(default="week", regex="^(day|week|month|year)$"),
    limit: int = Query(default=20, ge=1, le=100),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Получить популярные треки за период.
    """
    tracks = await analytics_service.get_popular_tracks(period=period, limit=limit)
    return {"period": period, "popular_tracks": tracks}

@router.get("/popular-artists", summary="Получить популярных исполнителей")
async def get_popular_artists_analytics(
    period: str = Query(default="week", regex="^(day|week|month|year)$"),
    limit: int = Query(default=20, ge=1, le=100),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Получить популярных исполнителей за период.
    """
    artists = await analytics_service.get_popular_artists(period=period, limit=limit)
    return {"period": period, "popular_artists": artists}

@router.get("/user/{user_id}/stats", response_model=AnalyticsStats, summary="Статистика пользователя")
async def get_user_analytics_stats(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    period: str = Query(default="week", regex="^(day|week|month|year)$"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Получить статистику прослушиваний пользователя.
    """
    stats = await analytics_service.get_user_stats(user_id=user_id, period=period)
    return stats

@router.get("/user/{user_id}/listening-history", summary="История прослушиваний пользователя")
async def get_user_listening_history_analytics(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    from_date: Optional[datetime] = Query(None, description="Начальная дата"),
    to_date: Optional[datetime] = Query(None, description="Конечная дата"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Получить историю прослушиваний пользователя с фильтрацией по дате.
    """
    history = await analytics_service.get_user_listening_history(
        user_id=user_id, 
        limit=limit,
        from_date=from_date,
        to_date=to_date
    )
    return {
        "user_id": user_id,
        "listening_history": history,
        "total_count": len(history)
    }

@router.get("/genres/stats", summary="Статистика по жанрам")
async def get_genre_stats(
    period: str = Query(default="month", regex="^(day|week|month|year)$"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Получить статистику прослушиваний по жанрам.
    """
    stats = await analytics_service.get_genre_stats(period=period)
    return {"period": period, "genre_stats": stats}

@router.get("/trends", summary="Музыкальные тренды")
async def get_music_trends(
    period: str = Query(default="week", regex="^(day|week|month|year)$"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Получить музыкальные тренды и аналитику.
    """
    trends = await analytics_service.get_music_trends(period=period)
    return {"period": period, "trends": trends}

@router.get("/dashboard", summary="Дашборд аналитики")
async def get_analytics_dashboard(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Получить общую аналитику для дашборда.
    """
    dashboard_data = await analytics_service.get_dashboard_data()
    return dashboard_data

@router.get("/recommendations/similar-users/{user_id}", summary="Похожие пользователи")
async def get_similar_users(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Найти пользователей с похожими музыкальными предпочтениями.
    """
    similar_users = await analytics_service.get_similar_users(user_id=user_id, limit=limit)
    return {"user_id": user_id, "similar_users": similar_users}

# Новые эндпоинты для расширенной ClickHouse-аналитики

@router.get("/realtime/platform-stats", summary="Статистика платформы в реальном времени")
async def get_realtime_platform_stats(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Получить статистику платформы в реальном времени из ClickHouse.
    """
    stats = await analytics_service.get_platform_statistics()
    return {"platform_stats": stats}

@router.get("/realtime/active-users", summary="Активные пользователи в реальном времени")
async def get_realtime_active_users(
    minutes: int = Query(default=60, ge=1, le=1440, description="Период в минутах"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Получить количество активных пользователей за последние N минут.
    """
    active_users = await analytics_service.get_active_users_count(minutes=minutes)
    return {"minutes": minutes, "active_users": active_users}

@router.get("/advanced/track-analytics/{track_id}", summary="Расширенная аналитика трека")
async def get_advanced_track_analytics(
    track_id: int = Path(..., title="ID трека", ge=1),
    period: str = Query(default="week", regex="^(day|week|month|year)$"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Получить расширенную аналитику трека из ClickHouse.
    """
    analytics = await analytics_service.get_track_analytics(track_id=track_id, period=period)
    return {"track_id": track_id, "period": period, "analytics": analytics}

@router.get("/advanced/user-analytics/{user_id}", summary="Расширенная аналитика пользователя")
async def get_advanced_user_analytics(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    period: str = Query(default="week", regex="^(day|week|month|year)$"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Получить расширенную аналитику пользователя из ClickHouse.
    """
    analytics = await analytics_service.get_user_analytics(user_id=user_id, period=period)
    return {"user_id": user_id, "period": period, "analytics": analytics}

@router.post("/events/search", status_code=201, summary="Записать событие поиска")
async def record_search_event(
    user_id: int = Body(...),
    query: str = Body(...),
    results_count: int = Body(default=0),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Записать событие поиска пользователя.
    """
    await analytics_service.record_search_event(
        user_id=user_id,
        query=query,
        results_count=results_count
    )
    return {"message": "Search event recorded"}

@router.post("/events/playlist", status_code=201, summary="Записать событие с плейлистом")
async def record_playlist_event(
    user_id: int = Body(...),
    playlist_id: int = Body(...),
    action: str = Body(..., regex="^(create|update|delete|add_track|remove_track)$"),
    track_id: Optional[int] = Body(default=None),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Записать событие действия с плейлистом.
    """
    await analytics_service.record_playlist_event(
        user_id=user_id,
        playlist_id=playlist_id,
        action=action,
        track_id=track_id
    )
    return {"message": "Playlist event recorded"}

@router.get("/performance/summary", summary="Сводка производительности аналитики")
async def get_performance_summary(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Получить сводку производительности различных источников данных.
    """
    # Сравним производительность PostgreSQL vs ClickHouse для некоторых запросов
    import time
    
    results = {}
    
    # Тест популярных треков
    start_time = time.time()
    pg_popular = await analytics_service.get_popular_tracks(period="week", limit=10)
    pg_time = time.time() - start_time
    
    start_time = time.time()
    ch_popular = await analytics_service.get_popular_tracks_clickhouse(period="week", limit=10)
    ch_time = time.time() - start_time
    
    results["popular_tracks"] = {
        "postgresql_time": round(pg_time, 4),
        "clickhouse_time": round(ch_time, 4),
        "performance_gain": round(pg_time / ch_time if ch_time > 0 else 0, 2)
    }
    
    return {"performance_comparison": results}