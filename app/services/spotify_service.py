"""
Сервис для работы со Spotify API
"""
import requests
import base64
from typing import Optional, Dict, Any, List
from app.core.config import settings


class SpotifyService:
    """Сервис для интеграции со Spotify API"""
    
    def __init__(self):
        self.client_id = getattr(settings, 'SPOTIFY_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'SPOTIFY_CLIENT_SECRET', None)
        self.access_token = None
        self.base_url = "https://api.spotify.com/v1"
    
    async def get_access_token(self) -> Optional[str]:
        """Получение токена доступа для Spotify API"""
        if not self.client_id or not self.client_secret:
            return None
        
        # Кодируем client_id и client_secret в base64
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("ascii")
        auth_base64 = base64.b64encode(auth_bytes).decode("ascii")
        
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials"
        }
        
        try:
            response = requests.post(
                "https://accounts.spotify.com/api/token",
                headers=headers,
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                return self.access_token
            else:
                print(f"Ошибка получения токена Spotify: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"Ошибка при запросе к Spotify API: {e}")
            return None
    
    async def search_track(self, query: str, artist: str = None) -> List[Dict[str, Any]]:
        """
        Поиск трека в Spotify
        
        Args:
            query: Название трека
            artist: Исполнитель (опционально)
        
        Returns:
            Список найденных треков
        """
        if not self.access_token:
            await self.get_access_token()
        
        if not self.access_token:
            return []
        
        # Формируем поисковый запрос
        search_query = f"track:{query}"
        if artist:
            search_query += f" artist:{artist}"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        params = {
            "q": search_query,
            "type": "track",
            "limit": 10
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                tracks = data.get("tracks", {}).get("items", [])
                
                # Форматируем результаты
                formatted_tracks = []
                for track in tracks:
                    formatted_track = {
                        "spotify_id": track["id"],
                        "name": track["name"],
                        "artist": track["artists"][0]["name"] if track["artists"] else "",
                        "album": track["album"]["name"],
                        "duration_ms": track["duration_ms"],
                        "preview_url": track["preview_url"],
                        "external_url": track["external_urls"]["spotify"],
                        "popularity": track["popularity"],
                        "explicit": track["explicit"],
                        "release_date": track["album"]["release_date"],
                        "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None
                    }
                    formatted_tracks.append(formatted_track)
                
                return formatted_tracks
            else:
                print(f"Ошибка поиска в Spotify: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            print(f"Ошибка при поиске в Spotify: {e}")
            return []
    
    async def get_track_by_id(self, spotify_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о треке по Spotify ID"""
        if not self.access_token:
            await self.get_access_token()
        
        if not self.access_token:
            return None
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/tracks/{spotify_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                track = response.json()
                return {
                    "spotify_id": track["id"],
                    "name": track["name"],
                    "artist": track["artists"][0]["name"] if track["artists"] else "",
                    "album": track["album"]["name"],
                    "duration_ms": track["duration_ms"],
                    "preview_url": track["preview_url"],
                    "external_url": track["external_urls"]["spotify"],
                    "popularity": track["popularity"],
                    "explicit": track["explicit"],
                    "release_date": track["album"]["release_date"],
                    "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None
                }
            else:
                return None
                
        except requests.RequestException as e:
            print(f"Ошибка при получении трека из Spotify: {e}")
            return None
    
    async def get_audio_features(self, spotify_id: str) -> Optional[Dict[str, Any]]:
        """Получение аудио-характеристик трека"""
        if not self.access_token:
            await self.get_access_token()
        
        if not self.access_token:
            return None
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/audio-features/{spotify_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                features = response.json()
                return {
                    "tempo": features.get("tempo"),
                    "energy": features.get("energy"),
                    "valence": features.get("valence"),
                    "danceability": features.get("danceability"),
                    "acousticness": features.get("acousticness"),
                    "instrumentalness": features.get("instrumentalness"),
                    "liveness": features.get("liveness"),
                    "speechiness": features.get("speechiness")
                }
            else:
                return None
                
        except requests.RequestException as e:
            print(f"Ошибка при получении аудио-характеристик: {e}")
            return None


# Singleton instance
spotify_service = SpotifyService()
