"""
Эндпоинты для аналитики артистов
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from typing import Dict, Any, Optional

from app.services.clickhouse_service import clickhouse_service

router = APIRouter()


@router.get("/api-stats", summary="Статистика API")
async def get_api_stats(
    days: int = Query(default=7, ge=1, le=365, description="Количество дней для анализа")
) -> Dict[str, Any]:
    """
    Получить статистику использования API за указанный период
    """
    try:
        stats = await clickhouse_service.get_api_stats(days=days)
        return {
            "period_days": days,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики API: {str(e)}")


@router.get("/track/{track_id}/stats", summary="Статистика трека")
async def get_track_stats(
    track_id: int = Path(..., ge=1, description="ID трека"),
    days: int = Query(default=30, ge=1, le=365, description="Количество дней для анализа")
) -> Dict[str, Any]:
    """
    Получить статистику трека за указанный период
    """
    try:
        stats = await clickhouse_service.get_track_stats(track_id=track_id, days=days)
        return {
            "track_id": track_id,
            "period_days": days,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики трека: {str(e)}")


@router.get("/artist/{artist_id}/stats", summary="Статистика артиста")
async def get_artist_stats(
    artist_id: int = Path(..., ge=1, description="ID артиста")
) -> Dict[str, Any]:
    """
    Получить статистику артиста (за последние 30 дней)
    """
    try:
        stats = await clickhouse_service.get_artist_stats(artist_id=artist_id)
        return {
            "artist_id": artist_id,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики артиста: {str(e)}")


@router.post("/track-action", summary="Записать действие с треком")
async def log_track_action_endpoint(
    track_id: int,
    artist_id: int,
    action: str,
    user_id: Optional[int] = None,
    duration_played_ms: Optional[int] = None,
    track_position_ms: Optional[int] = None,
    platform: str = "web",
    device_type: str = "unknown",
    location: Optional[str] = None,
    session_id: Optional[str] = None
):
    """
    Записать действие пользователя с треком (play, pause, skip, like, etc.)
    """
    try:
        await clickhouse_service.log_track_action(
            track_id=track_id,
            artist_id=artist_id,
            action=action,
            user_id=user_id,
            duration_played_ms=duration_played_ms,
            track_position_ms=track_position_ms,
            platform=platform,
            device_type=device_type,
            location=location,
            session_id=session_id
        )
        return {"message": "Действие записано успешно"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка записи действия: {str(e)}")


@router.post("/search-action", summary="Записать поисковый запрос")
async def log_search_action_endpoint(
    query: str,
    results_count: int,
    search_type: str,
    user_id: Optional[int] = None,
    clicked_result_id: Optional[int] = None,
    clicked_result_type: Optional[str] = None,
    session_id: Optional[str] = None
):
    """
    Записать поисковый запрос пользователя
    """
    try:
        await clickhouse_service.log_search_action(
            query=query,
            results_count=results_count,
            search_type=search_type,
            user_id=user_id,
            clicked_result_id=clicked_result_id,
            clicked_result_type=clicked_result_type,
            session_id=session_id
        )
        return {"message": "Поисковый запрос записан успешно"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка записи поискового запроса: {str(e)}")


@router.post("/artist-action", summary="Записать действие артиста")
async def log_artist_action_endpoint(
    artist_id: int,
    action: str,
    target_id: Optional[int] = None,
    metadata: Optional[Dict[str, str]] = None
):
    """
    Записать действие артиста (upload, delete, update, etc.)
    """
    try:
        await clickhouse_service.log_artist_action(
            artist_id=artist_id,
            action=action,
            target_id=target_id,
            metadata=metadata
        )
        return {"message": "Действие артиста записано успешно"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка записи действия артиста: {str(e)}")


@router.get("/health", summary="Проверка состояния аналитики")
async def analytics_health_check():
    """
    Проверить состояние подключения к ClickHouse
    """
    try:
        is_connected = await clickhouse_service.test_connection()
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "clickhouse_connected": is_connected
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "clickhouse_connected": False,
            "error": str(e)
        }
