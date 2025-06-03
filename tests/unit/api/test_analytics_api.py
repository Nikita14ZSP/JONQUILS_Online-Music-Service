"""
Unit тесты для аналитических API эндпоинтов
Тестируют логику без внешних зависимостей
"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient
from datetime import datetime, timedelta

from tests.utils.test_helpers import TestDataBuilder, ApiTestHelper, MockServiceBuilder


class TestAnalyticsAPI:
    """Тесты аналитических эндпоинтов"""
    
    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_popular_tracks_success(self, auth_client: AsyncClient):
        """Тест получения популярных треков"""
        # Подготовка
        mock_clickhouse = MockServiceBuilder.clickhouse_service()
        
        with patch('app.api.v1.endpoints.analytics.clickhouse_service', mock_clickhouse):
            api_helper = ApiTestHelper(auth_client)
            
            # Выполнение
            response = await auth_client.get("/api/v1/analytics/popular-tracks?limit=10")
            
            # Проверка
            await api_helper.assert_status(response, 200)
            data = response.json()
            
            assert "success" in data
            assert data["success"] is True
            assert "data" in data
            assert len(data["data"]) == 2  # Из мока
            
            # Проверяем структуру данных
            track = data["data"][0]
            assert "track_id" in track
            assert "play_count" in track
            assert "unique_listeners" in track
    
    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_popular_tracks_with_filters(self, auth_client: AsyncClient):
        """Тест получения популярных треков с фильтрами"""
        mock_clickhouse = MockServiceBuilder.clickhouse_service()
        
        with patch('app.api.v1.endpoints.analytics.clickhouse_service', mock_clickhouse):
            response = await auth_client.get(
                "/api/v1/analytics/popular-tracks"
                "?limit=5&time_range=week&genre=rock"
            )
            
            assert response.status_code == 200
            # Проверяем что мок был вызван с правильными параметрами
            mock_clickhouse.get_popular_tracks.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_user_stats_success(self, auth_client: AsyncClient, test_user):
        """Тест получения статистики пользователя"""
        mock_clickhouse = MockServiceBuilder.clickhouse_service(
            user_stats={
                "total_listening_time": 7200,
                "tracks_played": 50,
                "favorite_genre": "Electronic",
                "listening_streak": 7
            }
        )
        
        with patch('app.api.v1.endpoints.analytics.clickhouse_service', mock_clickhouse):
            api_helper = ApiTestHelper(auth_client)
            
            response = await auth_client.get(f"/api/v1/analytics/user/{test_user.id}/stats")
            
            await api_helper.assert_status(response, 200)
            await api_helper.assert_json_contains(response, {
                "success": True,
                "data": {
                    "total_listening_time": 7200,
                    "tracks_played": 50,
                    "favorite_genre": "Electronic"
                }
            })
    
    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_user_stats_forbidden(self, auth_client: AsyncClient):
        """Тест запрета доступа к чужой статистике"""
        # Пытаемся получить статистику другого пользователя
        response = await auth_client.get("/api/v1/analytics/user/999/stats")
        
        assert response.status_code == 403
        data = response.json()
        assert "Недостаточно прав" in data["detail"]
    
    @pytest.mark.unit
    @pytest.mark.api
    async def test_record_listening_event_success(self, auth_client: AsyncClient):
        """Тест записи события прослушивания"""
        mock_clickhouse = MockServiceBuilder.clickhouse_service()
        
        with patch('app.api.v1.endpoints.analytics.clickhouse_service', mock_clickhouse):
            api_helper = ApiTestHelper(auth_client)
            
            event_data = {
                "track_id": "track_123",
                "event_type": "play",
                "duration": 180,
                "quality": "high",
                "platform": "web"
            }
            
            response = await api_helper.post_json("/api/v1/analytics/listening-events", event_data)
            
            await api_helper.assert_status(response, 200)
            await api_helper.assert_json_contains(response, {
                "success": True,
                "message": "Событие записано"
            })
            
            # Проверяем что мок был вызван
            mock_clickhouse.record_listening_event.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.api
    async def test_record_listening_event_invalid_data(self, auth_client: AsyncClient):
        """Тест записи события с невалидными данными"""
        api_helper = ApiTestHelper(auth_client)
        
        # Отправляем невалидные данные (отсутствует track_id)
        invalid_data = {
            "event_type": "play",
            "duration": 180
        }
        
        response = await api_helper.post_json("/api/v1/analytics/listening-events", invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_listening_history_success(self, auth_client: AsyncClient, test_user):
        """Тест получения истории прослушивания"""
        test_history = [
            {
                "timestamp": datetime.now().isoformat(),
                "track_id": "track_1",
                "event_type": "play",
                "duration": 180
            },
            {
                "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                "track_id": "track_2", 
                "event_type": "skip",
                "duration": 30
            }
        ]
        
        mock_clickhouse = MockServiceBuilder.clickhouse_service()
        mock_clickhouse.get_listening_history.return_value = test_history
        
        with patch('app.api.v1.endpoints.analytics.clickhouse_service', mock_clickhouse):
            api_helper = ApiTestHelper(auth_client)
            
            response = await auth_client.get(
                f"/api/v1/analytics/user/{test_user.id}/listening-history?limit=10"
            )
            
            await api_helper.assert_status(response, 200)
            data = response.json()
            
            assert data["success"] is True
            assert len(data["data"]) == 2
            assert data["data"][0]["track_id"] == "track_1"
    
    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_dashboard_stats_success(self, auth_client: AsyncClient):
        """Тест получения статистики для дашборда"""
        mock_clickhouse = MockServiceBuilder.clickhouse_service()
        mock_clickhouse.get_dashboard_stats.return_value = {
            "total_plays_today": 1500,
            "active_users": 250,
            "new_tracks": 45,
            "popular_genres": ["Rock", "Pop", "Electronic"]
        }
        
        with patch('app.api.v1.endpoints.analytics.clickhouse_service', mock_clickhouse):
            api_helper = ApiTestHelper(auth_client)
            
            response = await auth_client.get("/api/v1/analytics/dashboard")
            
            await api_helper.assert_status(response, 200)
            await api_helper.assert_json_contains(response, {
                "success": True,
                "data": {
                    "total_plays_today": 1500,
                    "active_users": 250
                }
            })
    
    @pytest.mark.unit
    @pytest.mark.api
    async def test_get_genres_stats_success(self, auth_client: AsyncClient):
        """Тест получения статистики по жанрам"""
        mock_clickhouse = MockServiceBuilder.clickhouse_service()
        
        with patch('app.api.v1.endpoints.analytics.clickhouse_service', mock_clickhouse):
            response = await auth_client.get("/api/v1/analytics/genres/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.performance
    async def test_analytics_endpoint_performance(self, auth_client: AsyncClient):
        """Тест производительности аналитических эндпоинтов"""
        from tests.utils.test_helpers import PerformanceTestHelper
        
        mock_clickhouse = MockServiceBuilder.clickhouse_service()
        
        with patch('app.api.v1.endpoints.analytics.clickhouse_service', mock_clickhouse):
            # Тестируем несколько эндпоинтов на производительность
            endpoints = [
                "/api/v1/analytics/popular-tracks?limit=10",
                "/api/v1/analytics/genres/stats",
                "/api/v1/analytics/dashboard"
            ]
            
            for endpoint in endpoints:
                async def make_request():
                    return await auth_client.get(endpoint)
                
                response, duration = await PerformanceTestHelper.measure_async_time(make_request())
                
                # Проверяем что ответ быстрый (менее 500ms для unit тестов)
                PerformanceTestHelper.assert_performance(
                    duration, 0.5, f"GET {endpoint}"
                )
                assert response.status_code == 200


class TestAnalyticsAPIErrorHandling:
    """Тесты обработки ошибок в аналитических API"""
    
    @pytest.mark.unit
    @pytest.mark.api
    async def test_clickhouse_connection_error(self, auth_client: AsyncClient):
        """Тест обработки ошибки подключения к ClickHouse"""
        mock_clickhouse = MockServiceBuilder.clickhouse_service(connection_working=False)
        mock_clickhouse.get_popular_tracks.side_effect = Exception("Connection failed")
        
        with patch('app.api.v1.endpoints.analytics.clickhouse_service', mock_clickhouse):
            response = await auth_client.get("/api/v1/analytics/popular-tracks")
            
            assert response.status_code == 500
            data = response.json()
            assert "error" in data["detail"].lower()
    
    @pytest.mark.unit
    @pytest.mark.api
    async def test_invalid_user_id_format(self, auth_client: AsyncClient):
        """Тест с невалидным форматом user_id"""
        response = await auth_client.get("/api/v1/analytics/user/invalid_id/stats")
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.unit
    @pytest.mark.api
    async def test_negative_limit_parameter(self, auth_client: AsyncClient):
        """Тест с отрицательным параметром limit"""
        response = await auth_client.get("/api/v1/analytics/popular-tracks?limit=-5")
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.unit
    @pytest.mark.api
    async def test_too_large_limit_parameter(self, auth_client: AsyncClient):
        """Тест с слишком большим параметром limit"""
        mock_clickhouse = MockServiceBuilder.clickhouse_service()
        
        with patch('app.api.v1.endpoints.analytics.clickhouse_service', mock_clickhouse):
            response = await auth_client.get("/api/v1/analytics/popular-tracks?limit=10000")
            
            # Должен ограничиться максимальным значением
            assert response.status_code == 200


class TestAnalyticsAPIAuthentication:
    """Тесты аутентификации для аналитических API"""
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.security
    async def test_unauthenticated_access_denied(self, async_client: AsyncClient):
        """Тест запрета доступа без аутентификации"""
        endpoints = [
            "/api/v1/analytics/popular-tracks",
            "/api/v1/analytics/user/1/stats",
            "/api/v1/analytics/dashboard"
        ]
        
        for endpoint in endpoints:
            response = await async_client.get(endpoint)
            assert response.status_code == 401  # Unauthorized
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.security
    async def test_admin_only_endpoints(self, auth_client: AsyncClient, admin_client: AsyncClient):
        """Тест эндпоинтов доступных только администраторам"""
        admin_endpoints = [
            "/api/v1/analytics/performance/summary",
            "/api/v1/analytics/system/health"
        ]
        
        mock_clickhouse = MockServiceBuilder.clickhouse_service()
        
        with patch('app.api.v1.endpoints.analytics.clickhouse_service', mock_clickhouse):
            for endpoint in admin_endpoints:
                # Обычный пользователь не должен иметь доступ
                response = await auth_client.get(endpoint)
                assert response.status_code in [403, 404]  # Forbidden or Not Found
                
                # Админ должен иметь доступ
                response = await admin_client.get(endpoint)
                assert response.status_code == 200
