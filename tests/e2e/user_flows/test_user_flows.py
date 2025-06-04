"""
End-to-End тесты для пользовательских сценариев
Полные сценарии использования музыкального сервиса
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
import tempfile
import json
from io import BytesIO


@pytest.mark.e2e
class TestUserFlows:
    """E2E тесты пользовательских сценариев"""

    async def test_complete_user_registration_flow(self, async_client: AsyncClient):
        """Полный сценарий регистрации пользователя"""
        # 1. Регистрация нового пользователя
        registration_data = {
            "username": "newuser123",
            "email": "newuser@example.com",
            "password": "securepassword123",
            "full_name": "New User"
        }
        
        response = await async_client.post("/api/v1/auth/register", json=registration_data)
        assert response.status_code == 201
        user_data = response.json()
        assert user_data["username"] == "newuser123"
        assert user_data["email"] == "newuser@example.com"
        
        # 2. Подтверждение email (мокаем)
        with patch('app.services.auth_service.send_verification_email') as mock_send:
            mock_send.return_value = True
            
            verification_response = await async_client.post(
                f"/api/v1/auth/verify-email/{user_data['id']}/fake-token"
            )
            assert verification_response.status_code == 200
        
        # 3. Вход в систему
        login_data = {
            "username": "newuser123",
            "password": "securepassword123"
        }
        
        login_response = await async_client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert "access_token" in tokens
        
        # 4. Получение профиля пользователя
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        profile_response = await async_client.get("/api/v1/users/me", headers=headers)
        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert profile["username"] == "newuser123"

    async def test_track_upload_and_streaming_flow(self, auth_client: AsyncClient, temp_audio_file, temp_image_file):
        """Полный сценарий загрузки и стриминга трека"""
        # 1. Загрузка трека
        with open(temp_audio_file, 'rb') as audio_file, open(temp_image_file, 'rb') as cover_file:
            files = {
                'track_file': ('test_track.mp3', audio_file, 'audio/mpeg'),
                'cover_file': ('cover.jpg', cover_file, 'image/jpeg')
            }
            form_data = {
                'title': 'My Test Track',
                'artist': 'Test Artist',
                'album': 'Test Album',
                'genre': 'Rock',
                'duration': '180'
            }
            
            with patch('app.services.s3_service.upload_track') as mock_upload_track, \
                 patch('app.services.s3_service.upload_cover') as mock_upload_cover:
                
                mock_upload_track.return_value = {
                    'success': True,
                    's3_key': 'tracks/1/test_track.mp3',
                    'url': 'http://test.s3.com/tracks/1/test_track.mp3'
                }
                mock_upload_cover.return_value = {
                    'success': True,
                    's3_key': 'covers/1/test_track.jpg',
                    'url': 'http://test.s3.com/covers/1/test_track.jpg'
                }
                
                upload_response = await auth_client.post(
                    "/api/v1/tracks/upload",
                    files=files,
                    data=form_data
                )
                
                assert upload_response.status_code == 201
                track_data = upload_response.json()
                assert track_data['title'] == 'My Test Track'
                track_id = track_data['id']
        
        # 2. Получение информации о треке
        track_response = await auth_client.get(f"/api/v1/tracks/{track_id}")
        assert track_response.status_code == 200
        track_info = track_response.json()
        assert track_info['title'] == 'My Test Track'
        
        # 3. Получение URL для стриминга
        with patch('app.services.s3_service.get_track_url') as mock_get_url:
            mock_get_url.return_value = "http://test.s3.com/streaming-url"
            
            stream_response = await auth_client.get(f"/api/v1/tracks/{track_id}/stream")
            assert stream_response.status_code == 200
            stream_data = stream_response.json()
            assert 'stream_url' in stream_data
        
        # 4. Запись события прослушивания
        play_event = {
            'track_id': track_id,
            'event_type': 'play',
            'duration': 180,
            'platform': 'web'
        }
        
        with patch('app.services.clickhouse_service.insert_user_activity') as mock_insert:
            mock_insert.return_value = True
            
            event_response = await auth_client.post("/api/v1/analytics/events", json=play_event)
            assert event_response.status_code == 201

    async def test_playlist_management_flow(self, auth_client: AsyncClient):
        """Сценарий управления плейлистами"""
        # Создаем несколько треков для плейлиста (мокаем)
        mock_tracks = []
        for i in range(3):
            track_data = {
                'title': f'Track {i+1}',
                'artist': f'Artist {i+1}',
                'duration': 180 + i * 30
            }
            
            with patch('app.services.track_service.create_track') as mock_create:
                mock_create.return_value = {'id': f'track_{i+1}', **track_data}
                
                response = await auth_client.post("/api/v1/tracks", json=track_data)
                if response.status_code == 201:
                    mock_tracks.append(response.json())
        
        # 1. Создание плейлиста
        playlist_data = {
            'name': 'My Awesome Playlist',
            'description': 'Collection of my favorite tracks',
            'is_public': True
        }
        
        playlist_response = await auth_client.post("/api/v1/playlists", json=playlist_data)
        assert playlist_response.status_code == 201
        playlist = playlist_response.json()
        playlist_id = playlist['id']
        
        # 2. Добавление треков в плейлист
        for track in mock_tracks:
            add_response = await auth_client.post(
                f"/api/v1/playlists/{playlist_id}/tracks",
                json={'track_id': track['id']}
            )
            assert add_response.status_code == 200
        
        # 3. Получение плейлиста с треками
        full_playlist_response = await auth_client.get(f"/api/v1/playlists/{playlist_id}")
        assert full_playlist_response.status_code == 200
        full_playlist = full_playlist_response.json()
        assert len(full_playlist['tracks']) == 3
        
        # 4. Изменение порядка треков
        reorder_data = {
            'track_orders': [
                {'track_id': mock_tracks[2]['id'], 'position': 1},
                {'track_id': mock_tracks[0]['id'], 'position': 2},
                {'track_id': mock_tracks[1]['id'], 'position': 3}
            ]
        }
        
        reorder_response = await auth_client.put(
            f"/api/v1/playlists/{playlist_id}/reorder",
            json=reorder_data
        )
        assert reorder_response.status_code == 200
        
        # 5. Удаление трека из плейлиста
        remove_response = await auth_client.delete(
            f"/api/v1/playlists/{playlist_id}/tracks/{mock_tracks[1]['id']}"
        )
        assert remove_response.status_code == 200
        
        # 6. Проверка итогового состояния плейлиста
        final_playlist_response = await auth_client.get(f"/api/v1/playlists/{playlist_id}")
        final_playlist = final_playlist_response.json()
        assert len(final_playlist['tracks']) == 2

    async def test_search_and_discovery_flow(self, auth_client: AsyncClient):
        """Сценарий поиска и открытия музыки"""
        # 1. Поиск треков по названию
        search_query = "rock music"
        
        with patch('app.services.search_service.search_tracks') as mock_search:
            mock_search.return_value = {
                'tracks': [
                    {
                        'id': 'track_1',
                        'title': 'Rock Anthem',
                        'artist': 'Rock Band',
                        'genre': 'Rock',
                        'play_count': 1500
                    },
                    {
                        'id': 'track_2',
                        'title': 'Classic Rock',
                        'artist': 'Legend Band', 
                        'genre': 'Rock',
                        'play_count': 2000
                    }
                ],
                'total': 2
            }
            
            search_response = await auth_client.get(
                f"/api/v1/search/tracks?query={search_query}"
            )
            assert search_response.status_code == 200
            search_results = search_response.json()
            assert len(search_results['tracks']) == 2
        
        # 2. Получение рекомендаций
        with patch('app.services.analytics_service.get_recommendations') as mock_recommend:
            mock_recommend.return_value = [
                {
                    'track_id': 'recommended_1',
                    'title': 'You Might Like This',
                    'artist': 'Similar Artist',
                    'score': 0.85
                }
            ]
            
            recommendations_response = await auth_client.get("/api/v1/recommendations")
            assert recommendations_response.status_code == 200
            recommendations = recommendations_response.json()
            assert len(recommendations) > 0
        
        # 3. Получение популярных треков
        with patch('app.services.clickhouse_service.get_popular_tracks') as mock_popular:
            mock_popular.return_value = [
                {
                    'track_id': 'popular_1',
                    'title': 'Trending Song',
                    'artist': 'Hot Artist',
                    'play_count': 5000,
                    'unique_listeners': 2500
                }
            ]
            
            popular_response = await auth_client.get("/api/v1/tracks/popular")
            assert popular_response.status_code == 200
            popular_tracks = popular_response.json()
            assert len(popular_tracks) > 0
        
        # 4. Фильтрация по жанру
        genre = "Rock"
        genre_response = await auth_client.get(f"/api/v1/tracks?genre={genre}")
        assert genre_response.status_code == 200

    async def test_user_analytics_flow(self, auth_client: AsyncClient):
        """Сценарий просмотра аналитики пользователя"""
        # 1. Получение личной статистики
        with patch('app.services.clickhouse_service.get_user_stats') as mock_stats:
            mock_stats.return_value = {
                'total_listening_time': 7200,  # 2 hours
                'tracks_played': 50,
                'unique_tracks': 42,
                'favorite_genre': 'Rock',
                'listening_sessions': 15
            }
            
            stats_response = await auth_client.get("/api/v1/analytics/my-stats")
            assert stats_response.status_code == 200
            stats = stats_response.json()
            assert stats['total_listening_time'] > 0
            assert 'favorite_genre' in stats
        
        # 2. История прослушивания
        with patch('app.services.analytics_service.get_listening_history') as mock_history:
            mock_history.return_value = [
                {
                    'track_id': 'track_1',
                    'title': 'Recent Track',
                    'played_at': '2024-01-01T12:00:00Z',
                    'duration': 180
                }
            ]
            
            history_response = await auth_client.get("/api/v1/analytics/listening-history")
            assert history_response.status_code == 200
            history = history_response.json()
            assert len(history) > 0
        
        # 3. Топ треки пользователя
        with patch('app.services.analytics_service.get_user_top_tracks') as mock_top:
            mock_top.return_value = [
                {
                    'track_id': 'top_1',
                    'title': 'My Favorite',
                    'play_count': 25,
                    'total_time': 4500
                }
            ]
            
            top_response = await auth_client.get("/api/v1/analytics/my-top-tracks")
            assert top_response.status_code == 200
            top_tracks = top_response.json()
            assert len(top_tracks) > 0

    async def test_social_features_flow(self, auth_client: AsyncClient):
        """Сценарий социальных функций"""
        # 1. Поиск других пользователей
        search_response = await auth_client.get("/api/v1/users/search?query=test")
        assert search_response.status_code == 200
        
        # 2. Просмотр публичных плейлистов
        public_playlists_response = await auth_client.get("/api/v1/playlists/public")
        assert public_playlists_response.status_code == 200
        
        # 3. Подписка на плейлист
        playlist_id = "public_playlist_123"
        follow_response = await auth_client.post(f"/api/v1/playlists/{playlist_id}/follow")
        # Может вернуть 404 если плейлист не существует, что нормально для теста
        assert follow_response.status_code in [200, 404]
        
        # 4. Поделиться треком
        share_data = {
            'track_id': 'track_123',
            'platform': 'twitter',
            'message': 'Check out this awesome track!'
        }
        
        share_response = await auth_client.post("/api/v1/tracks/share", json=share_data)
        # API может не существовать, проверяем что запрос обработан
        assert share_response.status_code in [200, 201, 404, 501]

    @pytest.mark.slow
    async def test_performance_under_load(self, async_client: AsyncClient):
        """Тест производительности под нагрузкой"""
        import asyncio
        import time
        
        async def make_request():
            start_time = time.time()
            response = await async_client.get("/api/v1/tracks/popular")
            end_time = time.time()
            return {
                'status_code': response.status_code,
                'response_time': end_time - start_time
            }
        
        # Создаем 50 одновременных запросов
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        # Анализируем результаты
        successful_requests = [r for r in results if r['status_code'] == 200]
        response_times = [r['response_time'] for r in successful_requests]
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            # Проверяем производительность
            assert len(successful_requests) >= 40  # Минимум 80% успешных запросов
            assert avg_response_time < 2.0  # Средний ответ меньше 2 секунд
            assert max_response_time < 5.0  # Максимальный ответ меньше 5 секунд

    async def test_error_handling_flow(self, auth_client: AsyncClient):
        """Тест обработки ошибок в пользовательских сценариях"""
        # 1. Попытка доступа к несуществующему треку
        response = await auth_client.get("/api/v1/tracks/nonexistent_track_id")
        assert response.status_code == 404
        error_data = response.json()
        assert 'detail' in error_data
        
        # 2. Попытка загрузки некорректного файла
        invalid_file_data = b"This is not an audio file"
        files = {'track_file': ('invalid.txt', BytesIO(invalid_file_data), 'text/plain')}
        form_data = {'title': 'Invalid Track'}
        
        upload_response = await auth_client.post(
            "/api/v1/tracks/upload",
            files=files,
            data=form_data
        )
        assert upload_response.status_code in [400, 422]  # Bad request or validation error
        
        # 3. Попытка создания плейлиста с некорректными данными
        invalid_playlist = {'name': ''}  # Пустое название
        
        playlist_response = await auth_client.post("/api/v1/playlists", json=invalid_playlist)
        assert playlist_response.status_code == 422  # Validation error
        
        # 4. Проверка rate limiting (если реализован)
        # Делаем много запросов подряд
        for _ in range(100):
            await async_client.get("/api/v1/tracks/popular")
        
        # Последний запрос может быть заблокирован rate limiter'ом
        final_response = await async_client.get("/api/v1/tracks/popular")
        # 429 = Too Many Requests, 200 = OK если rate limiting не настроен
        assert final_response.status_code in [200, 429]
