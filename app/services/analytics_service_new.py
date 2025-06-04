from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, text

from app.schemas.user_activity import (
    ListeningEvent, 
    TrackAnalytics, 
    UserAnalytics, 
    PlatformAnalytics,
    AnalyticsQuery
)
from app.db.models import Track, Artist, User, ListeningHistory
from app.core.config import settings


class AnalyticsService:
    """Сервис для работы с аналитикой"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    
    async def record_listening_event(self, event: ListeningEvent) -> bool:
        """Записывает событие прослушивания в PostgreSQL"""
        try:
         
            db_event = ListeningHistory(
                user_id=event.user_id,
                track_id=event.track_id,
                played_at=event.timestamp or datetime.utcnow(),
                play_duration_ms=event.play_duration_ms,
                completion_percentage=event.completion_percentage,
                source=event.source,
                device_type=event.device_type
            )
            self.db.add(db_event)
            await self.db.commit()
            
            return True
        except Exception as e:
            print(f"Error recording listening event: {e}")
            return False
    
    async def get_track_analytics(self, track_id: int, days: int = 30) -> Optional[TrackAnalytics]:
        """Получение аналитики по треку"""
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
            
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
           
            stats_query = select(
                func.count(ListeningHistory.id).label("total_plays"),
                func.count(func.distinct(ListeningHistory.user_id)).label("unique_listeners"),
                func.avg(ListeningHistory.completion_percentage).label("avg_completion"),
                func.sum(ListeningHistory.play_duration_ms).label("total_listening_time")
            ).where(
                and_(
                    ListeningHistory.track_id == track_id,
                    ListeningHistory.played_at >= start_date,
                    ListeningHistory.played_at <= end_date
                )
            )
            
            stats_result = await self.db.execute(stats_query)
            stats = stats_result.first()
            
            
            hourly_query = select(
                func.extract('hour', ListeningHistory.played_at).label("hour"),
                func.count(ListeningHistory.id).label("plays")
            ).where(
                and_(
                    ListeningHistory.track_id == track_id,
                    ListeningHistory.played_at >= start_date,
                    ListeningHistory.played_at <= end_date
                )
            ).group_by(func.extract('hour', ListeningHistory.played_at))
            
            hourly_result = await self.db.execute(hourly_query)
            plays_by_hour = {int(row.hour): row.plays for row in hourly_result}
            
            
            daily_query = select(
                func.date(ListeningHistory.played_at).label("date"),
                func.count(ListeningHistory.id).label("plays")
            ).where(
                and_(
                    ListeningHistory.track_id == track_id,
                    ListeningHistory.played_at >= start_date,
                    ListeningHistory.played_at <= end_date
                )
            ).group_by(func.date(ListeningHistory.played_at))
            
            daily_result = await self.db.execute(daily_query)
            plays_by_day = {str(row.date): row.plays for row in daily_result}
            
            return TrackAnalytics(
                track_id=track_id,
                track_title=track.title,
                artist_name=artist_name,
                total_plays=stats.total_plays or 0,
                unique_listeners=stats.unique_listeners or 0,
                average_completion_rate=float(stats.avg_completion or 0),
                total_listening_time_ms=int(stats.total_listening_time or 0),
                plays_by_hour=plays_by_hour,
                plays_by_day=plays_by_day
            )
            
        except Exception as e:
            print(f"Error getting track analytics: {e}")
            return None
    
    async def get_user_analytics(self, user_id: int, days: int = 30) -> Optional[UserAnalytics]:
        """Получение аналитики по пользователю"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
           
            user_stats_query = select(
                func.sum(ListeningHistory.play_duration_ms).label("total_listening_time"),
                func.count(ListeningHistory.id).label("total_plays"),
                func.count(func.distinct(ListeningHistory.track_id)).label("unique_tracks")
            ).where(
                and_(
                    ListeningHistory.user_id == user_id,
                    ListeningHistory.played_at >= start_date,
                    ListeningHistory.played_at <= end_date
                )
            )
            
            user_stats_result = await self.db.execute(user_stats_query)
            user_stats = user_stats_result.first()
            
         
            hourly_activity_query = select(
                func.extract('hour', ListeningHistory.played_at).label("hour"),
                func.count(ListeningHistory.id).label("plays")
            ).where(
                and_(
                    ListeningHistory.user_id == user_id,
                    ListeningHistory.played_at >= start_date,
                    ListeningHistory.played_at <= end_date
                )
            ).group_by(func.extract('hour', ListeningHistory.played_at))
            
            hourly_result = await self.db.execute(hourly_activity_query)
            activity_by_hour = {int(row.hour): row.plays for row in hourly_result}
            
            
            favorite_genres = []
            favorite_artists = []
            
            return UserAnalytics(
                user_id=user_id,
                total_listening_time_ms=int(user_stats.total_listening_time or 0),
                total_tracks_played=int(user_stats.unique_tracks or 0),
                favorite_genres=favorite_genres,
                favorite_artists=favorite_artists,
                activity_by_hour=activity_by_hour
            )
            
        except Exception as e:
            print(f"Error getting user analytics: {e}")
            return None
    
    async def get_platform_analytics(self, days: int = 30) -> PlatformAnalytics:
        """Получение общей аналитики платформы"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            
            total_users_query = select(func.count(User.id))
            total_users_result = await self.db.execute(total_users_query)
            total_users = total_users_result.scalar() or 0
            
            total_tracks_query = select(func.count(Track.id))
            total_tracks_result = await self.db.execute(total_tracks_query)
            total_tracks = total_tracks_result.scalar() or 0
            
            total_artists_query = select(func.count(Artist.id))
            total_artists_result = await self.db.execute(total_artists_query)
            total_artists = total_artists_result.scalar() or 0
            
           
            today = datetime.utcnow().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            active_today_query = select(func.count(func.distinct(ListeningHistory.user_id))).where(
                func.date(ListeningHistory.played_at) == today
            )
            active_today_result = await self.db.execute(active_today_query)
            active_today = active_today_result.scalar() or 0
            
            active_week_query = select(func.count(func.distinct(ListeningHistory.user_id))).where(
                func.date(ListeningHistory.played_at) >= week_ago
            )
            active_week_result = await self.db.execute(active_week_query)
            active_week = active_week_result.scalar() or 0
            
            active_month_query = select(func.count(func.distinct(ListeningHistory.user_id))).where(
                func.date(ListeningHistory.played_at) >= month_ago
            )
            active_month_result = await self.db.execute(active_month_query)
            active_month = active_month_result.scalar() or 0
            
            plays_today_query = select(func.count(ListeningHistory.id)).where(
                func.date(ListeningHistory.played_at) == today
            )
            plays_today_result = await self.db.execute(plays_today_query)
            plays_today = plays_today_result.scalar() or 0
            
          
            top_tracks_data = await self.get_top_tracks(limit=10, days=days)
            
            return PlatformAnalytics(
                total_users=total_users,
                active_users_today=active_today,
                active_users_week=active_week,
                active_users_month=active_month,
                total_plays_today=plays_today,
                total_tracks=total_tracks,
                total_artists=total_artists,
                top_tracks=top_tracks_data
            )
            
        except Exception as e:
            print(f"Error getting platform analytics: {e}")
            return PlatformAnalytics()
    
    async def get_top_tracks(self, limit: int = 50, days: int = 30) -> List[TrackAnalytics]:
        """Получение топ треков за период"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            top_tracks_query = (
                select(
                    ListeningHistory.track_id,
                    func.count(ListeningHistory.id).label("total_plays"),
                    func.count(func.distinct(ListeningHistory.user_id)).label("unique_listeners"),
                    func.avg(ListeningHistory.completion_percentage).label("avg_completion"),
                    func.sum(ListeningHistory.play_duration_ms).label("total_listening_time")
                )
                .where(
                    and_(
                        ListeningHistory.played_at >= start_date,
                        ListeningHistory.played_at <= end_date
                    )
                )
                .group_by(ListeningHistory.track_id)
                .order_by(desc("total_plays"))
                .limit(limit)
            )
            
            top_tracks_result = await self.db.execute(top_tracks_query)
            
            track_analytics = []
            for row in top_tracks_result:
                
                track_query = (
                    select(Track, Artist.name.label("artist_name"))
                    .join(Artist, Track.artist_id == Artist.id)
                    .where(Track.id == row.track_id)
                )
                track_result = await self.db.execute(track_query)
                track_row = track_result.first()
                
                if track_row:
                    track, artist_name = track_row
                    track_analytics.append(TrackAnalytics(
                        track_id=row.track_id,
                        track_title=track.title,
                        artist_name=artist_name,
                        total_plays=row.total_plays,
                        unique_listeners=row.unique_listeners,
                        average_completion_rate=float(row.avg_completion or 0),
                        total_listening_time_ms=int(row.total_listening_time or 0)
                    ))
            
            return track_analytics
            
        except Exception as e:
            print(f"Error getting top tracks: {e}")
            return []
