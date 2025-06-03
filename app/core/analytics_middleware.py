"""
Middleware для логирования API запросов в ClickHouse
"""

import time
import asyncio
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.clickhouse_service import clickhouse_service


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware для сбора аналитики API запросов"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Засекаем время начала запроса
        start_time = time.time()
        
        # Получаем информацию о запросе
        method = request.method
        endpoint = str(request.url.path)
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host if request.client else ""
        
        # Получаем информацию о пользователе из токена (если есть)
        user_id = None
        artist_id = None
        session_id = None
        
        try:
            # Попытаемся извлечь user_id из токена если middleware для auth уже сработал
            if hasattr(request.state, 'user_id'):
                user_id = request.state.user_id
            if hasattr(request.state, 'artist_id'):
                artist_id = request.state.artist_id
            if hasattr(request.state, 'session_id'):
                session_id = request.state.session_id
        except:
            pass
        
        # Получаем размер запроса
        request_size = None
        if request.headers.get("content-length"):
            try:
                request_size = int(request.headers.get("content-length"))
            except:
                pass
        
        # Выполняем запрос
        response = await call_next(request)
        
        # Вычисляем время выполнения
        process_time = time.time() - start_time
        response_time_ms = int(process_time * 1000)
        
        # Получаем размер ответа
        response_size = None
        if hasattr(response, 'headers') and response.headers.get("content-length"):
            try:
                response_size = int(response.headers.get("content-length"))
            except:
                pass
        
        # Определяем, была ли ошибка
        error_message = None
        if response.status_code >= 400:
            error_message = f"HTTP {response.status_code}"
        
        # Логируем в ClickHouse асинхронно (не блокируем ответ)
        asyncio.create_task(
            clickhouse_service.log_api_request(
                method=method,
                endpoint=endpoint,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                user_id=user_id,
                artist_id=artist_id,
                user_agent=user_agent,
                ip_address=ip_address,
                request_size=request_size,
                response_size=response_size,
                error_message=error_message,
                session_id=session_id
            )
        )
        
        # Добавляем заголовок с временем обработки
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


def log_track_action_async(track_id: int, artist_id: int, action: str, user_id: int = None, **kwargs):
    """Асинхронное логирование действий с треками"""
    asyncio.create_task(
        clickhouse_service.log_track_action(
            track_id=track_id,
            artist_id=artist_id,
            action=action,
            user_id=user_id,
            **kwargs
        )
    )


def log_search_action_async(query: str, results_count: int, search_type: str, user_id: int = None, **kwargs):
    """Асинхронное логирование поисковых запросов"""
    asyncio.create_task(
        clickhouse_service.log_search_action(
            query=query,
            results_count=results_count,
            search_type=search_type,
            user_id=user_id,
            **kwargs
        )
    )


def log_user_action_async(user_id: int, action: str, **kwargs):
    """Асинхронное логирование действий пользователей"""
    asyncio.create_task(
        clickhouse_service.log_user_action(
            user_id=user_id,
            action=action,
            **kwargs
        )
    )


def log_artist_action_async(artist_id: int, action: str, **kwargs):
    """Асинхронное логирование действий артистов"""
    asyncio.create_task(
        clickhouse_service.log_artist_action(
            artist_id=artist_id,
            action=action,
            **kwargs
        )
    )
