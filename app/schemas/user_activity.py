from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ListeningEvent(BaseModel):
    """Событие прослушивания для отправки в аналитику"""
    user_id: int = Field(..., description="ID пользователя")
    track_id: int = Field(..., description="ID трека")
    play_duration_ms: int = Field(..., description="Длительность прослушивания в мс")
    completion_percentage: float = Field(..., ge=0.0, le=100.0, description="Процент прослушивания")
    source: str = Field(..., description="Источник: search, playlist, recommendation, etc.")
    device_type: str = Field("web", description="Тип устройства")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class PlaylistInteraction(BaseModel):
    """Взаимодействие с плейлистом"""
    user_id: int
    playlist_id: int
    action: str = Field(..., description="add_track, remove_track, create, delete, play")
    track_id: Optional[int] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

class SearchEvent(BaseModel):
    """Событие поиска"""
    user_id: Optional[int] = None
    query: str = Field(..., description="Поисковый запрос")
    results_count: int = Field(..., description="Количество найденных результатов")
    clicked_track_id: Optional[int] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

# Схемы для аналитических отчетов
class TrackAnalytics(BaseModel):
    """Аналитика трека"""
    track_id: int
    track_title: str
    artist_name: str
    total_plays: int = 0
    unique_listeners: int = 0
    average_completion_rate: float = 0.0
    total_listening_time_ms: int = 0
    plays_by_hour: Dict[int, int] = {}  # час -> количество воспроизведений
    plays_by_day: Dict[str, int] = {}   # дата -> количество воспроизведений

class UserAnalytics(BaseModel):
    """Аналитика пользователя"""
    user_id: int
    total_listening_time_ms: int = 0
    total_tracks_played: int = 0
    favorite_genres: list[str] = []
    favorite_artists: list[str] = []
    listening_patterns: Dict[str, Any] = {}  # паттерны прослушивания
    activity_by_hour: Dict[int, int] = {}

class PlatformAnalytics(BaseModel):
    """Общая аналитика платформы"""
    total_users: int = 0
    active_users_today: int = 0
    active_users_week: int = 0
    active_users_month: int = 0
    total_plays_today: int = 0
    total_tracks: int = 0
    total_artists: int = 0
    top_tracks: list[TrackAnalytics] = []
    top_genres: Dict[str, int] = {}

class AnalyticsQuery(BaseModel):
    """Запрос для получения аналитики"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[int] = None
    track_id: Optional[int] = None
    artist_id: Optional[int] = None
    genre: Optional[str] = None
    limit: int = Field(50, ge=1, le=1000)
    offset: int = Field(0, ge=0) 