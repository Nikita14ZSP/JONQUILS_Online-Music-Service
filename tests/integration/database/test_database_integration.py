"""
Интеграционные тесты для базы данных
Тестируют взаимодействие с реальной базой данных
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.models import User, Track, Artist, Album
from app.services.user_service import UserService
from app.services.track_service import TrackService
from app.services.artist_service import ArtistService
from app.services.album_service import AlbumService


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseIntegration:
    """Тесты интеграции с базой данных"""
    
    @pytest_asyncio.fixture
    async def user_service(self, test_db_session):
        """Фикстура сервиса пользователей"""
        return UserService(test_db_session)
    
    @pytest_asyncio.fixture
    async def track_service(self, test_db_session):
        """Фикстура сервиса треков"""
        return TrackService(test_db_session)
    
    @pytest_asyncio.fixture
    async def artist_service(self, test_db_session):
        """Фикстура сервиса артистов"""
        return ArtistService(test_db_session)
    
    @pytest_asyncio.fixture
    async def album_service(self, test_db_session):
        """Фикстура сервиса альбомов"""
        return AlbumService(test_db_session)

    async def test_database_connection(self, test_db_session: AsyncSession):
        """Тест подключения к базе данных"""
        result = await test_db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    async def test_user_crud_operations(self, user_service: UserService):
        """Тест CRUD операций с пользователями"""
        # Create
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
        created_user = await user_service.create_user(user_data)
        assert created_user.username == "testuser"
        assert created_user.email == "test@example.com"
        
        # Read
        found_user = await user_service.get_user_by_id(created_user.id)
        assert found_user is not None
        assert found_user.username == "testuser"
        
        # Update
        updated_user = await user_service.update_user(
            created_user.id, 
            {"full_name": "Updated Name"}
        )
        assert updated_user.full_name == "Updated Name"
        
        # Delete
        deleted = await user_service.delete_user(created_user.id)
        assert deleted is True
        
        # Verify deletion
        deleted_user = await user_service.get_user_by_id(created_user.id)
        assert deleted_user is None

    async def test_track_with_relationships(
        self, 
        track_service: TrackService,
        artist_service: ArtistService,
        album_service: AlbumService
    ):
        """Тест создания трека с связанными объектами"""
        # Создаем артиста
        artist_data = {
            "name": "Test Artist",
            "genre": "Rock",
            "bio": "Test bio"
        }
        artist = await artist_service.create_artist(artist_data)
        
        # Создаем альбом
        album_data = {
            "title": "Test Album",
            "artist_id": artist.id,
            "release_date": "2024-01-01"
        }
        album = await album_service.create_album(album_data)
        
        # Создаем трек
        track_data = {
            "title": "Test Track",
            "artist_id": artist.id,
            "album_id": album.id,
            "duration": 180,
            "genre": "Rock"
        }
        track = await track_service.create_track(track_data)
        
        # Проверяем связи
        track_with_relations = await track_service.get_track_with_relations(track.id)
        assert track_with_relations.artist.name == "Test Artist"
        assert track_with_relations.album.title == "Test Album"

    async def test_database_transactions(self, test_db_session: AsyncSession):
        """Тест транзакций базы данных"""
        try:
            # Начинаем транзакцию
            async with test_db_session.begin():
                # Создаем пользователя
                user = User(
                    username="transaction_test",
                    email="trans@test.com",
                    password_hash="hashed",
                    full_name="Transaction Test"
                )
                test_db_session.add(user)
                await test_db_session.flush()  # Получаем ID без коммита
                
                user_id = user.id
                assert user_id is not None
                
                # Проверяем, что пользователь виден в текущей транзакции
                result = await test_db_session.execute(
                    text("SELECT COUNT(*) FROM users WHERE id = :id"),
                    {"id": user_id}
                )
                assert result.scalar() == 1
                
                # Принудительно вызываем исключение для отката
                raise Exception("Test rollback")
                
        except Exception as e:
            if "Test rollback" not in str(e):
                raise
        
        # Проверяем, что транзакция откатилась
        result = await test_db_session.execute(
            text("SELECT COUNT(*) FROM users WHERE username = 'transaction_test'")
        )
        assert result.scalar() == 0

    async def test_concurrent_operations(self, test_db_session: AsyncSession):
        """Тест конкурентных операций"""
        import asyncio
        
        async def create_user(index):
            user = User(
                username=f"concurrent_user_{index}",
                email=f"concurrent{index}@test.com",
                password_hash="hashed",
                full_name=f"Concurrent User {index}"
            )
            test_db_session.add(user)
            await test_db_session.flush()
            return user.id
        
        # Создаем несколько пользователей параллельно
        tasks = [create_user(i) for i in range(5)]
        user_ids = await asyncio.gather(*tasks)
        
        await test_db_session.commit()
        
        # Проверяем, что все пользователи созданы
        result = await test_db_session.execute(
            text("SELECT COUNT(*) FROM users WHERE username LIKE 'concurrent_user_%'")
        )
        assert result.scalar() == 5
        
        # Проверяем уникальность ID
        assert len(set(user_ids)) == 5

    async def test_database_indexes_performance(self, test_db_session: AsyncSession):
        """Тест производительности индексов"""
        # Создаем много пользователей для тестирования индексов
        users = []
        for i in range(100):
            user = User(
                username=f"perf_user_{i:03d}",
                email=f"perf{i:03d}@test.com",
                password_hash="hashed",
                full_name=f"Performance User {i}"
            )
            users.append(user)
        
        test_db_session.add_all(users)
        await test_db_session.commit()
        
        # Тестируем поиск по username (должен использовать индекс)
        import time
        start_time = time.time()
        
        result = await test_db_session.execute(
            text("SELECT * FROM users WHERE username = 'perf_user_050'")
        )
        user = result.fetchone()
        
        query_time = time.time() - start_time
        
        assert user is not None
        assert query_time < 0.1  # Запрос должен быть быстрым с индексом

    @pytest.mark.slow
    async def test_large_dataset_operations(self, test_db_session: AsyncSession):
        """Тест операций с большими наборами данных"""
        # Создаем большое количество треков
        tracks = []
        for i in range(1000):
            track = Track(
                title=f"Track {i:04d}",
                duration=180 + (i % 120),  # Варьируем длительность
                genre="Test Genre",
                file_path=f"/test/track_{i:04d}.mp3"
            )
            tracks.append(track)
        
        # Тестируем bulk insert
        import time
        start_time = time.time()
        
        test_db_session.add_all(tracks)
        await test_db_session.commit()
        
        insert_time = time.time() - start_time
        
        # Проверяем, что все треки созданы
        result = await test_db_session.execute(
            text("SELECT COUNT(*) FROM tracks WHERE title LIKE 'Track %'")
        )
        track_count = result.scalar()
        
        assert track_count == 1000
        assert insert_time < 10.0  # Bulk insert должен быть относительно быстрым
        
        # Тестируем агрегацию
        start_time = time.time()
        
        result = await test_db_session.execute(
            text("SELECT AVG(duration), MIN(duration), MAX(duration) FROM tracks")
        )
        avg_duration, min_duration, max_duration = result.fetchone()
        
        aggregation_time = time.time() - start_time
        
        assert avg_duration > 0
        assert min_duration == 180
        assert max_duration == 299
        assert aggregation_time < 1.0  # Агрегация должна быть быстрой
