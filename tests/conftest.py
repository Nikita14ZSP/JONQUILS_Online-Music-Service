"""
Главный файл конфигурации для pytest
Содержит основные фикстуры и настройки тестирования
"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.config import settings
from app.db.database import get_db, Base
from app.core.deps import get_current_user
from app.services.clickhouse_service import clickhouse_service
from app.services.s3_service import s3_service
from app.schemas.user import User


def pytest_configure(config):
    """Конфигурация pytest"""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "e2e: end-to-end tests")
    config.addinivalue_line("markers", "slow: slow running tests")
    config.addinivalue_line("markers", "database: tests requiring database")
    config.addinivalue_line("markers", "s3: tests requiring S3 storage")
    config.addinivalue_line("markers", "clickhouse: tests requiring ClickHouse")
    config.addinivalue_line("markers", "elasticsearch: tests requiring Elasticsearch")

@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для всей сессии"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_db_engine():
    """Тестовый движок базы данных (in-memory SQLite)"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Тестовая сессия базы данных"""
    TestSessionLocal = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_app(test_db_session):
    """Тестовое приложение FastAPI с подменой зависимостей"""
    def override_get_db():
        return test_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Асинхронный HTTP клиент для тестирования API"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def auth_client(async_client, test_user) -> AsyncGenerator[AsyncClient, None]:
    """Авторизованный HTTP клиент"""
    def override_get_current_user():
        return test_user
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield async_client
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


@pytest_asyncio.fixture
async def admin_client(async_client, admin_user) -> AsyncGenerator[AsyncClient, None]:
    """HTTP клиент для администратора"""
    def override_get_current_user():
        return admin_user
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield async_client
    if get_current_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_user]


@pytest.fixture
def test_user() -> User:
    """Тестовый пользователь"""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        role="user",
        is_active=True
    )


@pytest.fixture
def admin_user() -> User:
    """Администратор"""
    return User(
        id=999,
        username="admin",
        email="admin@example.com",
        full_name="Admin User",
        role="admin",
        is_active=True
    )

@pytest.fixture
def mock_clickhouse_service():
    """Мок для ClickHouse сервиса"""
    mock = AsyncMock()

    mock.test_connection.return_value = True
    mock.create_tables.return_value = True
    mock.get_popular_tracks.return_value = [
        {"track_id": "track_1", "play_count": 100, "unique_listeners": 50},
        {"track_id": "track_2", "play_count": 80, "unique_listeners": 40},
    ]
    mock.get_user_stats.return_value = {
        "total_listening_time": 3600,
        "tracks_played": 25,
        "favorite_genre": "Rock"
    }
    
    return mock


@pytest.fixture
def mock_s3_service():
    """Мок для S3 сервиса"""
    mock = MagicMock()

    mock.upload_track.return_value = {
        'success': True,
        's3_key': 'test/track.mp3',
        'bucket': 'tracks',
        'file_size': 1024000,
        'url': 'http://test.s3.com/track.mp3'
    }
    mock.upload_cover.return_value = {
        'success': True,
        's3_key': 'test/cover.jpg',
        'bucket': 'covers',
        'url': 'http://test.s3.com/cover.jpg'
    }
    mock.get_track_url.return_value = "http://test.s3.com/presigned-url"
    mock.delete_track.return_value = True
    mock.list_user_tracks.return_value = []
    
    return mock


@pytest.fixture
def mock_elasticsearch():
    """Мок для Elasticsearch"""
    mock = AsyncMock()
    
    mock.search.return_value = {
        "hits": {
            "total": {"value": 2},
            "hits": [
                {"_source": {"title": "Test Track 1", "artist": "Test Artist"}},
                {"_source": {"title": "Test Track 2", "artist": "Another Artist"}}
            ]
        }
    }
    mock.index.return_value = {"result": "created"}
    mock.delete.return_value = {"result": "deleted"}
    
    return mock

@pytest.fixture
def sample_track_data():
    """Образец данных трека"""
    return {
        "title": "Test Track",
        "artist": "Test Artist",
        "album": "Test Album",
        "duration": 180,
        "genre": "Rock",
        "release_date": "2024-01-01"
    }


@pytest.fixture
def sample_user_data():
    """Образец данных пользователя"""
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "testpassword123",
        "full_name": "New User"
    }


@pytest.fixture
def sample_analytics_data():
    """Образец аналитических данных"""
    return [
        {
            "user_id": 1,
            "track_id": "track_1",
            "event_type": "play",
            "timestamp": "2024-01-01T12:00:00",
            "duration": 180,
            "platform": "web"
        },
        {
            "user_id": 1,
            "track_id": "track_2", 
            "event_type": "skip",
            "timestamp": "2024-01-01T12:05:00",
            "duration": 30,
            "platform": "mobile"
        }
    ]

@pytest.fixture
def temp_audio_file():
    """Временный аудио файл для тестирования"""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_file.write(b"ID3\x03\x00\x00\x00" + b"\x00" * 1000)
        temp_file_path = temp_file.name
    
    yield temp_file_path
    
    try:
        os.unlink(temp_file_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def temp_image_file():
    """Временный файл изображения для тестирования"""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        temp_file.write(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 1000)
        temp_file_path = temp_file.name
    
    yield temp_file_path
    
    try:
        os.unlink(temp_file_path)
    except FileNotFoundError:
        pass

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Автоматическая настройка тестового окружения"""
    test_env = {
        "TESTING": "true",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "S3_ENDPOINT_URL": "http://test-minio:9000",
        "CLICKHOUSE_HOST": "test-clickhouse",
        "ELASTICSEARCH_HOST": "test-elasticsearch",
        "REDIS_HOST": "test-redis"
    }
    
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield
    
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def mock_datetime():
    """Мок для datetime с фиксированным временем"""
    from unittest.mock import patch
    from datetime import datetime
    
    fixed_time = datetime(2024, 1, 1, 12, 0, 0)
    
    with patch('app.services.analytics_service.datetime') as mock_dt:
        mock_dt.now.return_value = fixed_time
        mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
        yield mock_dt


@pytest.fixture
def performance_monitor():
    """Фикстура для мониторинга производительности тестов"""
    import time
    
    start_time = time.time()
    yield
    end_time = time.time()
    
    duration = end_time - start_time
    if duration > 1.0:  
        print(f"\n  Медленный тест: {duration:.2f}s")


@pytest_asyncio.fixture
async def real_clickhouse_client():
    """Реальный клиент ClickHouse для интеграционных тестов"""
    if os.getenv("TESTING_WITH_REAL_SERVICES") != "true":
        pytest.skip("Интеграционные тесты отключены")
    
    try:
        await clickhouse_service.test_connection()
        yield clickhouse_service
    except Exception as e:
        pytest.skip(f"ClickHouse недоступен: {e}")


@pytest.fixture
def real_s3_client():
    """Реальный клиент S3 для интеграционных тестов"""
    if os.getenv("TESTING_WITH_REAL_SERVICES") != "true":
        pytest.skip("Интеграционные тесты отключены")
    
    try:
        s3_service.get_storage_stats()
        yield s3_service
    except Exception as e:
        pytest.skip(f"S3 недоступен: {e}")


@pytest.fixture
def assert_timing():
    """Утилита для проверки времени выполнения"""
    def _assert_timing(func, max_time=1.0):
        import time
        start = time.time()
        result = func()
        duration = time.time() - start
        assert duration <= max_time, f"Операция заняла {duration:.2f}s, ожидалось не более {max_time}s"
        return result
    
    return _assert_timing


@pytest.fixture
def test_data_factory():
    """Фабрика для создания тестовых данных"""
    from factory import Factory, Faker, Sequence
    
    class TrackFactory(Factory):
        title = Faker('sentence', nb_words=3)
        artist = Faker('name')
        album = Faker('sentence', nb_words=2)
        duration = Faker('random_int', min=60, max=300)
        genre = Faker('random_element', elements=('Rock', 'Pop', 'Jazz', 'Classical'))
    
    class UserFactory(Factory):
        username = Sequence(lambda n: f"user{n}")
        email = Faker('email')
        full_name = Faker('name')
        role = "user"
        is_active = True
    
    return {
        'track': TrackFactory,
        'user': UserFactory
    }
