"""
Утилиты для тестирования
Вспомогательные функции и классы для создания красивых и удобных тестов
"""

import asyncio
import json
import tempfile
from typing import Any, Dict, List, Optional, Union
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient, Response
from faker import Faker

fake = Faker(['ru_RU', 'en_US'])


class TestDataBuilder:
    """Построитель тестовых данных с fluent interface"""
    
    def __init__(self):
        self.data = {}
    
    def with_user(self, username: str = None, email: str = None, 
                  role: str = "user", **kwargs) -> "TestDataBuilder":
        """Добавляет пользователя"""
        self.data["user"] = {
            "username": username or fake.user_name(),
            "email": email or fake.email(),
            "full_name": kwargs.get("full_name", fake.name()),
            "role": role,
            "is_active": kwargs.get("is_active", True),
            **kwargs
        }
        return self
    
    def with_track(self, title: str = None, artist: str = None, 
                   duration: int = None, **kwargs) -> "TestDataBuilder":
        """Добавляет трек"""
        self.data["track"] = {
            "title": title or fake.sentence(nb_words=3),
            "artist": artist or fake.name(),
            "album": kwargs.get("album", fake.sentence(nb_words=2)),
            "duration": duration or fake.random_int(min=60, max=300),
            "genre": kwargs.get("genre", fake.random_element(elements=['Rock', 'Pop', 'Jazz', 'Electronic'])),
            "release_date": kwargs.get("release_date", fake.date_this_decade().isoformat()),
            **kwargs
        }
        return self
    
    def with_analytics_event(self, event_type: str = "play", 
                           timestamp: datetime = None, **kwargs) -> "TestDataBuilder":
        """Добавляет аналитическое событие"""
        if "analytics" not in self.data:
            self.data["analytics"] = []
        
        event = {
            "user_id": kwargs.get("user_id", 1),
            "track_id": kwargs.get("track_id", "track_1"),
            "event_type": event_type,
            "timestamp": (timestamp or datetime.now()).isoformat(),
            "duration": kwargs.get("duration", 180),
            "platform": kwargs.get("platform", "web"),
            "quality": kwargs.get("quality", "standard"),
            **kwargs
        }
        self.data["analytics"].append(event)
        return self
    
    def with_multiple_events(self, count: int, **kwargs) -> "TestDataBuilder":
        """Добавляет несколько событий"""
        for i in range(count):
            self.with_analytics_event(
                timestamp=datetime.now() - timedelta(hours=i),
                track_id=f"track_{i+1}",
                **kwargs
            )
        return self
    
    def build(self) -> Dict[str, Any]:
        """Возвращает собранные данные"""
        return self.data


class ApiTestHelper:
    """Помощник для тестирования API"""
    
    def __init__(self, client: AsyncClient):
        self.client = client
    
    async def post_json(self, url: str, data: Dict[str, Any], 
                       headers: Dict[str, str] = None) -> Response:
        """POST запрос с JSON данными"""
        return await self.client.post(
            url, 
            json=data, 
            headers=headers or {"Content-Type": "application/json"}
        )
    
    async def upload_file(self, url: str, file_path: str, 
                         field_name: str = "file", **form_data) -> Response:
        """Загрузка файла"""
        with open(file_path, "rb") as f:
            files = {field_name: f}
            data = form_data
            return await self.client.post(url, files=files, data=data)
    
    async def assert_status(self, response: Response, expected: int):
        """Проверка статуса ответа с детальной информацией"""
        if response.status_code != expected:
            error_detail = f"""
            Expected status: {expected}
            Actual status: {response.status_code}
            URL: {response.url}
            Response body: {response.text}
            """
            pytest.fail(error_detail)
    
    async def assert_json_contains(self, response: Response, expected: Dict[str, Any]):
        """Проверка что JSON ответ содержит ожидаемые поля"""
        actual = response.json()
        for key, value in expected.items():
            assert key in actual, f"Ключ '{key}' не найден в ответе"
            if isinstance(value, dict):
                assert isinstance(actual[key], dict), f"Значение '{key}' не является словарем"
                # Рекурсивная проверка вложенных словарей
                for nested_key, nested_value in value.items():
                    assert nested_key in actual[key], f"Вложенный ключ '{nested_key}' не найден"
                    assert actual[key][nested_key] == nested_value
            else:
                assert actual[key] == value, f"Значение для '{key}' не совпадает: ожидалось {value}, получено {actual[key]}"
    
    async def assert_pagination(self, response: Response, expected_total: int = None):
        """Проверка пагинации"""
        data = response.json()
        assert "data" in data, "Ответ должен содержать поле 'data'"
        assert "pagination" in data, "Ответ должен содержать поле 'pagination'"
        
        pagination = data["pagination"]
        assert "page" in pagination
        assert "per_page" in pagination
        assert "total" in pagination
        assert "pages" in pagination
        
        if expected_total is not None:
            assert pagination["total"] == expected_total


class MockServiceBuilder:
    """Построитель моков для сервисов"""
    
    @staticmethod
    def clickhouse_service(
        connection_working: bool = True,
        popular_tracks: List[Dict] = None,
        user_stats: Dict = None
    ) -> AsyncMock:
        """Создает мок для ClickHouse сервиса"""
        mock = AsyncMock()
        mock.test_connection.return_value = connection_working
        
        mock.get_popular_tracks.return_value = popular_tracks or [
            {"track_id": "track_1", "play_count": 100, "unique_listeners": 50},
            {"track_id": "track_2", "play_count": 80, "unique_listeners": 40},
        ]
        
        mock.get_user_stats.return_value = user_stats or {
            "total_listening_time": 3600,
            "tracks_played": 25,
            "favorite_genre": "Rock"
        }
        
        mock.record_listening_event.return_value = True
        mock.get_listening_history.return_value = []
        
        return mock
    
    @staticmethod
    def s3_service(upload_success: bool = True) -> MagicMock:
        """Создает мок для S3 сервиса"""
        mock = MagicMock()
        
        if upload_success:
            mock.upload_track.return_value = {
                'success': True,
                's3_key': 'test/track.mp3',
                'bucket': 'tracks',
                'file_size': 1024000,
                'url': 'http://test.s3.com/track.mp3'
            }
        else:
            mock.upload_track.return_value = {
                'success': False,
                'error': 'Upload failed'
            }
        
        mock.get_track_url.return_value = "http://test.s3.com/presigned-url"
        mock.delete_track.return_value = upload_success
        
        return mock


class DatabaseTestHelper:
    """Помощник для работы с тестовой базой данных"""
    
    def __init__(self, session):
        self.session = session
    
    async def create_user(self, **kwargs) -> Dict[str, Any]:
        """Создает пользователя в БД"""
        from app.db.models import User
        
        user_data = {
            "username": fake.user_name(),
            "email": fake.email(),
            "full_name": fake.name(),
            "hashed_password": "hashed_password",
            "role": "user",
            "is_active": True,
            **kwargs
        }
        
        user = User(**user_data)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active
        }
    
    async def create_track(self, user_id: int = None, **kwargs) -> Dict[str, Any]:
        """Создает трек в БД"""
        from app.db.models import Track
        
        track_data = {
            "title": fake.sentence(nb_words=3),
            "artist": fake.name(),
            "album": fake.sentence(nb_words=2),
            "duration": fake.random_int(min=60, max=300),
            "file_path": f"tracks/{fake.uuid4()}.mp3",
            "user_id": user_id or 1,
            **kwargs
        }
        
        track = Track(**track_data)
        self.session.add(track)
        await self.session.commit()
        await self.session.refresh(track)
        
        return {
            "id": track.id,
            "title": track.title,
            "artist": track.artist,
            "album": track.album,
            "duration": track.duration,
            "file_path": track.file_path,
            "user_id": track.user_id
        }


class PerformanceTestHelper:
    """Помощник для тестирования производительности"""
    
    @staticmethod
    async def measure_async_time(coro):
        """Измеряет время выполнения асинхронной функции"""
        import time
        start = time.time()
        result = await coro
        end = time.time()
        return result, end - start
    
    @staticmethod
    def measure_time(func):
        """Измеряет время выполнения функции"""
        import time
        start = time.time()
        result = func()
        end = time.time()
        return result, end - start
    
    @staticmethod
    def assert_performance(duration: float, max_time: float, operation_name: str = "Operation"):
        """Проверяет что операция выполнилась в заданное время"""
        assert duration <= max_time, f"{operation_name} заняла {duration:.3f}s, ожидалось не более {max_time}s"


class FileTestHelper:
    """Помощник для работы с файлами в тестах"""
    
    @staticmethod
    def create_temp_audio_file(size_kb: int = 100) -> str:
        """Создает временный аудио файл"""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            # Простой MP3 заголовок
            f.write(b"ID3\x03\x00\x00\x00")
            # Заполняем данными до нужного размера
            f.write(b"\x00" * (size_kb * 1024 - 10))
            return f.name
    
    @staticmethod
    def create_temp_image_file(size_kb: int = 50) -> str:
        """Создает временный файл изображения"""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            # Простой JPEG заголовок
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF")
            # Заполняем данными до нужного размера
            f.write(b"\x00" * (size_kb * 1024 - 20))
            return f.name


class ClickHouseTestHelper:
    """Помощник для тестирования ClickHouse"""
    
    def __init__(self, client):
        self.client = client
    
    async def insert_test_analytics(self, events: List[Dict]):
        """Вставляет тестовые аналитические данные"""
        if not events:
            return
        
        values = []
        for event in events:
            values.append([
                event.get("timestamp", datetime.now()),
                event.get("user_id", 1),
                event.get("track_id", "track_1"),
                event.get("event_type", "play"),
                event.get("duration", 180),
                event.get("quality", "standard"),
                event.get("platform", "web"),
                json.dumps(event.get("metadata", {}))
            ])
        
        await self.client.execute(
            """
            INSERT INTO track_analytics 
            (timestamp, user_id, track_id, event_type, duration, quality, platform, metadata)
            VALUES
            """,
            values
        )
    
    async def cleanup_test_data(self):
        """Очищает тестовые данные"""
        tables = ["track_analytics", "user_analytics", "search_analytics", "artist_analytics", "api_requests_log"]
        
        for table in tables:
            try:
                await self.client.execute(f"TRUNCATE TABLE {table}")
            except Exception:
                pass  # Игнорируем ошибки если таблица не существует


# Декораторы для тестов
def skip_if_no_docker():
    """Пропускает тест если Docker недоступен"""
    import shutil
    return pytest.mark.skipif(
        shutil.which("docker") is None,
        reason="Docker не установлен"
    )


def requires_service(service_name: str):
    """Пропускает тест если сервис недоступен"""
    def decorator(func):
        return pytest.mark.skipif(
            os.getenv(f"TEST_{service_name.upper()}_AVAILABLE") != "true",
            reason=f"Сервис {service_name} недоступен для тестирования"
        )(func)
    return decorator


# Утилиты для красивого вывода
class TestReporter:
    """Красивый репортер для тестов"""
    
    @staticmethod
    def print_test_header(test_name: str):
        """Печатает заголовок теста"""
        print(f"\n{'='*60}")
        print(f"🧪 {test_name}")
        print(f"{'='*60}")
    
    @staticmethod
    def print_success(message: str):
        """Печатает сообщение об успехе"""
        print(f"✅ {message}")
    
    @staticmethod
    def print_error(message: str):
        """Печатает сообщение об ошибке"""
        print(f"❌ {message}")
    
    @staticmethod
    def print_info(message: str):
        """Печатает информационное сообщение"""
        print(f"ℹ️  {message}")
    
    @staticmethod
    def print_performance(operation: str, duration: float):
        """Печатает информацию о производительности"""
        if duration < 0.1:
            emoji = "⚡"
        elif duration < 1.0:
            emoji = "🚀"
        else:
            emoji = "🐌"
        
        print(f"{emoji} {operation}: {duration:.3f}s")
