"""
S3 Service для работы с MinIO/S3 хранилищем
Используется для загрузки, скачивания и управления треками
"""

import boto3
import os
import hashlib
import mimetypes
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime, timedelta
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        """Инициализация S3 клиента для MinIO"""
        self.endpoint_url = os.getenv('S3_ENDPOINT_URL', 'http://localhost:9002')
        self.access_key = os.getenv('S3_ACCESS_KEY', 'minioadmin')
        self.secret_key = os.getenv('S3_SECRET_KEY', 'minioadmin123')
        self.region = os.getenv('S3_REGION', 'us-east-1')
        
        # Конфигурация для работы с MinIO
        config = Config(
            region_name=self.region,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            s3={'addressing_style': 'path'}
        )
        
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=config
        )
        
        # Bucket names
        self.tracks_bucket = 'tracks'
        self.covers_bucket = 'covers'
        self.playlists_bucket = 'playlists'
        self.temp_bucket = 'temp'
        
        self._ensure_buckets_exist()
    
    def _ensure_buckets_exist(self):
        """Создает buckets если они не существуют"""
        buckets = [self.tracks_bucket, self.covers_bucket, self.playlists_bucket, self.temp_bucket]
        
        try:
            existing_buckets = [bucket['Name'] for bucket in self.client.list_buckets()['Buckets']]
            
            for bucket_name in buckets:
                if bucket_name not in existing_buckets:
                    logger.info(f"Creating bucket: {bucket_name}")
                    self.client.create_bucket(Bucket=bucket_name)
                    
        except Exception as e:
            logger.error(f"Error ensuring buckets exist: {e}")
    
    def upload_track(self, file_content: BinaryIO, filename: str, 
                    user_id: int, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Загружает трек в S3
        
        Args:
            file_content: Содержимое файла
            filename: Имя файла
            user_id: ID пользователя
            metadata: Дополнительные метаданные
            
        Returns:
            Dict с информацией о загруженном файле
        """
        try:
            # Генерируем уникальный ключ для файла
            timestamp = datetime.now().strftime('%Y/%m/%d')
            file_hash = hashlib.md5(file_content.read()).hexdigest()[:8]
            file_content.seek(0)  # Возвращаемся в начало файла
            
            file_extension = os.path.splitext(filename)[1]
            s3_key = f"users/{user_id}/{timestamp}/{file_hash}_{filename}"
            
            # Определяем MIME тип
            content_type = mimetypes.guess_type(filename)[0] or 'audio/mpeg'
            
            # Подготавливаем метаданные
            upload_metadata = {
                'user-id': str(user_id),
                'original-filename': filename,
                'upload-timestamp': datetime.now().isoformat(),
                'file-hash': file_hash
            }
            
            if metadata:
                upload_metadata.update({f'custom-{k}': str(v) for k, v in metadata.items()})
            
            # Загружаем файл
            self.client.upload_fileobj(
                file_content,
                self.tracks_bucket,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': upload_metadata,
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            # Получаем размер файла
            response = self.client.head_object(Bucket=self.tracks_bucket, Key=s3_key)
            file_size = response['ContentLength']
            
            logger.info(f"Track uploaded successfully: {s3_key}")
            
            return {
                'success': True,
                's3_key': s3_key,
                'bucket': self.tracks_bucket,
                'file_size': file_size,
                'content_type': content_type,
                'metadata': upload_metadata,
                'url': self.get_track_url(s3_key)
            }
            
        except Exception as e:
            logger.error(f"Error uploading track: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def upload_cover(self, file_content: BinaryIO, filename: str, 
                    track_id: Optional[int] = None, album_id: Optional[int] = None) -> Dict[str, Any]:
        """Загружает обложку в S3"""
        try:
            timestamp = datetime.now().strftime('%Y/%m/%d')
            file_hash = hashlib.md5(file_content.read()).hexdigest()[:8]
            file_content.seek(0)
            
            # Определяем путь в зависимости от типа
            if track_id:
                s3_key = f"tracks/{track_id}/{timestamp}/{file_hash}_{filename}"
            elif album_id:
                s3_key = f"albums/{album_id}/{timestamp}/{file_hash}_{filename}"
            else:
                s3_key = f"misc/{timestamp}/{file_hash}_{filename}"
            
            content_type = mimetypes.guess_type(filename)[0] or 'image/jpeg'
            
            metadata = {
                'upload-timestamp': datetime.now().isoformat(),
                'file-hash': file_hash
            }
            
            if track_id:
                metadata['track-id'] = str(track_id)
            if album_id:
                metadata['album-id'] = str(album_id)
            
            self.client.upload_fileobj(
                file_content,
                self.covers_bucket,
                s3_key,
                ExtraArgs={
                    'ContentType': content_type,
                    'Metadata': metadata,
                    'ACL': 'public-read'  # Обложки доступны публично
                }
            )
            
            return {
                'success': True,
                's3_key': s3_key,
                'bucket': self.covers_bucket,
                'url': self.get_cover_url(s3_key)
            }
            
        except Exception as e:
            logger.error(f"Error uploading cover: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_track_url(self, s3_key: str, expires_in: int = 3600) -> str:
        """Генерирует presigned URL для трека"""
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.tracks_bucket, 'Key': s3_key},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"Error generating track URL: {e}")
            return ""
    
    def get_cover_url(self, s3_key: str) -> str:
        """Генерирует публичный URL для обложки"""
        return f"{self.endpoint_url}/{self.covers_bucket}/{s3_key}"
    
    def delete_track(self, s3_key: str) -> bool:
        """Удаляет трек из S3"""
        try:
            self.client.delete_object(Bucket=self.tracks_bucket, Key=s3_key)
            logger.info(f"Track deleted: {s3_key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting track: {e}")
            return False
    
    def get_track_metadata(self, s3_key: str) -> Optional[Dict]:
        """Получает метаданные трека"""
        try:
            response = self.client.head_object(Bucket=self.tracks_bucket, Key=s3_key)
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType'),
                'metadata': response.get('Metadata', {})
            }
        except Exception as e:
            logger.error(f"Error getting track metadata: {e}")
            return None
    
    def list_user_tracks(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Возвращает список треков пользователя"""
        try:
            prefix = f"users/{user_id}/"
            response = self.client.list_objects_v2(
                Bucket=self.tracks_bucket,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            tracks = []
            for obj in response.get('Contents', []):
                # Получаем метаданные для каждого файла
                metadata = self.get_track_metadata(obj['Key'])
                if metadata:
                    tracks.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'url': self.get_track_url(obj['Key']),
                        'metadata': metadata.get('metadata', {})
                    })
            
            return tracks
            
        except Exception as e:
            logger.error(f"Error listing user tracks: {e}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Возвращает статистику использования хранилища"""
        try:
            stats = {
                'buckets': {},
                'total_size': 0,
                'total_objects': 0
            }
            
            buckets = [self.tracks_bucket, self.covers_bucket, self.playlists_bucket, self.temp_bucket]
            
            for bucket_name in buckets:
                try:
                    response = self.client.list_objects_v2(Bucket=bucket_name)
                    objects = response.get('Contents', [])
                    
                    bucket_size = sum(obj['Size'] for obj in objects)
                    bucket_count = len(objects)
                    
                    stats['buckets'][bucket_name] = {
                        'objects': bucket_count,
                        'size_bytes': bucket_size,
                        'size_mb': round(bucket_size / (1024 * 1024), 2)
                    }
                    
                    stats['total_size'] += bucket_size
                    stats['total_objects'] += bucket_count
                    
                except Exception as e:
                    logger.error(f"Error getting stats for bucket {bucket_name}: {e}")
                    stats['buckets'][bucket_name] = {'error': str(e)}
            
            stats['total_size_mb'] = round(stats['total_size'] / (1024 * 1024), 2)
            stats['total_size_gb'] = round(stats['total_size'] / (1024 * 1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {'error': str(e)}
    
    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """Очищает временные файлы старше указанного времени"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            
            response = self.client.list_objects_v2(Bucket=self.temp_bucket)
            objects_to_delete = []
            
            for obj in response.get('Contents', []):
                if obj['LastModified'].replace(tzinfo=None) < cutoff_time:
                    objects_to_delete.append({'Key': obj['Key']})
            
            if objects_to_delete:
                self.client.delete_objects(
                    Bucket=self.temp_bucket,
                    Delete={'Objects': objects_to_delete}
                )
                
                logger.info(f"Cleaned up {len(objects_to_delete)} temp files")
                return len(objects_to_delete)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
            return 0

# Singleton instance
s3_service = S3Service()
