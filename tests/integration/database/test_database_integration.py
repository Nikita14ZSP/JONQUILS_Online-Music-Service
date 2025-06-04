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
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "full_name": "Test User"
        }
        created_user = await user_service.create_user(user_data)
        assert created_user.username == "testuser"
        assert created_user.email == "test@example.com"
        
        found_user = await user_service.get_user_by_id(created_user.id)
        assert found_user is not None
        assert found_user.username == "testuser"
        
        updated_user = await user_service.update_user(
            created_user.id, 
            {"full_name": "Updated Name"}
        )
        assert updated_user.full_name == "Updated Name"
        
        deleted = await user_service.delete_user(created_user.id)
        assert deleted is True
        
        deleted_user = await user_service.get_user_by_id(created_user.id)
        assert deleted_user is None

    async def test_track_with_relationships(
        self, 
        track_service: TrackService,
        artist_service: ArtistService,
        album_service: AlbumService
    ):
        """Тест создания трека с связанными объектами"""
        artist_data = {
            "name": "Test Artist",
            "genre": "Rock",
            "bio": "Test bio"
        }
        artist = await artist_service.create_artist(artist_data)
        
        album_data = {
            "title": "Test Album",
            "artist_id": artist.id,
            "release_date": "2024-01-01"
        }
        album = await album_service.create_album(album_data)
        
        track_data = {
            "title": "Test Track",
            "artist_id": artist.id,
            "album_id": album.id,
            "duration": 180,
            "genre": "Rock"
        }
        track = await track_service.create_track(track_data)
        
        track_with_relations = await track_service.get_track_with_relations(track.id)
        assert track_with_relations.artist.name == "Test Artist"
        assert track_with_relations.album.title == "Test Album"

    async def test_database_transactions(self, test_db_session: AsyncSession):
        """Тест транзакций базы данных"""
        try:
            async with test_db_session.begin():
                user = User(
                    username="transaction_test",
                    email="trans@test.com",
                    password_hash="hashed",
                    full_name="Transaction Test"
                )
                test_db_session.add(user)
                await test_db_session.flush()  
                
                user_id = user.id
                assert user_id is not None
                
                result = await test_db_session.execute(
                    text("SELECT COUNT(*) FROM users WHERE id = :id"),
                    {"id": user_id}
                )
                assert result.scalar() == 1
                
                raise Exception("Test rollback")
                
        except Exception as e:
            if "Test rollback" not in str(e):
                raise
        
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
        
        tasks = [create_user(i) for i in range(5)]
        user_ids = await asyncio.gather(*tasks)
        
        await test_db_session.commit()
        
        result = await test_db_session.execute(
            text("SELECT COUNT(*) FROM users WHERE username LIKE 'concurrent_user_%'")
        )
        assert result.scalar() == 5
        
        assert len(set(user_ids)) == 5

    async def test_database_indexes_performance(self, test_db_session: AsyncSession):
        """Тест производительности индексов"""
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
        
        import time
        start_time = time.time()
        
        result = await test_db_session.execute(
            text("SELECT * FROM users WHERE username = 'perf_user_050'")
        )
        user = result.fetchone()
        
        query_time = time.time() - start_time
        
        assert user is not None
        assert query_time < 0.1 

    @pytest.mark.slow
    async def test_large_dataset_operations(self, test_db_session: AsyncSession):
        """Тест операций с большими наборами данных"""
        tracks = []
        for i in range(1000):
            track = Track(
                title=f"Track {i:04d}",
                duration=180 + (i % 120),  
                genre="Test Genre",
                file_path=f"/test/track_{i:04d}.mp3"
            )
            tracks.append(track)
        
        import time
        start_time = time.time()
        
        test_db_session.add_all(tracks)
        await test_db_session.commit()
        
        insert_time = time.time() - start_time
        
        result = await test_db_session.execute(
            text("SELECT COUNT(*) FROM tracks WHERE title LIKE 'Track %'")
        )
        track_count = result.scalar()
        
        assert track_count == 1000
        assert insert_time < 10.0  
        
        start_time = time.time()
        
        result = await test_db_session.execute(
            text("SELECT AVG(duration), MIN(duration), MAX(duration) FROM tracks")
        )
        avg_duration, min_duration, max_duration = result.fetchone()
        
        aggregation_time = time.time() - start_time
        
        assert avg_duration > 0
        assert min_duration == 180
        assert max_duration == 299
        assert aggregation_time < 1.0  
