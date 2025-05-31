from fastapi import APIRouter, Body, HTTPException, Query
from typing import List

from app.schemas.user_activity import UserActivity, UserActivityCreate
from app.services.analytics_service import analytics_service
from app.services.track_service import track_service # Для проверки существования трека

router = APIRouter()

@router.post("/log_activity/", response_model=UserActivity, status_code=201, 
             summary="Залогировать действие пользователя")
def log_activity(activity_in: UserActivityCreate = Body(...)):
    """
    Записывает событие активности пользователя.
    - **user_id**: Идентификатор пользователя (опционально).
    - **track_id**: ID трека, с которым связано действие.
    - **action**: Тип действия (например, 'play', 'like', 'complete_listen').
    - **timestamp**: Время события (по умолчанию текущее UTC).
    - **listen_duration_ms**: Длительность прослушивания в мс (опционально).
    - **session_id**: Идентификатор сессии (опционально).
    """
    # Проверим, существует ли трек, прежде чем логировать активность
    track = track_service.get_track_by_id(activity_in.track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Track with id {activity_in.track_id} not found.")
    
    logged_event = analytics_service.log_user_activity(activity_in)
    return logged_event

@router.get("/activity_logs/track/{track_id}", response_model=List[UserActivity], 
            summary="Получить логи активности для трека")
def get_track_activity(
    track_id: int, 
    limit: int = Query(default=100, ge=1, le=1000)
):
    """
    Возвращает последние N записей активности для указанного трека.
    """
    # Проверим, существует ли трек
    track = track_service.get_track_by_id(track_id)
    if not track:
        raise HTTPException(status_code=404, detail=f"Track with id {track_id} not found.")
        
    logs = analytics_service.get_activity_logs_for_track(track_id=track_id, limit=limit)
    return logs

@router.get("/activity_logs/all/", response_model=List[UserActivity], 
            summary="Получить все логи активности (демо)")
def get_all_logs(limit: int = Query(default=100, ge=1, le=1000)):
    """
    Возвращает последние N записей активности по всей системе (для демонстрации).
    В реальной системе такой эндпоинт либо не будет существовать, либо будет сильно ограничен.
    """
    logs = analytics_service.get_all_activity_logs(limit=limit)
    return logs 