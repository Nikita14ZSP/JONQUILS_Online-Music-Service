"""
Эндпоинты для аналитики
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import time
from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_activity import ListeningEvent, AnalyticsStats
from app.services.analytics_service import AnalyticsService
from app.db.database import get_db
from app.services.clickhouse_service import clickhouse_service
from app.core.deps import get_current_user
from app.db.models import User

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
        listened_at=event.timestamp,
        duration_listened=event.play_duration_ms,
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
    tracks = await analytics_service.get_top_tracks(limit=limit)
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
    artists = await analytics_service.get_top_artists(period=period, limit=limit)
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

# ClickHouse аналитика - новые эндпоинты

@router.get("/clickhouse/api-stats", summary="Статистика API запросов (ClickHouse)")
async def get_clickhouse_api_stats(
    days: int = Query(7, ge=1, le=90, description="Количество дней для анализа")
):
    """
    Получение статистики API запросов за указанное количество дней из ClickHouse.
    """
    try:
        stats = await clickhouse_service.get_api_stats(days=days)
        return {
            "status": "success",
            "data": stats,
            "period_days": days,
            "source": "clickhouse"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

@router.get("/clickhouse/track/{track_id}/stats", summary="Статистика трека (ClickHouse)")
async def get_clickhouse_track_stats(
    track_id: int,
    days: int = Query(30, ge=1, le=365, description="Количество дней для анализа")
):
    """
    Получение статистики для конкретного трека из ClickHouse.
    """
    try:
        stats = await clickhouse_service.get_track_stats(track_id=track_id, days=days)
        return {
            "status": "success",
            "data": stats,
            "track_id": track_id,
            "period_days": days,
            "source": "clickhouse"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики трека: {str(e)}")

@router.get("/clickhouse/artist/{artist_id}/stats", summary="Статистика артиста (ClickHouse)")
async def get_clickhouse_artist_stats(
    artist_id: int
):
    """
    Получение статистики для артиста из ClickHouse.
    """
    try:
        stats = await clickhouse_service.get_artist_stats(artist_id=artist_id)
        return {
            "status": "success",
            "data": stats,
            "artist_id": artist_id,
            "source": "clickhouse"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики артиста: {str(e)}")

@router.post("/clickhouse/track/{track_id}/play", summary="Записать воспроизведение (ClickHouse)")
async def log_clickhouse_track_play(
    track_id: int,
    duration_ms: Optional[int] = Body(None),
    position_ms: Optional[int] = Body(None),
    platform: str = Body("web"),
    artist_id: int = Body(1),  # Временно фиксированное значение
    user_id: Optional[int] = Body(None)
):
    """
    Логирование воспроизведения трека в ClickHouse.
    """
    try:
        await clickhouse_service.log_track_action(
            track_id=track_id,
            artist_id=artist_id,
            action="play",
            user_id=user_id,
            duration_played_ms=duration_ms,
            track_position_ms=position_ms,
            platform=platform
        )
        
        return {"status": "success", "message": "Воспроизведение зарегистрировано в ClickHouse"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка записи воспроизведения: {str(e)}")

@router.post("/clickhouse/search", summary="Записать поисковый запрос (ClickHouse)")
async def log_clickhouse_search(
    query: str = Body(...),
    results_count: int = Body(...),
    search_type: str = Body("general"),
    clicked_result_id: Optional[int] = Body(None),
    clicked_result_type: Optional[str] = Body(None),
    user_id: Optional[int] = Body(None)
):
    """
    Логирование поискового запроса в ClickHouse.
    """
    try:
        await clickhouse_service.log_search_action(
            query=query,
            results_count=results_count,
            search_type=search_type,
            user_id=user_id,
            clicked_result_id=clicked_result_id,
            clicked_result_type=clicked_result_type
        )
        
        return {"status": "success", "message": "Поисковый запрос зарегистрирован в ClickHouse"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка записи поиска: {str(e)}")

@router.get("/clickhouse/health", summary="Проверка состояния ClickHouse")
async def clickhouse_health_check():
    """
    Проверка работоспособности системы аналитики ClickHouse.
    """
    try:
        is_connected = await clickhouse_service.test_connection()
        return {
            "status": "success" if is_connected else "error",
            "clickhouse_connected": is_connected,
            "message": "ClickHouse аналитика работает" if is_connected else "ClickHouse недоступен"
        }
    except Exception as e:
        return {
            "status": "error",
            "clickhouse_connected": False,
            "message": f"Ошибка подключения к ClickHouse: {str(e)}"
        }

@router.get("/user/analytics", summary="Получить аналитику пользователя")
async def get_user_analytics(
    current_user: User = Depends(get_current_user),
    days: int = Query(default=30, ge=1, le=365, description="Количество дней для анализа")
):
    """
    Получить аналитику активности текущего пользователя:
    - История поисков
    - Топ треков по прослушиваниям
    - Активность по времени
    - Статистика использования
    """
    try:
        user_id = current_user.id
        
        # Получаем историю поисков
        search_history = await clickhouse_service.get_user_search_history(user_id, days)
        
        # Получаем топ треков пользователя
        top_tracks = await clickhouse_service.get_user_top_tracks(user_id, days)
        
        # Получаем статистику активности
        activity_stats = await clickhouse_service.get_user_activity_stats(user_id, days)
        
        # Получаем активность по времени
        activity_timeline = await clickhouse_service.get_user_activity_timeline(user_id, days)
        
        return {
            "user_id": user_id,
            "period_days": days,
            "search_history": search_history,
            "top_tracks": top_tracks,
            "activity_stats": activity_stats,
            "activity_timeline": activity_timeline
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения аналитики пользователя: {str(e)}")

@router.get("/user/search-history", summary="Получить историю поисков пользователя")
async def get_user_search_history(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=200, description="Количество записей")
):
    """
    Получить последние поисковые запросы пользователя.
    """
    try:
        user_id = current_user.id
        search_history = await clickhouse_service.get_user_search_history(user_id, limit=limit)
        
        return {
            "user_id": user_id,
            "search_history": search_history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения истории поисков: {str(e)}")

@router.get("/user/{user_id}", summary="Получить аналитику конкретного пользователя")
async def get_user_analytics_by_id(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    period: str = Query(default="30d", regex="^(7d|30d|90d)$", description="Период: 7d, 30d, 90d"),
    current_user: User = Depends(get_current_user)
):
    """
    Получить аналитику активности пользователя по ID:
    - История поисков
    - Топ треков по прослушиваниям  
    - Активность по времени
    - Статистика использования
    """
    try:
        # Проверяем, что пользователь запрашивает свою аналитику или является администратором
        if current_user.id != user_id and current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        # Конвертируем период в дни
        days_map = {'7d': 7, '30d': 30, '90d': 90}
        days = days_map.get(period, 30)
        
        # Получаем статистику поисков
        search_history = await clickhouse_service.get_user_search_history(user_id, days)
        search_count = len(search_history)
        unique_queries = len(set(item['search_query'] for item in search_history))
        clicked_searches = sum(1 for item in search_history if item.get('clicked_result_id'))
        click_through_rate = clicked_searches / search_count if search_count > 0 else 0
        avg_results = sum(item['results_count'] for item in search_history) / search_count if search_count > 0 else 0
        
        # Получаем топ треки пользователя
        top_tracks_data = await clickhouse_service.get_user_top_tracks(user_id, days)
        
        # Получаем общую статистику прослушиваний
        listening_data = await clickhouse_service.get_user_listening_stats(user_id, days)
        total_plays = listening_data.get('total_plays', 0)
        total_duration = listening_data.get('total_duration_sec', 0)
        unique_tracks = listening_data.get('unique_tracks', 0)
        avg_session_length = listening_data.get('avg_session_length_sec', 0)
        
        # Получаем активность по дням (последние 30 дней)
        activity_timeline = await clickhouse_service.get_user_activity_timeline(user_id, min(days, 30))
        
        # Подсчитываем общую активность
        active_days = len([day for day in activity_timeline if day.get('search_count', 0) + day.get('listening_count', 0) > 0])
        total_sessions = sum(day.get('session_count', 1) for day in activity_timeline)
        total_activity = search_count + total_plays
        avg_daily_activity = total_activity / days if days > 0 else 0
        
        # Формируем топ треки с дополнительной информацией
        formatted_top_tracks = []
        max_plays = max([track.get('play_count', 0) for track in top_tracks_data]) if top_tracks_data else 1
        
        for track in top_tracks_data[:10]:
            formatted_top_tracks.append({
                'track_id': track.get('track_id'),
                'title': track.get('title', f"Track {track.get('track_id')}"),
                'artist_name': track.get('artist_name', 'Unknown Artist'),
                'play_count': track.get('play_count', 0),
                'total_duration': track.get('total_duration_sec', 0),
                'percentage': (track.get('play_count', 0) / max_plays * 100) if max_plays > 0 else 0
            })
        
        # Формируем историю поисков
        formatted_search_history = []
        for search in search_history[-10:]:  # Последние 10 поисков
            formatted_search_history.append({
                'query': search.get('search_query', ''),
                'timestamp': search.get('timestamp', ''),
                'results_count': search.get('results_count', 0),
                'clicked': bool(search.get('clicked_result_id'))
            })
        
        # Формируем временную линию активности
        formatted_timeline = []
        for day in activity_timeline:
            formatted_timeline.append({
                'date': day.get('date', ''),
                'search_count': day.get('search_count', 0),
                'listening_count': day.get('listening_count', 0)
            })
        
        return {
            "search_stats": {
                "total_searches": search_count,
                "unique_queries": unique_queries,
                "avg_results_per_search": round(avg_results, 1),
                "click_through_rate": round(click_through_rate, 3)
            },
            "listening_stats": {
                "total_plays": total_plays,
                "total_duration": total_duration,
                "unique_tracks": unique_tracks,
                "avg_session_length": avg_session_length
            },
            "activity_stats": {
                "active_days": active_days,
                "total_sessions": total_sessions,
                "avg_daily_activity": round(avg_daily_activity, 1)
            },
            "search_history": formatted_search_history,
            "top_tracks": formatted_top_tracks,
            "activity_timeline": formatted_timeline
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user analytics: {str(e)}")