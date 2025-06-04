from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    role = Column(String(50), default="listener", nullable=False)  
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    
    playlists = relationship("Playlist", back_populates="user")
    listening_history = relationship("ListeningHistory", back_populates="user")
    user_preferences = relationship("UserPreference", back_populates="user")
    artist_profile = relationship("Artist", back_populates="user", uselist=False) 

class Artist(Base):
    __tablename__ = "artists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True, index=True) 
    name = Column(String(255), nullable=False, index=True)
    bio = Column(Text)
    country = Column(String(100))
    image_url = Column(String(500))
    spotify_id = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    
    user = relationship("User", back_populates="artist_profile") 
    albums = relationship("Album", back_populates="artist")
    tracks = relationship("Track", back_populates="artist")

class Album(Base):
    __tablename__ = "albums"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False)
    release_date = Column(DateTime)
    cover_image_url = Column(String(500))
    spotify_id = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    
    artist = relationship("Artist", back_populates="albums")
    tracks = relationship("Track", back_populates="album")

class Genre(Base):
    __tablename__ = "genres"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    
    tracks = relationship("Track", back_populates="genre")

class Track(Base):
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"), nullable=False)
    album_id = Column(Integer, ForeignKey("albums.id"))
    genre_id = Column(Integer, ForeignKey("genres.id"))
    duration_ms = Column(Integer)  
    file_path = Column(String(500))  
    file_url = Column(String(500))   
    spotify_id = Column(String(100), unique=True)
    preview_url = Column(String(500))  
    explicit = Column(Boolean, default=False)
    popularity = Column(Integer, default=0)  
    tempo = Column(Float)  
    energy = Column(Float)  
    valence = Column(Float)  
    danceability = Column(Float)  
    created_at = Column(DateTime, default=datetime.utcnow)
    
    
    artist = relationship("Artist", back_populates="tracks")
    album = relationship("Album", back_populates="tracks")
    genre = relationship("Genre", back_populates="tracks")
    listening_history = relationship("ListeningHistory", back_populates="track")
    playlist_tracks = relationship("PlaylistTrack", back_populates="track")

class Playlist(Base):
    __tablename__ = "playlists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    cover_image_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    
    user = relationship("User", back_populates="playlists")
    tracks = relationship("PlaylistTrack", back_populates="playlist")

class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    position = Column(Integer, nullable=False)  
    added_at = Column(DateTime, default=datetime.utcnow)
    
    
    playlist = relationship("Playlist", back_populates="tracks")
    track = relationship("Track", back_populates="playlist_tracks")

class ListeningHistory(Base):
    """Модель для отслеживания истории прослушивания - для аналитики в ClickHouse"""
    __tablename__ = "listening_history"
    
    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    played_at = Column(DateTime, default=datetime.utcnow, index=True)
    play_duration_ms = Column(Integer)  
    completion_percentage = Column(Float)  
    source = Column(String(50))  
    device_type = Column(String(50))  
    
    
    user = relationship("User", back_populates="listening_history")
    track = relationship("Track", back_populates="listening_history")

class UserPreference(Base):
    """Предпочтения пользователя для рекомендательной системы"""
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    genre_id = Column(Integer, ForeignKey("genres.id"))
    artist_id = Column(Integer, ForeignKey("artists.id"))
    preference_score = Column(Float)  
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    
    user = relationship("User", back_populates="user_preferences")
