"""
ClickHouse сервис для аналитики
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from clickhouse_driver import Client
from clickhouse_driver.errors import Error as ClickHouseError

from app.core.config import settings
from app.schemas.user_activity import ListeningEvent


class ClickHouseService:
    """Сервис для работы с ClickHouse"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Инициализация клиента ClickHouse"""
        try:
            self.client = Client(
                host=settings.CLICKHOUSE_HOST,
                port=settings.CLICKHOUSE_PORT,
                user=settings.CLICKHOUSE_USER,
                password=settings.CLICKHOUSE_PASSWORD if settings.CLICKHOUSE_PASSWORD else None,
                database=settings.CLICKHOUSE_DATABASE,
                settings={'use_numpy': True}
            )
            # Проверяем соединение
            self.client.execute('SELECT 1')
            print(f"✅ ClickHouse connection established to {settings.CLICKHOUSE_HOST}:{settings.CLICKHOUSE_PORT}")
        except Exception as e:
            print(f"❌ Failed to connect to ClickHouse: {e}")
            self.client = None
    
    async def create_tables(self):
        """Создание таблиц в ClickHouse для аналитики"""
        if not self.client:
            print("ClickHouse client not available")
            return False
        
        try:
            # Таблица для событий прослушивания
            listening_events_table = """
            CREATE TABLE IF NOT EXISTS listening_events (
                event_id String,
                user_id UInt32,
                track_id UInt32,
                artist_id UInt32,
                album_id UInt32,
                genre_id UInt32,
                played_at DateTime,
                play_duration_ms UInt32,
                completion_percentage Float32,
                source String,
                device_type String,
                session_id String,
                ip_address String,
                user_agent String,
                country String,
                city String,
                date Date MATERIALIZED toDate(played_at),
                hour UInt8 MATERIALIZED toHour(played_at)
            ) ENGINE = MergeTree()
            ORDER BY (date, user_id, track_id, played_at)
            PARTITION BY toYYYYMM(played_at)
            """
            
            # Таблица для поисковых событий
            search_events_table = """
            CREATE TABLE IF NOT EXISTS search_events (
                event_id String,
                user_id UInt32,
                query String,
                results_count UInt32,
                clicked_track_id UInt32,
                search_timestamp DateTime,
                session_id String,
                ip_address String,
                date Date MATERIALIZED toDate(search_timestamp)
            ) ENGINE = MergeTree()
            ORDER BY (date, user_id, search_timestamp)
            PARTITION BY toYYYYMM(search_timestamp)
            """
            
            # Таблица для событий плейлистов
            playlist_events_table = """
            CREATE TABLE IF NOT EXISTS playlist_events (
                event_id String,
                user_id UInt32,
                playlist_id UInt32,
                track_id UInt32,
                action String,
                timestamp DateTime,
                session_id String,
                date Date MATERIALIZED toDate(timestamp)
            ) ENGINE = MergeTree()
            ORDER BY (date, user_id, playlist_id, timestamp)
            PARTITION BY toYYYYMM(timestamp)
            """
            
            # Агрегированная таблица для статистики треков по дням
            daily_track_stats_table = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS daily_track_stats
            TO daily_track_stats_table
            AS SELECT
                track_id,
                date,
                count() as plays_count,
                uniq(user_id) as unique_listeners,
                avg(completion_percentage) as avg_completion,
                sum(play_duration_ms) as total_listening_time
            FROM listening_events
            GROUP BY track_id, date
            """
            
            # Таблица назначения для материализованного представления
            daily_track_stats_table_target = """
            CREATE TABLE IF NOT EXISTS daily_track_stats_table (
                track_id UInt32,
                date Date,
                plays_count UInt32,
                unique_listeners UInt32,
                avg_completion Float32,
                total_listening_time UInt64
            ) ENGINE = SummingMergeTree()
            ORDER BY (track_id, date)
            """
            
            # Выполняем создание таблиц
            await asyncio.to_thread(self.client.execute, listening_events_table)
            await asyncio.to_thread(self.client.execute, search_events_table)
            await asyncio.to_thread(self.client.execute, playlist_events_table)
            await asyncio.to_thread(self.client.execute, daily_track_stats_table_target)
            await asyncio.to_thread(self.client.execute, daily_track_stats_table)
            
            print("✅ ClickHouse tables created successfully")
            return True
            
        except ClickHouseError as e:
            print(f"❌ Error creating ClickHouse tables: {e}")
            return False
    
    async def insert_listening_event(self, event_data: Dict[str, Any]) -> bool:
        """Вставка события прослушивания в ClickHouse"""
        if not self.client:
            return False
        
        try:
            query = """
            INSERT INTO listening_events (
                event_id, user_id, track_id, artist_id, album_id, genre_id,
                played_at, play_duration_ms, completion_percentage,
                source, device_type, session_id, ip_address, user_agent,
                country, city
            ) VALUES
            """
            
            await asyncio.to_thread(
                self.client.execute,
                query,
                [event_data]
            )
            return True
            
        except ClickHouseError as e:
            print(f"Error inserting listening event: {e}")
            return False
    
    async def insert_search_event(self, event_data: Dict[str, Any]) -> bool:
        """Вставка поискового события в ClickHouse"""
        if not self.client:
            return False
        
        try:
            query = """
            INSERT INTO search_events (
                event_id, user_id, query, results_count, clicked_track_id,
                search_timestamp, session_id, ip_address
            ) VALUES
            """
            
            await asyncio.to_thread(
                self.client.execute,
                query,
                [event_data]
            )
            return True
            
        except ClickHouseError as e:
            print(f"Error inserting search event: {e}")
            return False
    
    async def get_track_analytics(self, track_id: int, days: int = 30) -> Dict[str, Any]:
        """Получение аналитики трека из ClickHouse"""
        if not self.client:
            return {}
        
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Основная статистика
            stats_query = """
            SELECT
                count() as total_plays,
                uniq(user_id) as unique_listeners,
                avg(completion_percentage) as avg_completion,
                sum(play_duration_ms) as total_listening_time
            FROM listening_events
            WHERE track_id = %(track_id)s
            AND date BETWEEN %(start_date)s AND %(end_date)s
            """
            
            # Статистика по часам
            hourly_query = """
            SELECT
                hour,
                count() as plays
            FROM listening_events
            WHERE track_id = %(track_id)s
            AND date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY hour
            ORDER BY hour
            """
            
            # Статистика по дням
            daily_query = """
            SELECT
                date,
                count() as plays,
                uniq(user_id) as unique_listeners
            FROM listening_events
            WHERE track_id = %(track_id)s
            AND date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY date
            ORDER BY date
            """
            
            # Выполняем запросы
            stats_result = await asyncio.to_thread(
                self.client.execute,
                stats_query,
                {'track_id': track_id, 'start_date': start_date, 'end_date': end_date}
            )
            
            hourly_result = await asyncio.to_thread(
                self.client.execute,
                hourly_query,
                {'track_id': track_id, 'start_date': start_date, 'end_date': end_date}
            )
            
            daily_result = await asyncio.to_thread(
                self.client.execute,
                daily_query,
                {'track_id': track_id, 'start_date': start_date, 'end_date': end_date}
            )
            
            # Формируем результат
            stats = stats_result[0] if stats_result else (0, 0, 0.0, 0)
            hourly_data = {hour: plays for hour, plays in hourly_result}
            daily_data = {str(date): {'plays': plays, 'unique_listeners': listeners} 
                         for date, plays, listeners in daily_result}
            
            return {
                'total_plays': stats[0],
                'unique_listeners': stats[1],
                'avg_completion': float(stats[2]),
                'total_listening_time': stats[3],
                'plays_by_hour': hourly_data,
                'plays_by_day': daily_data
            }
            
        except ClickHouseError as e:
            print(f"Error getting track analytics: {e}")
            return {}
    
    async def get_user_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """Получение аналитики пользователя из ClickHouse"""
        if not self.client:
            return {}
        
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Основная статистика пользователя
            user_stats_query = """
            SELECT
                count() as total_plays,
                uniq(track_id) as unique_tracks,
                sum(play_duration_ms) as total_listening_time,
                avg(completion_percentage) as avg_completion
            FROM listening_events
            WHERE user_id = %(user_id)s
            AND date BETWEEN %(start_date)s AND %(end_date)s
            """
            
            # Активность по часам
            hourly_activity_query = """
            SELECT
                hour,
                count() as plays
            FROM listening_events
            WHERE user_id = %(user_id)s
            AND date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY hour
            ORDER BY hour
            """
            
            # Топ исполнители
            top_artists_query = """
            SELECT
                artist_id,
                count() as plays
            FROM listening_events
            WHERE user_id = %(user_id)s
            AND date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY artist_id
            ORDER BY plays DESC
            LIMIT 10
            """
            
            # Выполняем запросы
            stats_result = await asyncio.to_thread(
                self.client.execute,
                user_stats_query,
                {'user_id': user_id, 'start_date': start_date, 'end_date': end_date}
            )
            
            hourly_result = await asyncio.to_thread(
                self.client.execute,
                hourly_activity_query,
                {'user_id': user_id, 'start_date': start_date, 'end_date': end_date}
            )
            
            artists_result = await asyncio.to_thread(
                self.client.execute,
                top_artists_query,
                {'user_id': user_id, 'start_date': start_date, 'end_date': end_date}
            )
            
            # Формируем результат
            stats = stats_result[0] if stats_result else (0, 0, 0, 0.0)
            hourly_data = {hour: plays for hour, plays in hourly_result}
            top_artists = [{'artist_id': artist_id, 'plays': plays} 
                          for artist_id, plays in artists_result]
            
            return {
                'total_plays': stats[0],
                'unique_tracks': stats[1],
                'total_listening_time': stats[2],
                'avg_completion': float(stats[3]),
                'activity_by_hour': hourly_data,
                'top_artists': top_artists
            }
            
        except ClickHouseError as e:
            print(f"Error getting user analytics: {e}")
            return {}
    
    async def get_top_tracks(self, limit: int = 50, days: int = 30) -> List[Dict[str, Any]]:
        """Получение топ треков из ClickHouse"""
        if not self.client:
            return []
        
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            query = """
            SELECT
                track_id,
                count() as total_plays,
                uniq(user_id) as unique_listeners,
                avg(completion_percentage) as avg_completion,
                sum(play_duration_ms) as total_listening_time
            FROM listening_events
            WHERE date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY track_id
            ORDER BY total_plays DESC
            LIMIT %(limit)s
            """
            
            result = await asyncio.to_thread(
                self.client.execute,
                query,
                {'start_date': start_date, 'end_date': end_date, 'limit': limit}
            )
            
            return [
                {
                    'track_id': track_id,
                    'total_plays': plays,
                    'unique_listeners': listeners,
                    'avg_completion': float(completion),
                    'total_listening_time': listening_time
                }
                for track_id, plays, listeners, completion, listening_time in result
            ]
            
        except ClickHouseError as e:
            print(f"Error getting top tracks: {e}")
            return []
    
    async def get_platform_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Получение общей аналитики платформы из ClickHouse"""
        if not self.client:
            return {}
        
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Общая статистика
            platform_stats_query = """
            SELECT
                count() as total_plays,
                uniq(user_id) as active_users,
                uniq(track_id) as played_tracks,
                sum(play_duration_ms) as total_listening_time
            FROM listening_events
            WHERE date BETWEEN %(start_date)s AND %(end_date)s
            """
            
            # Активность по дням
            daily_activity_query = """
            SELECT
                date,
                count() as plays,
                uniq(user_id) as active_users
            FROM listening_events
            WHERE date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY date
            ORDER BY date
            """
            
            # Выполняем запросы
            stats_result = await asyncio.to_thread(
                self.client.execute,
                platform_stats_query,
                {'start_date': start_date, 'end_date': end_date}
            )
            
            daily_result = await asyncio.to_thread(
                self.client.execute,
                daily_activity_query,
                {'start_date': start_date, 'end_date': end_date}
            )
            
            # Формируем результат
            stats = stats_result[0] if stats_result else (0, 0, 0, 0)
            daily_data = {str(date): {'plays': plays, 'active_users': users} 
                         for date, plays, users in daily_result}
            
            return {
                'total_plays': stats[0],
                'active_users': stats[1],
                'played_tracks': stats[2],
                'total_listening_time': stats[3],
                'daily_activity': daily_data
            }
            
        except ClickHouseError as e:
            print(f"Error getting platform analytics: {e}")
            return {}
    
    async def get_trending_tracks(self, limit: int = 10, days: int = 7) -> List[Dict]:
        """
        Получить трендовые треки за указанный период
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            query = """
            SELECT
                track_id,
                count() as play_count,
                uniq(user_id) as unique_listeners,
                avg(play_duration_ms) as avg_duration
            FROM listening_events
            WHERE date BETWEEN %(start_date)s AND %(end_date)s
            GROUP BY track_id
            ORDER BY play_count DESC
            LIMIT %(limit)s
            """
            
            result = await asyncio.to_thread(
                self.client.execute,
                query,
                {
                    'start_date': start_date.date(),
                    'end_date': end_date.date(),
                    'limit': limit
                }
            )
            
            return [
                {
                    'track_id': track_id,
                    'play_count': play_count,
                    'unique_listeners': unique_listeners,
                    'avg_duration': avg_duration
                }
                for track_id, play_count, unique_listeners, avg_duration in result
            ]
            
        except ClickHouseError as e:
            print(f"Error getting trending tracks: {e}")
            return []
