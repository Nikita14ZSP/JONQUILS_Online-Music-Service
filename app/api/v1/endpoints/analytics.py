from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import time
from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends

from app.schemas.user_activity import ListeningEvent, AnalyticsStats
from app.services.clickhouse_service import clickhouse_service
from app.core.deps import get_current_user
from app.db.models import User

router = APIRouter()

@router.post("/listening-events", status_code=201, summary="Записать событие прослушивания")
async def record_listening_event(
    event: ListeningEvent = Body(...)
):
    try:
        await clickhouse_service.log_track_action(
            track_id=event.track_id,
            artist_id=event.artist_id or 1,  
            action="play",
            user_id=event.user_id,
            duration_played_ms=event.play_duration_ms,
            platform=event.source or "web",
            device_type=event.device_type or "unknown"
        )
        return {"message": "Listening event recorded in ClickHouse"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record listening event: {str(e)}")

@router.get("/popular-tracks", summary="Получить популярные треки")
async def get_popular_tracks_analytics(
    period: str = Query(default="week", regex="^(day|week|month|year)$"),
    limit: int = Query(default=20, ge=1, le=100)
):
    try:
        period_days = {"day": 1, "week": 7, "month": 30, "year": 365}
        days = period_days.get(period, 7)
        
        query = """
        SELECT 
            track_id,
            artist_id,
            count() as play_count,
            uniq(user_id) as unique_listeners,
            sum(duration_played_ms) as total_duration
        FROM track_analytics 
        WHERE action = 'play' 
            AND timestamp >= subtractDays(now(), {days})
        GROUP BY track_id, artist_id
        ORDER BY play_count DESC, unique_listeners DESC
        LIMIT {limit}
        """.format(days=days, limit=limit)
        
        result = await clickhouse_service.execute_query(query)
        
        tracks = []
        for row in result:
            tracks.append({
                "track_id": row[0],
                "artist_id": row[1],
                "title": f"Track {row[0]}",  
                "artist_name": f"Artist {row[1]}",  
                "play_count": row[2],
                "unique_listeners": row[3],
                "total_duration_ms": row[4]
            })
        
        return {"period": period, "popular_tracks": tracks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get popular tracks: {str(e)}")

@router.get("/popular-artists", summary="Получить популярных исполнителей")
async def get_popular_artists_analytics(
    period: str = Query(default="week", regex="^(day|week|month|year)$"),
    limit: int = Query(default=20, ge=1, le=100)
):
    try:
        period_days = {"day": 1, "week": 7, "month": 30, "year": 365}
        days = period_days.get(period, 7)
        
        query = """
        SELECT 
            artist_id,
            count() as total_plays,
            uniq(user_id) as unique_listeners,
            uniq(track_id) as unique_tracks
        FROM track_analytics 
        WHERE action = 'play' 
            AND timestamp >= subtractDays(now(), {days})
        GROUP BY artist_id
        ORDER BY total_plays DESC, unique_listeners DESC
        LIMIT {limit}
        """.format(days=days, limit=limit)
        
        result = await clickhouse_service.execute_query(query)
        
        artists = []
        for row in result:
            artists.append({
                "artist_id": row[0],
                "artist_name": f"Artist {row[0]}",  
                "total_plays": row[1],
                "unique_listeners": row[2],
                "unique_tracks": row[3]
            })
        
        return {"period": period, "popular_artists": artists}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get popular artists: {str(e)}")

@router.get("/user/{user_id}/stats", summary="Статистика пользователя")
async def get_user_analytics_stats(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    period: str = Query(default="week", regex="^(day|week|month|year)$")
):
    try:
        listening_stats = await clickhouse_service.get_user_listening_stats(user_id, period)
        
        search_stats = await clickhouse_service.get_user_search_stats(user_id, period)
        
        top_tracks = await clickhouse_service.get_user_top_tracks(user_id, period, 5)
        
        stats = {
            "user_id": user_id,
            "period": period,
            "listening": listening_stats,
            "search": search_stats,
            "top_tracks": top_tracks,
            "total_activity": listening_stats.get("total_plays", 0) + search_stats.get("total_searches", 0)
        }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user stats: {str(e)}")

@router.get("/user/{user_id}/listening-history", summary="История прослушиваний пользователя")
async def get_user_listening_history_analytics(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    from_date: Optional[datetime] = Query(None, description="Начальная дата"),
    to_date: Optional[datetime] = Query(None, description="Конечная дата")
):
    try:
        conditions = ["user_id = {}".format(user_id), "action = 'play'"]
        
        if from_date:
            conditions.append(f"timestamp >= '{from_date.isoformat()}'")
        if to_date:
            conditions.append(f"timestamp <= '{to_date.isoformat()}'")
            
        where_clause = " AND ".join(conditions)
        
        query = f"""
        SELECT 
            track_id,
            artist_id,
            timestamp,
            duration_played_ms,
            platform,
            device_type
        FROM track_analytics 
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        
        result = await clickhouse_service.execute_query(query)
        
        history = []
        for row in result:
            history.append({
                "track_id": row[0],
                "artist_id": row[1],
                "track_title": f"Track {row[0]}",  
                "artist_name": f"Artist {row[1]}",
                "played_at": row[2].isoformat(),
                "play_duration_ms": row[3],
                "platform": row[4],
                "device_type": row[5]
            })
        
        return {
            "user_id": user_id,
            "listening_history": history,
            "total_count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get listening history: {str(e)}")

@router.get("/genres/stats", summary="Статистика по жанрам")
async def get_genre_stats(
    period: str = Query(default="month", regex="^(day|week|month|year)$")
):
    try:
        period_days = {"day": 1, "week": 7, "month": 30, "year": 365}
        days = period_days.get(period, 30)
        
        query = """
        SELECT 
            'Electronic' as genre,
            count() as play_count,
            uniq(user_id) as unique_listeners
        FROM track_analytics 
        WHERE action = 'play' 
            AND timestamp >= subtractDays(now(), {days})
            AND track_id % 4 = 0
        UNION ALL
        SELECT 
            'Rock' as genre,
            count() as play_count,
            uniq(user_id) as unique_listeners
        FROM track_analytics 
        WHERE action = 'play' 
            AND timestamp >= subtractDays(now(), {days})
            AND track_id % 4 = 1
        UNION ALL
        SELECT 
            'Pop' as genre,
            count() as play_count,
            uniq(user_id) as unique_listeners
        FROM track_analytics 
        WHERE action = 'play' 
            AND timestamp >= subtractDays(now(), {days})
            AND track_id % 4 = 2
        UNION ALL
        SELECT 
            'Hip-Hop' as genre,
            count() as play_count,
            uniq(user_id) as unique_listeners
        FROM track_analytics 
        WHERE action = 'play' 
            AND timestamp >= subtractDays(now(), {days})
            AND track_id % 4 = 3
        ORDER BY play_count DESC
        """.format(days=days)
        
        result = await clickhouse_service.execute_query(query)
        
        genre_stats = []
        for row in result:
            genre_stats.append({
                "genre": row[0],
                "play_count": row[1],
                "unique_listeners": row[2]
            })
        
        return {"period": period, "genre_stats": genre_stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get genre stats: {str(e)}")

@router.get("/trends", summary="Музыкальные тренды")
async def get_music_trends(
    period: str = Query(default="week", regex="^(day|week|month|year)$")
):
    try:
        period_days = {"day": 1, "week": 7, "month": 30, "year": 365}
        days = period_days.get(period, 7)
        
        trending_query = """
        SELECT 
            track_id,
            artist_id,
            count() as current_plays,
            count() / {days} as avg_daily_plays
        FROM track_analytics 
        WHERE action = 'play' 
            AND timestamp >= subtractDays(now(), {days})
        GROUP BY track_id, artist_id
        HAVING current_plays > 5
        ORDER BY avg_daily_plays DESC
        LIMIT 10
        """.format(days=days)
        
        trending_result = await clickhouse_service.execute_query(trending_query)
        
        growth_query = """
        WITH recent AS (
            SELECT track_id, count() as recent_plays
            FROM track_analytics 
            WHERE action = 'play' 
                AND timestamp >= subtractDays(now(), {half_days})
            GROUP BY track_id
        ),
        older AS (
            SELECT track_id, count() as older_plays
            FROM track_analytics 
            WHERE action = 'play' 
                AND timestamp >= subtractDays(now(), {days})
                AND timestamp < subtractDays(now(), {half_days})
            GROUP BY track_id
        )
        SELECT 
            r.track_id,
            r.recent_plays,
            o.older_plays,
            (r.recent_plays - o.older_plays) as growth
        FROM recent r
        LEFT JOIN older o ON r.track_id = o.track_id
        WHERE r.recent_plays > 2
        ORDER BY growth DESC
        LIMIT 5
        """.format(days=days, half_days=days//2)
        
        growth_result = await clickhouse_service.execute_query(growth_query)
        
        trends = {
            "trending_tracks": [
                {
                    "track_id": row[0],
                    "artist_id": row[1],
                    "title": f"Track {row[0]}",
                    "artist_name": f"Artist {row[1]}",
                    "current_plays": row[2],
                    "avg_daily_plays": round(row[3], 1)
                }
                for row in trending_result
            ],
            "fastest_growing": [
                {
                    "track_id": row[0],
                    "title": f"Track {row[0]}",
                    "recent_plays": row[1],
                    "older_plays": row[2] or 0,
                    "growth": row[3]
                }
                for row in growth_result
            ]
        }
        
        return {"period": period, "trends": trends}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {str(e)}")

@router.get("/dashboard", summary="Дашборд аналитики")
async def get_analytics_dashboard():
    try:
        total_query = """
        SELECT 
            count() as total_plays,
            uniq(user_id) as active_users,
            uniq(track_id) as unique_tracks,
            uniq(artist_id) as unique_artists
        FROM track_analytics 
        WHERE action = 'play' 
            AND timestamp >= subtractDays(now(), 30)
        """
        
        total_result = await clickhouse_service.execute_query(total_query)
        total_stats = total_result[0] if total_result else (0, 0, 0, 0)
        
        daily_query = """
        SELECT 
            toDate(timestamp) as date,
            count() as plays,
            uniq(user_id) as users
        FROM track_analytics 
        WHERE action = 'play' 
            AND timestamp >= subtractDays(now(), 7)
        GROUP BY date
        ORDER BY date
        """
        
        daily_result = await clickhouse_service.execute_query(daily_query)
        
        platform_query = """
        SELECT 
            platform,
            count() as plays,
            uniq(user_id) as users
        FROM track_analytics 
        WHERE action = 'play' 
            AND timestamp >= subtractDays(now(), 7)
        GROUP BY platform
        ORDER BY plays DESC
        """
        
        platform_result = await clickhouse_service.execute_query(platform_query)
        
        dashboard_data = {
            "overview": {
                "total_plays": total_stats[0],
                "active_users": total_stats[1],
                "unique_tracks": total_stats[2],
                "unique_artists": total_stats[3]
            },
            "daily_activity": [
                {
                    "date": row[0].strftime('%Y-%m-%d'),
                    "plays": row[1],
                    "users": row[2]
                }
                for row in daily_result
            ],
            "platform_stats": [
                {
                    "platform": row[0],
                    "plays": row[1],
                    "users": row[2]
                }
                for row in platform_result
            ]
        }
        
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")

@router.get("/recommendations/similar-users/{user_id}", summary="Похожие пользователи")
async def get_similar_users(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    limit: int = Query(default=10, ge=1, le=50)
):
    try:
        user_tracks_query = """
        SELECT track_id, count() as play_count
        FROM track_analytics 
        WHERE user_id = {user_id} 
            AND action = 'play' 
            AND timestamp >= subtractDays(now(), 30)
        GROUP BY track_id
        ORDER BY play_count DESC
        LIMIT 20
        """.format(user_id=user_id)
        
        user_tracks_result = await clickhouse_service.execute_query(user_tracks_query)
        
        if not user_tracks_result:
            return {"user_id": user_id, "similar_users": []}
        
        top_track_ids = [str(row[0]) for row in user_tracks_result]
        track_ids_str = ",".join(top_track_ids)
        
        similar_query = f"""
        SELECT 
            user_id as similar_user_id,
            count() as common_tracks,
            uniq(track_id) as total_user_tracks
        FROM track_analytics 
        WHERE track_id IN ({track_ids_str})
            AND user_id != {user_id}
            AND action = 'play'
            AND timestamp >= subtractDays(now(), 30)
        GROUP BY user_id
        HAVING common_tracks >= 3
        ORDER BY common_tracks DESC, total_user_tracks DESC
        LIMIT {limit}
        """
        
        similar_result = await clickhouse_service.execute_query(similar_query)
        
        similar_users = []
        for row in similar_result:
            similarity_score = (row[1] / len(top_track_ids)) * 100
            similar_users.append({
                "user_id": row[0],
                "common_tracks": row[1],
                "total_tracks": row[2],
                "similarity_score": round(similarity_score, 1)
            })
        
        return {"user_id": user_id, "similar_users": similar_users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get similar users: {str(e)}")

@router.get("/realtime/platform-stats", summary="Статистика платформы в реальном времени")
async def get_realtime_platform_stats():
    try:
        stats = await clickhouse_service.get_api_stats(days=1)
        
        platform_query = """
        SELECT 
            count() as total_actions,
            uniq(user_id) as active_users,
            countIf(action = 'play') as plays,
            countIf(action = 'like') as likes,
            countIf(action = 'skip') as skips
        FROM track_analytics 
        WHERE timestamp >= subtractHours(now(), 1)
        """
        
        result = await clickhouse_service.execute_query(platform_query)
        platform_stats = result[0] if result else (0, 0, 0, 0, 0)
        
        enhanced_stats = {
            **stats,
            "realtime_stats": {
                "total_actions_last_hour": platform_stats[0],
                "active_users_last_hour": platform_stats[1],
                "plays_last_hour": platform_stats[2],
                "likes_last_hour": platform_stats[3],
                "skips_last_hour": platform_stats[4]
            }
        }
        
        return {"platform_stats": enhanced_stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get platform stats: {str(e)}")

@router.get("/realtime/active-users", summary="Активные пользователи в реальном времени")
async def get_realtime_active_users(
    minutes: int = Query(default=60, ge=1, le=1440, description="Период в минутах")
):
    try:
        query = """
        SELECT 
            uniq(user_id) as active_users,
            count() as total_actions
        FROM track_analytics 
        WHERE timestamp >= subtractMinutes(now(), {minutes})
        """.format(minutes=minutes)
        
        result = await clickhouse_service.execute_query(query)
        
        if result:
            active_users = result[0][0]
            total_actions = result[0][1]
        else:
            active_users = 0
            total_actions = 0
        
        return {
            "minutes": minutes,
            "active_users": active_users,
            "total_actions": total_actions,
            "avg_actions_per_user": round(total_actions / max(active_users, 1), 1)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active users: {str(e)}")

@router.get("/advanced/track-analytics/{track_id}", summary="Расширенная аналитика трека")
async def get_advanced_track_analytics(
    track_id: int = Path(..., title="ID трека", ge=1),
    period: str = Query(default="week", regex="^(day|week|month|year)$")
):
    try:
        period_days = {"day": 1, "week": 7, "month": 30, "year": 365}
        days = period_days.get(period, 7)
        
        stats = await clickhouse_service.get_track_stats(track_id, days)
        
        hourly_query = """
        SELECT 
            toHour(timestamp) as hour,
            count() as plays
        FROM track_analytics 
        WHERE track_id = {track_id} 
            AND action = 'play'
            AND timestamp >= subtractDays(now(), {days})
        GROUP BY hour
        ORDER BY hour
        """.format(track_id=track_id, days=days)
        
        hourly_result = await clickhouse_service.execute_query(hourly_query)
        
        hourly_stats = {hour: 0 for hour in range(24)}
        for row in hourly_result:
            hourly_stats[row[0]] = row[1]
        
        enhanced_stats = {
            **stats,
            "hourly_distribution": hourly_stats,
            "track_id": track_id,
            "period": period
        }
        
        return {"track_id": track_id, "period": period, "analytics": enhanced_stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get track analytics: {str(e)}")

@router.get("/advanced/user-analytics/{user_id}", summary="Расширенная аналитика пользователя")
async def get_advanced_user_analytics(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    period: str = Query(default="week", regex="^(day|week|month|year)$")
):
    try:
        activity_stats = await clickhouse_service.get_user_activity_stats(user_id, 
                                                                        clickhouse_service._get_days_for_period(period))
        
        top_tracks = await clickhouse_service.get_user_top_tracks(user_id, period, 10)
        
        timeline = await clickhouse_service.get_user_activity_timeline(user_id, 
                                                                     clickhouse_service._get_days_for_period(period))
        
        analytics = {
            "activity_stats": activity_stats,
            "top_tracks": top_tracks,
            "activity_timeline": timeline
        }
        
        return {"user_id": user_id, "period": period, "analytics": analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user analytics: {str(e)}")

@router.post("/events/search", status_code=201, summary="Записать событие поиска")
async def record_search_event(
    user_id: int = Body(...),
    query: str = Body(...),
    results_count: int = Body(default=0),
    search_type: str = Body(default="general"),
    clicked_result_id: Optional[int] = Body(default=None),
    clicked_result_type: Optional[str] = Body(default=None)
):
    try:
        await clickhouse_service.log_search_action(
            query=query,
            results_count=results_count,
            search_type=search_type,
            user_id=user_id,
            clicked_result_id=clicked_result_id,
            clicked_result_type=clicked_result_type
        )
        return {"message": "Search event recorded in ClickHouse"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record search event: {str(e)}")

@router.post("/events/playlist", status_code=201, summary="Записать событие с плейлистом")
async def record_playlist_event(
    user_id: int = Body(...),
    playlist_id: int = Body(...),
    action: str = Body(..., regex="^(create|update|delete|add_track|remove_track)$"),
    track_id: Optional[int] = Body(default=None)
):
    try:
        await clickhouse_service.log_user_action(
            user_id=user_id,
            action=f"playlist_{action}",
            tracks_played=1 if action == "add_track" else 0
        )
        
        if action == "add_track" and track_id:
            await clickhouse_service.log_track_action(
                track_id=track_id,
                artist_id=1, 
                action="add_to_playlist",
                user_id=user_id
            )
        
        return {"message": "Playlist event recorded in ClickHouse"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record playlist event: {str(e)}")

@router.get("/performance/summary", summary="Сводка производительности аналитики")
async def get_performance_summary():
    try:
        import time
        
        results = {}
        
        start_time = time.time()
        
        popular_tracks_query = """
        SELECT 
            track_id,
            count() as play_count
        FROM track_analytics 
        WHERE action = 'play' 
            AND timestamp >= subtractDays(now(), 7)
        GROUP BY track_id
        ORDER BY play_count DESC
        LIMIT 10
        """
        
        popular_result = await clickhouse_service.execute_query(popular_tracks_query)
        popular_time = time.time() - start_time
        
        start_time = time.time()
        active_users_query = """
        SELECT uniq(user_id) as active_users
        FROM track_analytics 
        WHERE timestamp >= subtractDays(now(), 1)
        """
        
        active_result = await clickhouse_service.execute_query(active_users_query)
        active_time = time.time() - start_time
        
        start_time = time.time()
        complex_query = """
        SELECT 
            track_id,
            count() as plays,
            uniq(user_id) as listeners,
            avg(duration_played_ms) as avg_duration
        FROM track_analytics 
        WHERE action = 'play' 
            AND timestamp >= subtractDays(now(), 30)
        GROUP BY track_id
        HAVING plays > 5
        ORDER BY plays DESC, listeners DESC
        LIMIT 50
        """
        
        complex_result = await clickhouse_service.execute_query(complex_query)
        complex_time = time.time() - start_time
        
        results = {
            "clickhouse_performance": {
                "popular_tracks_query": {
                    "time_seconds": round(popular_time, 4),
                    "results_count": len(popular_result),
                    "performance_rating": "Excellent" if popular_time < 0.1 else "Good" if popular_time < 0.5 else "Fair"
                },
                "active_users_query": {
                    "time_seconds": round(active_time, 4),
                    "active_users": active_result[0][0] if active_result else 0,
                    "performance_rating": "Excellent" if active_time < 0.05 else "Good" if active_time < 0.2 else "Fair"
                },
                "complex_analytics_query": {
                    "time_seconds": round(complex_time, 4),
                    "results_count": len(complex_result),
                    "performance_rating": "Excellent" if complex_time < 0.5 else "Good" if complex_time < 2.0 else "Fair"
                }
            },
            "database_info": {
                "engine": "ClickHouse",
                "optimized_for": "OLAP/Analytics",
                "data_compression": "High",
                "real_time_queries": "Yes"
            }
        }
        
        return {"performance_comparison": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance summary: {str(e)}")

@router.get("/clickhouse/api-stats", summary="Статистика API запросов (ClickHouse)")
async def get_clickhouse_api_stats(
    days: int = Query(7, ge=1, le=90, description="Количество дней для анализа")
):
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
    artist_id: int = Body(1),  
    user_id: Optional[int] = Body(None)
):
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
    try:
        user_id = current_user.id
        
        search_history = await clickhouse_service.get_user_search_history(user_id, days)
        
        top_tracks = await clickhouse_service.get_user_top_tracks(user_id, days)
        
        activity_stats = await clickhouse_service.get_user_activity_stats(user_id, days)
        
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
    try:
        if current_user.id != user_id and current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Доступ запрещен")
        
        days_map = {'7d': 7, '30d': 30, '90d': 90}
        days = days_map.get(period, 30)
        
        search_history = await clickhouse_service.get_user_search_history(user_id, days)
        search_count = len(search_history)
        unique_queries = len(set(item['search_query'] for item in search_history))
        clicked_searches = sum(1 for item in search_history if item.get('clicked_result_id'))
        click_through_rate = clicked_searches / search_count if search_count > 0 else 0
        avg_results = sum(item['results_count'] for item in search_history) / search_count if search_count > 0 else 0
        
        top_tracks_data = await clickhouse_service.get_user_top_tracks(user_id, days)
        
        listening_data = await clickhouse_service.get_user_listening_stats(user_id, days)
        total_plays = listening_data.get('total_plays', 0)
        total_duration = listening_data.get('total_duration_sec', 0)
        unique_tracks = listening_data.get('unique_tracks', 0)
        avg_session_length = listening_data.get('avg_session_length_sec', 0)
        
        activity_timeline = await clickhouse_service.get_user_activity_timeline(user_id, min(days, 30))
        
        active_days = len([day for day in activity_timeline if day.get('search_count', 0) + day.get('listening_count', 0) > 0])
        total_sessions = sum(day.get('session_count', 1) for day in activity_timeline)
        total_activity = search_count + total_plays
        avg_daily_activity = total_activity / days if days > 0 else 0
        
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
        
        formatted_search_history = []
        for search in search_history[-10:]:  
            formatted_search_history.append({
                'query': search.get('search_query', ''),
                'timestamp': search.get('timestamp', ''),
                'results_count': search.get('results_count', 0),
                'clicked': bool(search.get('clicked_result_id'))
            })
        
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
