"""
API эндпоинты для работы с S3 хранилищем
Включает загрузку треков, обложек и управление файлами
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from app.services.s3_service import s3_service
from app.core.deps import get_current_user
from app.schemas.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/tracks/upload")
async def upload_track(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Загрузка трека в S3
    """
    # Проверяем тип файла
    allowed_types = ['audio/mpeg', 'audio/wav', 'audio/flac', 'audio/mp4', 'audio/m4a']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип файла. Разрешены: {', '.join(allowed_types)}"
        )
    
    # Проверяем размер файла (максимум 100MB)
    max_size = 100 * 1024 * 1024  # 100MB
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=400,
            detail="Файл слишком большой. Максимальный размер: 100MB"
        )
    
    try:
        # Загружаем файл в S3
        from io import BytesIO
        file_content = BytesIO(contents)
        
        result = s3_service.upload_track(
            file_content=file_content,
            filename=file.filename,
            user_id=current_user.id,
            metadata={
                'content_type': file.content_type,
                'size': len(contents)
            }
        )
        
        if result['success']:
            logger.info(f"Track uploaded by user {current_user.id}: {file.filename}")
            return {
                "success": True,
                "message": "Трек успешно загружен",
                "data": {
                    "s3_key": result['s3_key'],
                    "file_size": result['file_size'],
                    "url": result['url']
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result['error'])
            
    except Exception as e:
        logger.error(f"Error uploading track: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки файла")

@router.post("/covers/upload")
async def upload_cover(
    file: UploadFile = File(...),
    track_id: Optional[int] = Query(None),
    album_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Загрузка обложки в S3
    """
    # Проверяем тип файла
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый тип файла. Разрешены: {', '.join(allowed_types)}"
        )
    
    # Проверяем размер файла (максимум 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=400,
            detail="Файл слишком большой. Максимальный размер: 10MB"
        )
    
    if not track_id and not album_id:
        raise HTTPException(
            status_code=400,
            detail="Необходимо указать track_id или album_id"
        )
    
    try:
        from io import BytesIO
        file_content = BytesIO(contents)
        
        result = s3_service.upload_cover(
            file_content=file_content,
            filename=file.filename,
            track_id=track_id,
            album_id=album_id
        )
        
        if result['success']:
            logger.info(f"Cover uploaded by user {current_user.id}: {file.filename}")
            return {
                "success": True,
                "message": "Обложка успешно загружена",
                "data": {
                    "s3_key": result['s3_key'],
                    "url": result['url']
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result['error'])
            
    except Exception as e:
        logger.error(f"Error uploading cover: {e}")
        raise HTTPException(status_code=500, detail="Ошибка загрузки обложки")

@router.get("/tracks/user/{user_id}")
async def get_user_tracks(
    user_id: int,
    current_user: User = Depends(get_current_user),
    limit: int = Query(100, le=1000)
) -> Dict[str, Any]:
    """
    Получение списка треков пользователя
    """
    # Проверяем права доступа
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    try:
        tracks = s3_service.list_user_tracks(user_id, limit)
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "tracks": tracks,
                "total": len(tracks)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user tracks: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения списка треков")

@router.get("/tracks/{s3_key}/url")
async def get_track_url(
    s3_key: str,
    current_user: User = Depends(get_current_user),
    expires_in: int = Query(3600, le=86400)  # Максимум 24 часа
) -> Dict[str, Any]:
    """
    Получение presigned URL для трека
    """
    try:
        # Получаем метаданные трека для проверки прав
        metadata = s3_service.get_track_metadata(s3_key)
        if not metadata:
            raise HTTPException(status_code=404, detail="Трек не найден")
        
        # Проверяем права доступа (базовая проверка)
        track_user_id = metadata.get('metadata', {}).get('user-id')
        if track_user_id and str(current_user.id) != track_user_id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        
        url = s3_service.get_track_url(s3_key, expires_in)
        
        if url:
            return {
                "success": True,
                "data": {
                    "url": url,
                    "expires_in": expires_in
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Ошибка генерации URL")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting track URL: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения URL трека")

@router.get("/tracks/{s3_key}/stream")
async def stream_track(
    s3_key: str,
    current_user: User = Depends(get_current_user)
):
    """
    Перенаправление на поток трека
    """
    try:
        # Получаем метаданные трека для проверки прав
        metadata = s3_service.get_track_metadata(s3_key)
        if not metadata:
            raise HTTPException(status_code=404, detail="Трек не найден")
        
        # Проверяем права доступа
        track_user_id = metadata.get('metadata', {}).get('user-id')
        if track_user_id and str(current_user.id) != track_user_id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        
        # Генерируем URL и перенаправляем
        url = s3_service.get_track_url(s3_key, expires_in=3600)
        
        if url:
            return RedirectResponse(url=url)
        else:
            raise HTTPException(status_code=500, detail="Ошибка генерации URL")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming track: {e}")
        raise HTTPException(status_code=500, detail="Ошибка стриминга трека")

@router.delete("/tracks/{s3_key}")
async def delete_track(
    s3_key: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Удаление трека из S3
    """
    try:
        # Получаем метаданные трека для проверки прав
        metadata = s3_service.get_track_metadata(s3_key)
        if not metadata:
            raise HTTPException(status_code=404, detail="Трек не найден")
        
        # Проверяем права доступа
        track_user_id = metadata.get('metadata', {}).get('user-id')
        if track_user_id and str(current_user.id) != track_user_id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        
        success = s3_service.delete_track(s3_key)
        
        if success:
            logger.info(f"Track deleted by user {current_user.id}: {s3_key}")
            return {
                "success": True,
                "message": "Трек успешно удален"
            }
        else:
            raise HTTPException(status_code=500, detail="Ошибка удаления трека")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting track: {e}")
        raise HTTPException(status_code=500, detail="Ошибка удаления трека")

@router.get("/storage/stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Получение статистики использования хранилища
    """
    try:
        stats = s3_service.get_storage_stats()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики")

@router.post("/maintenance/cleanup-temp")
async def cleanup_temp_files(
    current_user: User = Depends(get_current_user),
    older_than_hours: int = Query(24, ge=1, le=168)  # От 1 часа до недели
) -> Dict[str, Any]:
    """
    Очистка временных файлов (только для администраторов)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    try:
        deleted_count = s3_service.cleanup_temp_files(older_than_hours)
        
        logger.info(f"Temp files cleanup by admin {current_user.id}: {deleted_count} files")
        
        return {
            "success": True,
            "message": f"Удалено {deleted_count} временных файлов",
            "data": {
                "deleted_files": deleted_count,
                "older_than_hours": older_than_hours
            }
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {e}")
        raise HTTPException(status_code=500, detail="Ошибка очистки временных файлов")

@router.get("/health")
async def s3_health_check() -> Dict[str, Any]:
    """
    Проверка состояния S3 сервиса
    """
    try:
        # Простая проверка - получаем статистику
        stats = s3_service.get_storage_stats()
        
        return {
            "success": True,
            "status": "healthy",
            "data": {
                "endpoint": s3_service.endpoint_url,
                "buckets_count": len(stats.get('buckets', {})),
                "total_objects": stats.get('total_objects', 0),
                "total_size_mb": stats.get('total_size_mb', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"S3 health check failed: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }
