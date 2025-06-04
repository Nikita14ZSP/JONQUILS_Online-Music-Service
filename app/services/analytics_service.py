"""
Сервис аналитики с интеграцией ClickHouse
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, text

from app.schemas.user_activity import (
    ListeningEvent, 
    TrackAnalytics, 
    UserAnalytics, 
    PlatformAnalytics,
    AnalyticsQuery
)
from app.db.models import Track, Artist, User, ListeningHistory, Album, Genre
from app.core.config import settings
from app.services.clickhouse_service import clickhouse_service


class AnalyticsService:
    """Сервис для работы с аналитикой с интеграцией ClickHouse"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.clickhouse = clickhouse_service
    
    async def record_listening_event(
        self, 
        user_id: int, 
        track_id: int, 
        listened_at: datetime = None,
        duration_listened: int = None,
        source: str = "unknown",
        device_type: str = "web",
        session_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        completion_percentage: float = 0.0
    ) -> bool:
        """Записывает событие прослушивания в PostgreSQL и ClickHouse"""
        try:
            if listened_at is None:
                listened_at = datetime.utcnow()
            
            if session_id is None:
                session_id = str(uuid.uuid4())
            
           
            track_query = (
                select(Track, Artist.id.label("artist_id"), Album.id.label("album_id"), Genre.id.label("genre_id"))
                .outerjoin(Artist, Track.artist_id == Artist.id)
                .outerjoin(Album, Track.album_id == Album.id)
                .outerjoin(Genre, Track.genre_id == Genre.id)
                .where(Track.id == track_id)
            )
            track_result = await self.db.execute(track_query)
            track_data = track_result.first()
            
            if not track_data:
                print(f"Track {track_id} not found")
                return False
            
            track, artist_id, album_id, genre_id = track_data
            
            
            db_event = ListeningHistory(
                user_id=user_id,
                track_id=track_id,
                played_at=listened_at,
                play_duration_ms=duration_listened or 0,
                completion_percentage=completion_percentage,
                source=source,
                device_type=device_type
            )
            self.db.add(db_event)
            await self.db.commit()
            
            
            clickhouse_event = {
                'event_id': str(uuid.uuid4()),
                'user_id': user_id,
                'track_id': track_id,
                'artist_id': artist_id or 0,
                'album_id': album_id or 0,
                'genre_id': genre_id or 0,
                'played_at': listened_at,
                'play_duration_ms': duration_listened or 0,
                'completion_percentage': completion_percentage,
                'source': source,
                'device_type': device_type,
                'session_id': session_id,
                'ip_address': ip_address or '',
                'user_agent': user_agent or '',
                'country': '',  
                'city': ''
            }
            
            
            await self.clickhouse.insert_listening_event(clickhouse_event)
            
            return True
            
        except Exception as e:
            print(f"Error recording listening event: {e}")
            return False
    
    async def record_search_event(
        self,
        query: str,
        results_count: int,
        user_id: int = None,
        clicked_track_id: int = None,
        session_id: str = None,
        ip_address: str = None
    ) -> bool:
        """Записывает поисковое событие в ClickHouse"""
        try:
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            search_event = {
                'event_id': str(uuid.uuid4()),
                'user_id': user_id or 0,
                'query': query,
                'results_count': results_count,
                'clicked_track_id': clicked_track_id or 0,
                'search_timestamp': datetime.utcnow(),
                'session_id': session_id,
                'ip_address': ip_address or ''
            }
            
            await self.clickhouse.insert_search_event(search_event)
            return True
            
        except Exception as e:
            print(f"Error recording search event: {e}")
            return False
    
    async def get_track_analytics(self, track_id: int, days: int = 30) -> Optional[TrackAnalytics]:
        """Получение аналитики по треку из ClickHouse"""
        try:
           
            track_query = (
                select(Track, Artist.name.label("artist_name"))
                .join(Artist, Track.artist_id == Artist.id)
                .where(Track.id == track_id)
            )
            track_result = await self.db.execute(track_query)
            track_row = track_result.first()
            
            if not track_row:
                return None
            
            track, artist_name = track_row
            
          
            analytics_data = await self.clickhouse.get_track_analytics(track_id, days)
            
            if not analytics_data:
                return None
            
            return TrackAnalytics(
                track_id=track_id,
                track_title=track.title,
                artist_name=artist_name,
                total_plays=analytics_data.get('total_plays', 0),
                unique_listeners=analytics_data.get('unique_listeners', 0),
                average_completion_rate=analytics_data.get('avg_completion', 0.0),
                total_listening_time_ms=analytics_data.get('total_listening_time', 0),
                plays_by_hour=analytics_data.get('plays_by_hour', {}),
                plays_by_day=analytics_data.get('plays_by_day', {})
            )
            
        except Exception as e:
            print(f"Error getting track analytics: {e}")
            return None
    
    async def get_user_analytics(self, user_id: int, period: str = "week") -> Optional[UserAnalytics]:
        """Получение аналитики по пользователю из ClickHouse"""
        try:
           
            days_map = {
                "day": 1,
                "week": 7,
                "month": 30,
                "year": 365,
                "all": 365 * 10 
            }
            days = days_map.get(period, 7)

            
            analytics_data = await self.clickhouse.get_user_analytics(user_id, days)
            
            if not analytics_data:
                return None
            
            
            top_artists_data = analytics_data.get('top_artists', [])
            favorite_artists = []
            
            for artist_data in top_artists_data[:5]:  
                artist_query = select(Artist.name).where(Artist.id == artist_data['artist_id'])
                artist_result = await self.db.execute(artist_query)
                artist_name = artist_result.scalar()
                if artist_name:
                    favorite_artists.append(artist_name)
            
            return UserAnalytics(
                user_id=user_id,
                total_listening_time_ms=analytics_data.get('total_listening_time', 0),
                total_tracks_played=analytics_data.get('unique_tracks', 0),
                favorite_genres=[],  
                favorite_artists=favorite_artists,
                listening_patterns={},
                activity_by_hour=analytics_data.get('activity_by_hour', {})
            )
            
        except Exception as e:
            print(f"Error getting user analytics: {e}")
            return None
    
    async def get_top_tracks(self, limit: int = 50, days: int = 30) -> List[TrackAnalytics]:
        """Получение топ треков из ClickHouse"""
        try:
            
            top_tracks_data = await self.clickhouse.get_top_tracks(limit, days)
            
            track_analytics = []
            
            for track_data in top_tracks_data:
               
                track_query = (
                    select(Track, Artist.name.label("artist_name"))
                    .join(Artist, Track.artist_id == Artist.id)
                    .where(Track.id == track_data['track_id'])
                )
                track_result = await self.db.execute(track_query)
                track_row = track_result.first()
                
                if track_row:
                    track, artist_name = track_row
                    track_analytics.append(TrackAnalytics(
                        track_id=track_data['track_id'],
                        track_title=track.title,
                        artist_name=artist_name,
                        total_plays=track_data['total_plays'],
                        unique_listeners=track_data['unique_listeners'],
                        average_completion_rate=track_data['avg_completion'],
                        total_listening_time_ms=track_data['total_listening_time'],
                        plays_by_hour={},
                        plays_by_day={}
                    ))
            
            return track_analytics
            
        except Exception as e:
            print(f"Error getting top tracks: {e}")
            return []
    
    async def get_platform_analytics(self, days: int = 30) -> PlatformAnalytics:
        """Получение общей аналитики платформы из ClickHouse"""
        try:
            
            total_users_query = select(func.count(User.id))
            total_users_result = await self.db.execute(total_users_query)
            total_users = total_users_result.scalar() or 0
            
            total_tracks_query = select(func.count(Track.id))
            total_tracks_result = await self.db.execute(total_tracks_query)
            total_tracks = total_tracks_result.scalar() or 0
            
            total_artists_query = select(func.count(Artist.id))
            total_artists_result = await self.db.execute(total_artists_query)
            total_artists = total_artists_result.scalar() or 0
            
            
            platform_data = await self.clickhouse.get_platform_analytics(days)
            
           
            top_tracks = await self.get_top_tracks(10, days)
            
            return PlatformAnalytics(
                total_users=total_users,
                active_users_today=0,  
                active_users_week=0,
                active_users_month=platform_data.get('active_users', 0),
                total_plays_today=0,
                total_tracks=total_tracks,
                total_artists=total_artists,
                top_tracks=top_tracks,
                top_genres={}
            )
            
        except Exception as e:
            print(f"Error getting platform analytics: {e}")
            return PlatformAnalytics()
    
    async def get_user_stats(self, user_id: int, period: str = "week") -> dict:
        """Получить статистику пользователя за период"""
        days_map = {
            "day": 1,
            "week": 7,
            "month": 30,
            "year": 365
        }
        
        days = days_map.get(period, 7)
        user_analytics = await self.get_user_analytics(user_id, period)
        
        if user_analytics:
            return {
                "total_listening_time_ms": user_analytics.total_listening_time_ms,
                "total_tracks_played": user_analytics.total_tracks_played,
                "favorite_artists": user_analytics.favorite_artists,
                "activity_by_hour": user_analytics.activity_by_hour,
                "period": period
            }
        
        return {
            "total_listening_time_ms": 0,
            "total_tracks_played": 0,
            "favorite_artists": [],
            "activity_by_hour": {},
            "period": period
        }
    
    async def get_user_listening_history(
        self,
        user_id: int,
        limit: int = 50,
        from_date: datetime = None,
        to_date: datetime = None
    ) -> List[dict]:
        """Получить историю прослушиваний пользователя из PostgreSQL"""
        try:
            query = (
                select(
                    ListeningHistory,
                    Track.title.label("track_title"),
                    Artist.name.label("artist_name")
                )
                .join(Track, ListeningHistory.track_id == Track.id)
                .join(Artist, Track.artist_id == Artist.id)
                .where(ListeningHistory.user_id == user_id)
            )
            
            if from_date:
                query = query.where(ListeningHistory.played_at >= from_date)
            if to_date:
                query = query.where(ListeningHistory.played_at <= to_date)
            
            query = query.order_by(desc(ListeningHistory.played_at)).limit(limit)
            
            result = await self.db.execute(query)
            rows = result.all()
            
            history = []
            for row in rows:
                listening_event, track_title, artist_name = row
                history.append({
                    "track_id": listening_event.track_id,
                    "track_title": track_title,
                    "artist_name": artist_name,
                    "played_at": listening_event.played_at,
                    "play_duration_ms": listening_event.play_duration_ms,
                    "completion_percentage": listening_event.completion_percentage,
                    "source": listening_event.source,
                    "device_type": listening_event.device_type
                })
            
            return history
            
        except Exception as e:
            print(f"Error getting user listening history: {e}")
            return []
