"""
ClickHouse сервис для аналитики
"""
import asyncio
import uuid
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
            # Отладочная информация
            print(f"🔍 Debug ClickHouse settings:")
            print(f"   HOST: {settings.CLICKHOUSE_HOST}")
            print(f"   PORT: {settings.CLICKHOUSE_PORT}")
            print(f"   USER: {settings.CLICKHOUSE_USER}")
            print(f"   PASSWORD: {settings.CLICKHOUSE_PASSWORD}")
            print(f"   DATABASE: {settings.CLICKHOUSE_DATABASE}")
            
            # Используем настройки подключения к ClickHouse в Docker
            self.client = Client(
                host=settings.CLICKHOUSE_HOST,
                port=settings.CLICKHOUSE_PORT,
                user=settings.CLICKHOUSE_USER,
                password=settings.CLICKHOUSE_PASSWORD,
                database=settings.CLICKHOUSE_DATABASE
            )
            # Временно отключаем проверку соединения при инициализации
            # self.client.execute('SELECT 1')
            print(f"✅ ClickHouse client configured for {settings.CLICKHOUSE_HOST}:{settings.CLICKHOUSE_PORT} as {settings.CLICKHOUSE_USER}")
        except Exception as e:
            print(f"❌ Failed to configure ClickHouse client: {e}")
            self.client = None
    
    async def test_connection(self):
        """Тестируем подключение к ClickHouse"""
        if not self.client:
            raise Exception("ClickHouse client not initialized")
        
        try:
            result = self.client.execute('SELECT 1')
            return result[0][0] == 1
        except Exception as e:
            raise Exception(f"Failed to test ClickHouse connection: {e}")
    
    async def create_tables(self):
        """Создание таблиц ClickHouse для аналитики"""
        if not self.client:
            print("⚠️ ClickHouse client not available, skipping table creation")
            return
        
        try:
            # Проверяем подключение
            await self.test_connection()
            print("✅ ClickHouse connection successful")
            
            # Создаем базу данных если не существует
            self.client.execute("CREATE DATABASE IF NOT EXISTS jonquils_analytics")
            
            # Переключаемся на базу данных
            self.client.execute("USE jonquils_analytics")
            
            # Определяем DDL команды для создания таблиц
            tables = [
                """
                CREATE TABLE IF NOT EXISTS api_requests_log (
                    timestamp DateTime DEFAULT now(),
                    request_id String,
                    user_id UInt64 DEFAULT 0,
                    artist_id UInt64 DEFAULT 0,
                    method String,
                    endpoint String,
                    status_code UInt16,
                    response_time_ms UInt32,
                    user_agent String DEFAULT '',
                    ip_address String DEFAULT '',
                    request_size UInt32 DEFAULT 0,
                    response_size UInt32 DEFAULT 0,
                    error_message String DEFAULT '',
                    session_id String DEFAULT '',
                    date Date DEFAULT toDate(timestamp)
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(date)
                ORDER BY (timestamp, endpoint, user_id)
                """,
                """
                CREATE TABLE IF NOT EXISTS track_analytics (
                    timestamp DateTime DEFAULT now(),
                    track_id UInt64,
                    artist_id UInt64,
                    user_id UInt64 DEFAULT 0,
                    action String,
                    duration_played_ms UInt32 DEFAULT 0,
                    track_position_ms UInt32 DEFAULT 0,
                    platform String DEFAULT 'web',
                    device_type String DEFAULT 'unknown',
                    location String DEFAULT '',
                    session_id String DEFAULT '',
                    date Date DEFAULT toDate(timestamp)
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(date)
                ORDER BY (timestamp, track_id, user_id)
                """,
                """
                CREATE TABLE IF NOT EXISTS search_analytics (
                    timestamp DateTime DEFAULT now(),
                    user_id UInt64 DEFAULT 0,
                    query String,
                    results_count UInt32,
                    search_type String,
                    clicked_result_id UInt64 DEFAULT 0,
                    clicked_result_type String DEFAULT '',
                    session_id String DEFAULT '',
                    date Date DEFAULT toDate(timestamp)
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(date)
                ORDER BY (timestamp, query, user_id)
                """,
                """
                CREATE TABLE IF NOT EXISTS user_analytics (
                    timestamp DateTime DEFAULT now(),
                    user_id UInt64,
                    action String,
                    session_duration_minutes UInt32 DEFAULT 0,
                    pages_visited UInt32 DEFAULT 1,
                    tracks_played UInt32 DEFAULT 0,
                    searches_made UInt32 DEFAULT 0,
                    session_id String DEFAULT '',
                    date Date DEFAULT toDate(timestamp)
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(date)
                ORDER BY (timestamp, user_id)
                """,
                """
                CREATE TABLE IF NOT EXISTS artist_analytics (
                    timestamp DateTime DEFAULT now(),
                    artist_id UInt64,
                    action String,
                    target_id UInt64 DEFAULT 0,
                    metadata_key String DEFAULT '',
                    metadata_value String DEFAULT '',
                    date Date DEFAULT toDate(timestamp)
                ) ENGINE = MergeTree()
                PARTITION BY toYYYYMM(date)
                ORDER BY (timestamp, artist_id)
                """
            ]
            
            # Создаем каждую таблицу
            for i, table_ddl in enumerate(tables, 1):
                try:
                    self.client.execute(table_ddl)
                    print(f"✅ Table {i}/5 created successfully")
                except Exception as e:
                    print(f"⚠️ Warning: Failed to create table {i}: {e}")
                    continue
            
            print("✅ All ClickHouse tables processed successfully")
                
        except Exception as e:
            print(f"❌ Failed to create ClickHouse tables: {e}")
            # Не поднимаем исключение, чтобы приложение могло работать без ClickHouse
    
    # Методы для логирования API запросов
    async def log_api_request(self, 
                            method: str, 
                            endpoint: str, 
                            status_code: int,
                            response_time_ms: int,
                            user_id: Optional[int] = None,
                            artist_id: Optional[int] = None,
                            user_agent: str = "",
                            ip_address: str = "",
                            request_size: Optional[int] = None,
                            response_size: Optional[int] = None,
                            error_message: Optional[str] = None,
                            session_id: Optional[str] = None):
        """Логирование API запроса"""
        if not self.client:
            return
        
        try:
            request_id = str(uuid.uuid4())
            
            query = """
            INSERT INTO api_requests_log 
            (request_id, user_id, artist_id, method, endpoint, status_code, response_time_ms, 
             user_agent, ip_address, request_size, response_size, error_message, session_id)
            VALUES
            """
            
            data = [(
                request_id, 
                user_id or 0, 
                artist_id or 0, 
                method, 
                endpoint, 
                status_code, 
                response_time_ms, 
                user_agent or '', 
                ip_address or '', 
                request_size or 0, 
                response_size or 0, 
                error_message or '', 
                session_id or ''
            )]
            
            self.client.execute(query, data)
        except Exception as e:
            print(f"Failed to log API request: {e}")
    

    async def log_track_action(self,
                              track_id: int,
                              artist_id: int,
                              action: str,
                              user_id: Optional[int] = None,
                              duration_played_ms: Optional[int] = None,
                              track_position_ms: Optional[int] = None,
                              platform: str = "web",
                              device_type: str = "unknown",
                              location: Optional[str] = None,
                              session_id: Optional[str] = None):
        """Логирование действий с треками"""
        if not self.client:
            return
        
        try:
            query = """
            INSERT INTO track_analytics 
            (track_id, artist_id, user_id, action, duration_played_ms, track_position_ms,
             platform, device_type, location, session_id)
            VALUES
            """
            
            data = [(
                track_id, 
                artist_id, 
                user_id or 0, 
                action, 
                duration_played_ms or 0,
                track_position_ms or 0, 
                platform, 
                device_type, 
                location or '', 
                session_id or ''
            )]
            
            self.client.execute(query, data)
        except Exception as e:
            print(f"Failed to log track action: {e}")
    
    
    async def log_search_action(self,
                               query: str,
                               results_count: int,
                               search_type: str,
                               user_id: Optional[int] = None,
                               clicked_result_id: Optional[int] = None,
                               clicked_result_type: Optional[str] = None,
                               session_id: Optional[str] = None):
        """Логирование поисковых запросов"""
        if not self.client:
            return
        
        try:
            sql_query = """
            INSERT INTO search_analytics 
            (user_id, query, results_count, search_type, clicked_result_id, 
             clicked_result_type, session_id)
            VALUES
            """
            
            data = [(
                user_id or 0, 
                query, 
                results_count, 
                search_type, 
                clicked_result_id or 0, 
                clicked_result_type or '', 
                session_id or ''
            )]
            
            self.client.execute(sql_query, data)
        except Exception as e:
            print(f"Failed to log search action: {e}")
    
    
    async def log_user_action(self,
                             user_id: int,
                             action: str,
                             session_duration_minutes: Optional[int] = None,
                             pages_visited: int = 1,
                             tracks_played: int = 0,
                             searches_made: int = 0,
                             session_id: Optional[str] = None):
        """Логирование действий пользователей"""
        if not self.client:
            return
        
        try:
            query = """
            INSERT INTO user_analytics 
            (user_id, action, session_duration_minutes, pages_visited, 
             tracks_played, searches_made, session_id)
            VALUES
            """
            
            data = [(
                user_id, 
                action, 
                session_duration_minutes or 0, 
                pages_visited,
                tracks_played, 
                searches_made, 
                session_id or ''
            )]
            
            self.client.execute(query, data)
        except Exception as e:
            print(f"Failed to log user action: {e}")
    
    # Методы для аналитики артистов
    async def log_artist_action(self,
                               artist_id: int,
                               action: str,
                               target_id: Optional[int] = None,
                               metadata: Optional[Dict[str, str]] = None):
        """Логирование действий артистов"""
        if not self.client:
            return
        
        try:
            # Обрабатываем metadata как ключ-значение пары
            metadata_key = ''
            metadata_value = ''
            if metadata:
                # Берем первую пару ключ-значение из словаря
                first_key = next(iter(metadata.keys()), '')
                metadata_key = first_key
                metadata_value = metadata.get(first_key, '')
            
            query = """
            INSERT INTO artist_analytics 
            (artist_id, action, target_id, metadata_key, metadata_value)
            VALUES
            """
            
            data = [(
                artist_id, action, target_id or 0, metadata_key, metadata_value
            )]
            
            self.client.execute(query, data)
        except Exception as e:
            print(f"Failed to log artist action: {e}")
    
    # Методы для получения аналитики
    async def get_api_stats(self, days: int = 7) -> Dict[str, Any]:
        """Получение статистики API за последние дни"""
        if not self.client:
            return {}
        
        try:
            query = """
            SELECT 
                endpoint,
                count() as requests,
                avg(response_time_ms) as avg_response_time,
                countIf(status_code >= 400) as errors
            FROM api_requests_log 
            WHERE date >= today() - {days}
            GROUP BY endpoint
            ORDER BY requests DESC
            """.format(days=days)
            
            result = self.client.execute(query)
            
            stats = []
            for row in result:
                stats.append({
                    'endpoint': row[0],
                    'requests': row[1],
                    'avg_response_time': round(row[2], 2),
                    'errors': row[3]
                })
            
            return {'endpoints': stats}
        except Exception as e:
            print(f"Failed to get API stats: {e}")
            return {}
    
    async def get_track_stats(self, track_id: int, days: int = 30) -> Dict[str, Any]:
        """Получение статистики трека"""
        if not self.client:
            return {}
        
        try:
            query = """
            SELECT 
                action,
                count() as count,
                uniq(user_id) as unique_users
            FROM track_analytics 
            WHERE track_id = {track_id} AND date >= today() - {days}
            GROUP BY action
            ORDER BY count DESC
            """.format(track_id=track_id, days=days)
            
            result = self.client.execute(query)
            
            stats = {}
            for row in result:
                stats[row[0]] = {
                    'count': row[1],
                    'unique_users': row[2]
                }
            
            return stats
        except Exception as e:
            print(f"Failed to get track stats: {e}")
            return {}
    
    async def get_artist_stats(self, artist_id: int) -> Dict[str, Any]:
        """Получение статистики артиста"""
        if not self.client:
            return {}
        
        try:
           
            tracks_query = """
            SELECT 
                count() as total_plays,
                uniq(user_id) as unique_listeners,
                countIf(action = 'like') as total_likes
            FROM track_analytics 
            WHERE artist_id = {artist_id} AND date >= today() - 30
            """.format(artist_id=artist_id)
            
            tracks_result = self.client.execute(tracks_query)
            
            
            actions_query = """
            SELECT 
                action,
                count() as count
            FROM artist_analytics 
            WHERE artist_id = {artist_id} AND date >= today() - 30
            GROUP BY action
            """.format(artist_id=artist_id)
            
            actions_result = self.client.execute(actions_query)
            
            stats = {
                'tracks': {
                    'total_plays': tracks_result[0][0] if tracks_result else 0,
                    'unique_listeners': tracks_result[0][1] if tracks_result else 0,
                    'total_likes': tracks_result[0][2] if tracks_result else 0
                },
                'actions': {}
            }
            
            for row in actions_result:
                stats['actions'][row[0]] = row[1]
            
            return stats
        except Exception as e:
            print(f"Failed to get artist stats: {e}")
            return {}
    
    async def close(self):
        """Закрываем соединение с ClickHouse"""
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
            self.client = None
    
    async def execute_query(self, query: str, parameters: list = None):
        """Выполняем произвольный запрос"""
        if not self.client:
            raise Exception("ClickHouse client not initialized")
        
        try:
            if parameters:
                return self.client.execute(query, parameters)
            return self.client.execute(query)
        except Exception as e:
            raise Exception(f"Failed to execute query: {e}")
    
    # Методы для получения пользовательской аналитики
    async def get_user_search_history(self, user_id: int, days: int = 30, limit: int = 50):
        """Получаем историю поисков пользователя"""
        if not self.client:
            return []
        
        try:
            query = """
            SELECT 
                timestamp,
                search_query,
                results_count,
                clicked_result_id,
                clicked_result_type
            FROM search_analytics 
            WHERE user_id = %(user_id)s 
                AND timestamp >= subtractDays(now(), %(days)s)
            ORDER BY timestamp DESC
            LIMIT %(limit)s
            """
            
            result = self.client.execute(query, {
                'user_id': user_id,
                'days': days,
                'limit': limit
            })
            
            return [
                {
                    'timestamp': row[0],
                    'search_query': row[1],
                    'results_count': row[2],
                    'clicked_result_id': row[3],
                    'clicked_result_type': row[4]
                }
                for row in result
            ]
        except Exception as e:
            print(f"Error getting user search history: {e}")
            return []
    
    async def get_user_top_tracks(self, user_id: int, days: int = 30, limit: int = 10):
        """Получаем топ треков пользователя по прослушиваниям"""
        if not self.client:
            return []
        
        try:
            query = """
            SELECT 
                track_id,
                count() as play_count,
                sum(play_duration_ms) as total_duration_ms,
                avg(play_duration_ms) as avg_duration_ms
            FROM track_analytics 
            WHERE user_id = %(user_id)s 
                AND timestamp >= subtractDays(now(), %(days)s)
            GROUP BY track_id
            ORDER BY play_count DESC
            LIMIT %(limit)s
            """
            
            result = self.client.execute(query, {
                'user_id': user_id,
                'days': days,
                'limit': limit
            })
            
            return [
                {
                    'track_id': row[0],
                    'play_count': row[1],
                    'total_duration_ms': row[2],
                    'avg_duration_ms': row[3]
                }
                for row in result
            ]
        except Exception as e:
            print(f"Error getting user top tracks: {e}")
            return []
    
    async def get_user_activity_stats(self, user_id: int, days: int = 30):
        """Получаем общую статистику активности пользователя"""
        if not self.client:
            return {}
        
        try:
            # Статистика поиска
            search_query = """
            SELECT 
                count() as total_searches,
                uniq(search_query) as unique_queries,
                countIf(clicked_result_id > 0) as searches_with_clicks
            FROM search_analytics 
            WHERE user_id = %(user_id)s 
                AND timestamp >= subtractDays(now(), %(days)s)
            """
            
            search_result = self.client.execute(search_query, {
                'user_id': user_id,
                'days': days
            })
            
            # Статистика прослушивания
            track_query = """
            SELECT 
                count() as total_plays,
                uniq(track_id) as unique_tracks,
                sum(play_duration_ms) as total_listening_time_ms,
                avg(play_duration_ms) as avg_play_duration_ms
            FROM track_analytics 
            WHERE user_id = %(user_id)s 
                AND timestamp >= subtractDays(now(), %(days)s)
            """
            
            track_result = self.client.execute(track_query, {
                'user_id': user_id,
                'days': days
            })
            
            search_stats = search_result[0] if search_result else (0, 0, 0)
            track_stats = track_result[0] if track_result else (0, 0, 0, 0)
            
            return {
                'search_stats': {
                    'total_searches': search_stats[0],
                    'unique_queries': search_stats[1],
                    'searches_with_clicks': search_stats[2],
                    'click_through_rate': search_stats[2] / max(search_stats[0], 1) * 100
                },
                'listening_stats': {
                    'total_plays': track_stats[0],
                    'unique_tracks': track_stats[1],
                    'total_listening_time_ms': track_stats[2],
                    'avg_play_duration_ms': track_stats[3],
                    'total_listening_hours': track_stats[2] / (1000 * 60 * 60) if track_stats[2] else 0
                }
            }
        except Exception as e:
            print(f"Error getting user activity stats: {e}")
            return {}
    
    async def get_user_activity_timeline(self, user_id: int, days: int = 30):
        """Получаем временную линию активности пользователя"""
        if not self.client:
            return []
        
        try:
            query = """
            SELECT 
                toDate(timestamp) as date,
                count() as activity_count,
                'search' as activity_type
            FROM search_analytics 
            WHERE user_id = %(user_id)s 
                AND timestamp >= subtractDays(now(), %(days)s)
            GROUP BY toDate(timestamp)
            
            UNION ALL
            
            SELECT 
                toDate(timestamp) as date,
                count() as activity_count,
                'listening' as activity_type
            FROM track_analytics 
            WHERE user_id = %(user_id)s 
                AND timestamp >= subtractDays(now(), %(days)s)
            GROUP BY toDate(timestamp)
            
            ORDER BY date DESC
            """
            
            result = self.client.execute(query, {
                'user_id': user_id,
                'days': days
            })
            
            # Группируем по дате
            timeline = {}
            for row in result:
                date_str = row[0].strftime('%Y-%m-%d')
                if date_str not in timeline:
                    timeline[date_str] = {'date': date_str, 'search_count': 0, 'listening_count': 0}
                
                if row[2] == 'search':
                    timeline[date_str]['search_count'] = row[1]
                elif row[2] == 'listening':
                    timeline[date_str]['listening_count'] = row[1]
            
            # Конвертируем в список и сортируем по дате
            timeline_list = list(timeline.values())
            timeline_list.sort(key=lambda x: x['date'], reverse=True)
            
            return timeline_list
        except Exception as e:
            print(f"Error getting user activity timeline: {e}")
            return []

    async def get_user_search_stats(self, user_id: int, period: str = "week") -> Dict[str, Any]:
        """Получить статистику поиска пользователя"""
        if not self.client:
            return {"total_searches": 0, "unique_queries": 0, "avg_results": 0}
        
        try:
            days = self._get_days_for_period(period)
            
            query = """
            SELECT 
                count() as total_searches,
                uniq(query) as unique_queries,
                avg(result_count) as avg_results,
                sum(clicked_result) as clicked_results
            FROM search_analytics 
            WHERE user_id = %(user_id)s 
                AND timestamp >= subtractDays(now(), %(days)s)
            """
            
            result = self.client.execute(query, {
                'user_id': user_id,
                'days': days
            })
            
            if result:
                row = result[0]
                return {
                    "total_searches": row[0],
                    "unique_queries": row[1],
                    "avg_results": round(row[2] or 0, 1),
                    "clicked_results": row[3] or 0
                }
            
            return {"total_searches": 0, "unique_queries": 0, "avg_results": 0, "clicked_results": 0}
        except Exception as e:
            print(f"Error getting user search stats: {e}")
            return {"total_searches": 0, "unique_queries": 0, "avg_results": 0, "clicked_results": 0}

    async def get_user_listening_stats(self, user_id: int, period: str = "week") -> Dict[str, Any]:
        """Получить статистику прослушивания пользователя"""
        if not self.client:
            return {"total_plays": 0, "unique_tracks": 0, "total_duration": 0}
        
        try:
            days = self._get_days_for_period(period)
            
            query = """
            SELECT 
                count() as total_plays,
                uniq(track_id) as unique_tracks,
                sum(duration_ms) as total_duration_ms,
                uniq(artist_id) as unique_artists
            FROM track_analytics 
            WHERE user_id = %(user_id)s 
                AND timestamp >= subtractDays(now(), %(days)s)
            """
            
            result = self.client.execute(query, {
                'user_id': user_id,
                'days': days
            })
            
            if result:
                row = result[0]
                total_duration_ms = row[2] or 0
                total_hours = round(total_duration_ms / (1000 * 60 * 60), 1)
                
                return {
                    "total_plays": row[0],
                    "unique_tracks": row[1],
                    "unique_artists": row[3],
                    "total_duration_hours": total_hours,
                    "total_duration_ms": total_duration_ms
                }
            
            return {"total_plays": 0, "unique_tracks": 0, "unique_artists": 0, "total_duration_hours": 0, "total_duration_ms": 0}
        except Exception as e:
            print(f"Error getting user listening stats: {e}")
            return {"total_plays": 0, "unique_tracks": 0, "unique_artists": 0, "total_duration_hours": 0, "total_duration_ms": 0}

    async def get_user_top_tracks(self, user_id: int, period: str = "week", limit: int = 10) -> List[Dict[str, Any]]:
        """Получить топ треков пользователя"""
        if not self.client:
            return []
        
        try:
            days = self._get_days_for_period(period)
            
            query = """
            SELECT 
                track_id,
                track_name,
                artist_name,
                count() as play_count,
                sum(duration_ms) as total_duration_ms,
                avg(duration_ms) as avg_duration_ms
            FROM track_analytics 
            WHERE user_id = %(user_id)s 
                AND timestamp >= subtractDays(now(), %(days)s)
            GROUP BY track_id, track_name, artist_name
            ORDER BY play_count DESC, total_duration_ms DESC
            LIMIT %(limit)s
            """
            
            result = self.client.execute(query, {
                'user_id': user_id,
                'days': days,
                'limit': limit
            })
            
            top_tracks = []
            for row in result:
                track = {
                    "track_id": row[0],
                    "track_name": row[1],
                    "artist_name": row[2],
                    "play_count": row[3],
                    "total_duration_ms": row[4],
                    "avg_duration_ms": round(row[5], 0) if row[5] else 0,
                    "total_hours": round((row[4] or 0) / (1000 * 60 * 60), 1)
                }
                top_tracks.append(track)
            
            return top_tracks
        except Exception as e:
            print(f"Error getting user top tracks: {e}")
            return []

    async def get_user_recent_searches(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить недавние поиски пользователя"""
        if not self.client:
            return []
        
        try:
            query = """
            SELECT 
                query,
                timestamp,
                result_count,
                clicked_result,
                search_type
            FROM search_analytics 
            WHERE user_id = %(user_id)s 
            ORDER BY timestamp DESC
            LIMIT %(limit)s
            """
            
            result = self.client.execute(query, {
                'user_id': user_id,
                'limit': limit
            })
            
            recent_searches = []
            for row in result:
                search = {
                    "query": row[0],
                    "timestamp": row[1].isoformat(),
                    "result_count": row[2],
                    "clicked_result": bool(row[3]),
                    "search_type": row[4]
                }
                recent_searches.append(search)
            
            return recent_searches
        except Exception as e:
            print(f"Error getting user recent searches: {e}")
            return []


clickhouse_service = ClickHouseService()
