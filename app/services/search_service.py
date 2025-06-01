from typing import List, Optional, Dict, Any
from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_

from app.db.models import Track, Artist, Album, Genre
from app.schemas.track import TrackWithDetails, TrackSearchQuery, TrackSearchResponse
from app.core.config import settings


class SearchService:
    """Сервис для полнотекстового поиска с использованием Elasticsearch"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # Настройка подключения к Elasticsearch
        es_config = {
            'hosts': [f"{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"]
        }
        
        if settings.ELASTICSEARCH_USERNAME and settings.ELASTICSEARCH_PASSWORD:
            es_config['basic_auth'] = (
                settings.ELASTICSEARCH_USERNAME, 
                settings.ELASTICSEARCH_PASSWORD
            )
        
        # self.es = AsyncElasticsearch(**es_config)
        # Пока используем заглушку, потом подключим Elasticsearch
        self.es = None
    
    async def index_track(self, track: Track, artist_name: str = None, album_title: str = None, genre_name: str = None):
        """Индексация трека в Elasticsearch"""
        if not self.es:
            return  # Заглушка
        
        doc = {
            "id": track.id,
            "title": track.title,
            "artist_id": track.artist_id,
            "artist_name": artist_name or "",
            "album_id": track.album_id,
            "album_title": album_title or "",
            "genre_id": track.genre_id,
            "genre_name": genre_name or "",
            "duration_ms": track.duration_ms,
            "popularity": track.popularity,
            "explicit": track.explicit,
            "tempo": track.tempo,
            "energy": track.energy,
            "valence": track.valence,
            "danceability": track.danceability,
            "created_at": track.created_at.isoformat() if track.created_at else None,
        }
        
        try:
            await self.es.index(
                index="tracks",
                id=track.id,
                document=doc
            )
        except Exception as e:
            print(f"Error indexing track {track.id}: {e}")
    
    async def search_tracks_elasticsearch(self, search_query: TrackSearchQuery) -> TrackSearchResponse:
        """Поиск треков через Elasticsearch"""
        if not self.es:
            # Fallback к поиску через PostgreSQL
            return await self.search_tracks_fallback(search_query)
        
        # Построение запроса для Elasticsearch
        query = {
            "bool": {
                "must": [],
                "filter": []
            }
        }
        
        # Основной текстовый поиск
        if search_query.query:
            query["bool"]["must"].append({
                "multi_match": {
                    "query": search_query.query,
                    "fields": [
                        "title^3",      # Больший вес для названия трека
                        "artist_name^2", # Средний вес для исполнителя
                        "album_title",   # Обычный вес для альбома
                        "genre_name"     # Обычный вес для жанра
                    ],
                    "fuzziness": "AUTO",  # Автоматическая нечеткость для опечаток
                    "operator": "and"
                }
            })
        
        # Фильтры
        if search_query.artist:
            query["bool"]["filter"].append({
                "match": {
                    "artist_name": search_query.artist
                }
            })
        
        if search_query.album:
            query["bool"]["filter"].append({
                "match": {
                    "album_title": search_query.album
                }
            })
        
        if search_query.genre:
            query["bool"]["filter"].append({
                "match": {
                    "genre_name": search_query.genre
                }
            })
        
        if search_query.duration_from or search_query.duration_to:
            range_filter = {"range": {"duration_ms": {}}}
            if search_query.duration_from:
                range_filter["range"]["duration_ms"]["gte"] = search_query.duration_from
            if search_query.duration_to:
                range_filter["range"]["duration_ms"]["lte"] = search_query.duration_to
            query["bool"]["filter"].append(range_filter)
        
        # Выполнение поиска
        try:
            response = await self.es.search(
                index="tracks",
                query=query,
                from_=search_query.offset,
                size=search_query.limit,
                sort=[
                    {"_score": {"order": "desc"}},  # Сортировка по релевантности
                    {"popularity": {"order": "desc"}}  # Затем по популярности
                ]
            )
            
            # Получение полной информации о треках из PostgreSQL
            track_ids = [hit["_source"]["id"] for hit in response["hits"]["hits"]]
            tracks = await self._get_tracks_with_details(track_ids)
            
            return TrackSearchResponse(
                tracks=tracks,
                total=response["hits"]["total"]["value"],
                limit=search_query.limit,
                offset=search_query.offset
            )
            
        except Exception as e:
            print(f"Elasticsearch search error: {e}")
            # Fallback к поиску через PostgreSQL
            return await self.search_tracks_fallback(search_query)
    
    async def search_tracks_fallback(self, search_query: TrackSearchQuery) -> TrackSearchResponse:
        """Fallback поиск через PostgreSQL"""
        # Базовый запрос с джойнами
        base_query = (
            select(
                Track,
                Artist.name.label("artist_name"),
                Artist.image_url.label("artist_image_url"),
                Album.title.label("album_title"),
                Album.cover_image_url.label("album_cover_url"),
                Genre.name.label("genre_name")
            )
            .outerjoin(Artist, Track.artist_id == Artist.id)
            .outerjoin(Album, Track.album_id == Album.id)
            .outerjoin(Genre, Track.genre_id == Genre.id)
        )
        
        # Добавляем условия поиска
        conditions = []
        
        # Текстовый поиск
        if search_query.query:
            search_term = f"%{search_query.query}%"
            conditions.append(
                or_(
                    Track.title.ilike(search_term),
                    Artist.name.ilike(search_term),
                    Album.title.ilike(search_term),
                    Genre.name.ilike(search_term)
                )
            )
        
        # Фильтры
        if search_query.artist:
            conditions.append(Artist.name.ilike(f"%{search_query.artist}%"))
        
        if search_query.album:
            conditions.append(Album.title.ilike(f"%{search_query.album}%"))
        
        if search_query.genre:
            conditions.append(Genre.name.ilike(f"%{search_query.genre}%"))
        
        if search_query.duration_from:
            conditions.append(Track.duration_ms >= search_query.duration_from)
        
        if search_query.duration_to:
            conditions.append(Track.duration_ms <= search_query.duration_to)
        
        # Применяем условия
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        # Подсчет общего количества
        from sqlalchemy import func
        count_query = select(func.count()).select_from(
            base_query.subquery()
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Основной запрос с пагинацией и сортировкой
        query = (
            base_query
            .order_by(Track.popularity.desc())  # Сортировка по популярности
            .offset(search_query.offset)
            .limit(search_query.limit)
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        # Формируем результат
        tracks = []
        for row in rows:
            track = row[0]
            track_with_details = TrackWithDetails(
                **track.__dict__,
                artist_name=row.artist_name,
                artist_image_url=row.artist_image_url,
                album_title=row.album_title,
                album_cover_url=row.album_cover_url,
                genre_name=row.genre_name
            )
            tracks.append(track_with_details)
        
        return TrackSearchResponse(
            tracks=tracks,
            total=total,
            limit=search_query.limit,
            offset=search_query.offset
        )
    
    async def _get_tracks_with_details(self, track_ids: List[int]) -> List[TrackWithDetails]:
        """Получение треков с деталями по списку ID"""
        if not track_ids:
            return []
        
        query = (
            select(
                Track,
                Artist.name.label("artist_name"),
                Artist.image_url.label("artist_image_url"),
                Album.title.label("album_title"),
                Album.cover_image_url.label("album_cover_url"),
                Genre.name.label("genre_name")
            )
            .outerjoin(Artist, Track.artist_id == Artist.id)
            .outerjoin(Album, Track.album_id == Album.id)
            .outerjoin(Genre, Track.genre_id == Genre.id)
            .where(Track.id.in_(track_ids))
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        # Создаем словарь для сохранения порядка
        track_dict = {}
        for row in rows:
            track = row[0]
            track_with_details = TrackWithDetails(
                **track.__dict__,
                artist_name=row.artist_name,
                artist_image_url=row.artist_image_url,
                album_title=row.album_title,
                album_cover_url=row.album_cover_url,
                genre_name=row.genre_name
            )
            track_dict[track.id] = track_with_details
        
        # Возвращаем в том же порядке, что и track_ids
        return [track_dict[track_id] for track_id in track_ids if track_id in track_dict]
    
    async def suggest_tracks(self, query: str, limit: int = 5) -> List[str]:
        """Автодополнение для поиска треков"""
        if not self.es:
            # Fallback автодополнение через PostgreSQL
            return await self._suggest_tracks_fallback(query, limit)
        
        try:
            response = await self.es.search(
                index="tracks",
                query={
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "artist_name", "album_title"],
                        "type": "phrase_prefix"
                    }
                },
                size=limit,
                _source=["title", "artist_name"]
            )
            
            suggestions = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                suggestion = f"{source['title']} - {source['artist_name']}"
                suggestions.append(suggestion)
            
            return suggestions
            
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return await self._suggest_tracks_fallback(query, limit)
    
    async def _suggest_tracks_fallback(self, query: str, limit: int) -> List[str]:
        """Fallback автодополнение через PostgreSQL"""
        search_term = f"{query}%"
        
        suggestion_query = (
            select(Track.title, Artist.name.label("artist_name"))
            .join(Artist, Track.artist_id == Artist.id)
            .where(
                or_(
                    Track.title.ilike(search_term),
                    Artist.name.ilike(search_term)
                )
            )
            .limit(limit)
        )
        
        result = await self.db.execute(suggestion_query)
        rows = result.all()
        
        return [f"{row.title} - {row.artist_name}" for row in rows]
    
    async def create_elasticsearch_mapping(self):
        """Создание маппинга для Elasticsearch"""
        if not self.es:
            return
        
        mapping = {
            "properties": {
                "id": {"type": "integer"},
                "title": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "suggest": {
                            "type": "completion",
                            "analyzer": "simple"
                        }
                    }
                },
                "artist_name": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                        "keyword": {"type": "keyword"},
                        "suggest": {
                            "type": "completion",
                            "analyzer": "simple"
                        }
                    }
                },
                "album_title": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {"keyword": {"type": "keyword"}}
                },
                "genre_name": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {"keyword": {"type": "keyword"}}
                },
                "duration_ms": {"type": "integer"},
                "popularity": {"type": "integer"},
                "explicit": {"type": "boolean"},
                "tempo": {"type": "float"},
                "energy": {"type": "float"},
                "valence": {"type": "float"},
                "danceability": {"type": "float"},
                "created_at": {"type": "date"}
            }
        }
        
        try:
            await self.es.indices.create(
                index="tracks",
                mappings=mapping,
                ignore=400  # Игнорируем ошибку если индекс уже существует
            )
        except Exception as e:
            print(f"Error creating Elasticsearch mapping: {e}")
    
    async def reindex_all_tracks(self):
        """Переиндексация всех треков"""
        if not self.es:
            return
        
        # Получаем все треки с деталями
        query = (
            select(
                Track,
                Artist.name.label("artist_name"),
                Album.title.label("album_title"),
                Genre.name.label("genre_name")
            )
            .outerjoin(Artist, Track.artist_id == Artist.id)
            .outerjoin(Album, Track.album_id == Album.id)
            .outerjoin(Genre, Track.genre_id == Genre.id)
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        for row in rows:
            track = row[0]
            await self.index_track(
                track,
                artist_name=row.artist_name,
                album_title=row.album_title,
                genre_name=row.genre_name
            )
    
    async def search_tracks(self, query: str, genre: str = None, year: int = None, 
                           artist: str = None, album: str = None, limit: int = 10) -> List[TrackWithDetails]:
        """Поиск треков с простыми параметрами (для совместимости с API endpoint)"""
        from app.schemas.track import TrackSearchQuery
        
        # Создаем объект поискового запроса
        search_query = TrackSearchQuery(
            query=query,
            genre=genre,
            artist=artist,
            album=album,
            limit=limit,
            offset=0
        )
        
        # Используем основной метод поиска
        if self.es:
            result = await self.search_tracks_elasticsearch(search_query)
        else:
            result = await self.search_tracks_fallback(search_query)
        
        return result.tracks
