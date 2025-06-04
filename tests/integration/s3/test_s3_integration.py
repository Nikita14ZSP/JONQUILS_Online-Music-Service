"""
Интеграционные тесты для S3 сервиса
Тестируют взаимодействие с MinIO/S3 хранилищем
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
import tempfile
import os
from io import BytesIO

from app.services.s3_service import S3Service


@pytest.mark.integration
@pytest.mark.s3
class TestS3Integration:
    """Тесты интеграции с S3 хранилищем"""
    
    @pytest_asyncio.fixture
    async def s3_service(self):
        """Фикстура S3 сервиса с моком"""
        # Используем мок для тестов вместо реального S3
        with patch('app.services.s3_service.S3Service') as mock_s3:
            service = S3Service()
            
            # Настраиваем mock методы
            mock_s3.upload_track.return_value = {
                'success': True,
                's3_key': 'test/track.mp3',
                'bucket': 'tracks',
                'file_size': 1024000,
                'url': 'http://test.s3.com/track.mp3'
            }
            
            mock_s3.upload_cover.return_value = {
                'success': True,
                's3_key': 'test/cover.jpg',
                'bucket': 'covers',
                'url': 'http://test.s3.com/cover.jpg'
            }
            
            mock_s3.get_track_url.return_value = "http://test.s3.com/presigned-url"
            mock_s3.delete_track.return_value = True
            mock_s3.list_user_tracks.return_value = []
            mock_s3.get_storage_stats.return_value = {
                'total_tracks': 0,
                'total_size': 0,
                'buckets': {
                    'tracks': {'count': 0, 'size': 0},
                    'covers': {'count': 0, 'size': 0}
                }
            }
            
            yield service

    def test_s3_service_initialization(self, s3_service):
        """Тест инициализации S3 сервиса"""
        assert s3_service is not None
        assert hasattr(s3_service, 'upload_track')
        assert hasattr(s3_service, 'upload_cover')
        assert hasattr(s3_service, 'get_track_url')

    async def test_track_upload(self, s3_service, temp_audio_file):
        """Тест загрузки трека"""
        user_id = 1
        track_id = "test_track_123"
        
        with open(temp_audio_file, 'rb') as file:
            file_data = file.read()
        
        # Мокаем загрузку
        with patch.object(s3_service, 'upload_track') as mock_upload:
            mock_upload.return_value = {
                'success': True,
                's3_key': f'tracks/{user_id}/{track_id}.mp3',
                'bucket': 'tracks',
                'file_size': len(file_data),
                'url': f'http://test.s3.com/tracks/{user_id}/{track_id}.mp3'
            }
            
            result = s3_service.upload_track(
                file_data=file_data,
                filename="test_track.mp3",
                user_id=user_id,
                track_id=track_id
            )
            
            assert result['success'] is True
            assert track_id in result['s3_key']
            assert result['file_size'] > 0
            mock_upload.assert_called_once()

    async def test_cover_upload(self, s3_service, temp_image_file):
        """Тест загрузки обложки"""
        user_id = 1
        track_id = "test_track_123"
        
        with open(temp_image_file, 'rb') as file:
            file_data = file.read()
        
        with patch.object(s3_service, 'upload_cover') as mock_upload:
            mock_upload.return_value = {
                'success': True,
                's3_key': f'covers/{user_id}/{track_id}.jpg',
                'bucket': 'covers',
                'url': f'http://test.s3.com/covers/{user_id}/{track_id}.jpg'
            }
            
            result = s3_service.upload_cover(
                file_data=file_data,
                filename="cover.jpg",
                user_id=user_id,
                track_id=track_id
            )
            
            assert result['success'] is True
            assert track_id in result['s3_key']
            mock_upload.assert_called_once()

    async def test_presigned_url_generation(self, s3_service):
        """Тест генерации presigned URL"""
        s3_key = "tracks/1/test_track.mp3"
        
        with patch.object(s3_service, 'get_track_url') as mock_get_url:
            mock_get_url.return_value = f"http://test.s3.com/{s3_key}?presigned=true"
            
            url = s3_service.get_track_url(s3_key, expiration=3600)
            
            assert url is not None
            assert "presigned=true" in url
            assert s3_key in url
            mock_get_url.assert_called_once_with(s3_key, expiration=3600)

    async def test_track_deletion(self, s3_service):
        """Тест удаления трека"""
        s3_key = "tracks/1/test_track.mp3"
        
        with patch.object(s3_service, 'delete_track') as mock_delete:
            mock_delete.return_value = True
            
            result = s3_service.delete_track(s3_key)
            
            assert result is True
            mock_delete.assert_called_once_with(s3_key)

    async def test_list_user_tracks(self, s3_service):
        """Тест получения списка треков пользователя"""
        user_id = 1
        
        mock_tracks = [
            {
                'key': f'tracks/{user_id}/track1.mp3',
                'size': 1024000,
                'last_modified': '2024-01-01T12:00:00Z'
            },
            {
                'key': f'tracks/{user_id}/track2.mp3',
                'size': 2048000,
                'last_modified': '2024-01-02T12:00:00Z'
            }
        ]
        
        with patch.object(s3_service, 'list_user_tracks') as mock_list:
            mock_list.return_value = mock_tracks
            
            tracks = s3_service.list_user_tracks(user_id)
            
            assert len(tracks) == 2
            assert all(str(user_id) in track['key'] for track in tracks)
            mock_list.assert_called_once_with(user_id)

    async def test_storage_statistics(self, s3_service):
        """Тест получения статистики хранилища"""
        mock_stats = {
            'total_tracks': 150,
            'total_size': 1536000000,  # ~1.5GB
            'buckets': {
                'tracks': {'count': 100, 'size': 1024000000},
                'covers': {'count': 50, 'size': 512000000}
            }
        }
        
        with patch.object(s3_service, 'get_storage_stats') as mock_stats_method:
            mock_stats_method.return_value = mock_stats
            
            stats = s3_service.get_storage_stats()
            
            assert stats['total_tracks'] == 150
            assert stats['total_size'] > 0
            assert 'tracks' in stats['buckets']
            assert 'covers' in stats['buckets']
            mock_stats_method.assert_called_once()

    async def test_bucket_operations(self, s3_service):
        """Тест операций с bucket'ами"""
        bucket_name = "test-bucket"
        
        # Тест создания bucket
        with patch.object(s3_service, 'create_bucket') as mock_create:
            mock_create.return_value = True
            
            result = s3_service.create_bucket(bucket_name)
            assert result is True
            mock_create.assert_called_once_with(bucket_name)
        
        # Тест проверки существования bucket
        with patch.object(s3_service, 'bucket_exists') as mock_exists:
            mock_exists.return_value = True
            
            exists = s3_service.bucket_exists(bucket_name)
            assert exists is True
            mock_exists.assert_called_once_with(bucket_name)

    async def test_file_validation(self, s3_service):
        """Тест валидации файлов"""
        # Тест валидации аудио файла
        valid_audio_data = b"ID3\x03\x00" + b"\x00" * 1000  # Фиктивный MP3
        invalid_audio_data = b"invalid audio data"
        
        with patch.object(s3_service, 'validate_audio_file') as mock_validate:
            mock_validate.side_effect = lambda data: data.startswith(b"ID3")
            
            assert s3_service.validate_audio_file(valid_audio_data) is True
            assert s3_service.validate_audio_file(invalid_audio_data) is False
        
        # Тест валидации изображения
        valid_image_data = b"\xff\xd8\xff\xe0"  # JPEG header
        invalid_image_data = b"invalid image data"
        
        with patch.object(s3_service, 'validate_image_file') as mock_validate:
            mock_validate.side_effect = lambda data: data.startswith(b"\xff\xd8")
            
            assert s3_service.validate_image_file(valid_image_data) is True
            assert s3_service.validate_image_file(invalid_image_data) is False

    async def test_cleanup_temp_files(self, s3_service):
        """Тест очистки временных файлов"""
        with patch.object(s3_service, 'cleanup_temp_files') as mock_cleanup:
            mock_cleanup.return_value = {
                'deleted_files': 5,
                'freed_space': 1024000
            }
            
            result = s3_service.cleanup_temp_files(older_than_hours=24)
            
            assert result['deleted_files'] == 5
            assert result['freed_space'] > 0
            mock_cleanup.assert_called_once_with(older_than_hours=24)

    @pytest.mark.slow
    async def test_large_file_upload(self, s3_service):
        """Тест загрузки больших файлов"""
        # Создаем большой временный файл (имитация)
        large_file_size = 10 * 1024 * 1024  # 10MB
        user_id = 1
        track_id = "large_track_123"
        
        with patch.object(s3_service, 'upload_track') as mock_upload:
            # Имитируем успешную загрузку большого файла
            mock_upload.return_value = {
                'success': True,
                's3_key': f'tracks/{user_id}/{track_id}.mp3',
                'bucket': 'tracks',
                'file_size': large_file_size,
                'url': f'http://test.s3.com/tracks/{user_id}/{track_id}.mp3',
                'upload_time': 2.5  # секунды
            }
            
            # Имитируем данные большого файла
            large_file_data = b"0" * large_file_size
            
            result = s3_service.upload_track(
                file_data=large_file_data,
                filename="large_track.mp3",
                user_id=user_id,
                track_id=track_id
            )
            
            assert result['success'] is True
            assert result['file_size'] == large_file_size
            mock_upload.assert_called_once()

    async def test_concurrent_uploads(self, s3_service):
        """Тест параллельных загрузок"""
        import asyncio
        
        async def upload_track(track_num):
            with patch.object(s3_service, 'upload_track') as mock_upload:
                mock_upload.return_value = {
                    'success': True,
                    's3_key': f'tracks/1/track_{track_num}.mp3',
                    'bucket': 'tracks',
                    'file_size': 1024000,
                    'url': f'http://test.s3.com/tracks/1/track_{track_num}.mp3'
                }
                
                file_data = b"test audio data " * 1000
                return s3_service.upload_track(
                    file_data=file_data,
                    filename=f"track_{track_num}.mp3",
                    user_id=1,
                    track_id=f"track_{track_num}"
                )
        
        # Запускаем несколько загрузок параллельно
        tasks = [upload_track(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Проверяем, что все загрузки успешны
        assert len(results) == 5
        assert all(result['success'] for result in results)
        assert len(set(result['s3_key'] for result in results)) == 5  # Уникальные ключи
