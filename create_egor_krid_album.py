#!/usr/bin/env python3
"""
Скрипт для создания тестовых данных: альбом Егора Крида "Меньше чем три"
"""

import asyncio
import httpx
from datetime import datetime
import json

BASE_URL = "http://localhost:8000/api/v1"

# Данные для альбома Егора Крида "Меньше чем три"
egor_krid_data = {
    "artist": {
        "name": "Егор Крид", 
        "bio": "Российский рэпер, певец и автор песен. Один из самых популярных исполнителей русскоязычной сцены.",
        "country": "Россия",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Egor_Kreed_2019.jpg/800px-Egor_Kreed_2019.jpg"
    },
    "album": {
        "title": "Меньше чем три",
        "release_date": "2020-12-25T00:00:00Z",
        "cover_image_url": "https://i.scdn.co/image/ab67616d0000b273f8b3d3f5c6b1c8a0b7e0c5f1"
    },
    "genre": {
        "name": "Хип-хоп",
        "description": "Современный русский хип-хоп и поп-рэп"
    },
    "tracks": [
        {
            "title": "Меньше чем три",
            "duration_ms": 189000,  # 3:09
            "popularity": 95,
            "tempo": 128.0,
            "energy": 0.7,
            "valence": 0.6,
            "danceability": 0.8,
            "explicit": False
        },
        {
            "title": "Голос",
            "duration_ms": 178000,  # 2:58
            "popularity": 88,
            "tempo": 120.0,
            "energy": 0.65,
            "valence": 0.55,
            "danceability": 0.75,
            "explicit": False
        },
        {
            "title": "Девочка с картинки",
            "duration_ms": 195000,  # 3:15
            "popularity": 82,
            "tempo": 125.0,
            "energy": 0.72,
            "valence": 0.7,
            "danceability": 0.85,
            "explicit": False
        },
        {
            "title": "Сердцеедка",
            "duration_ms": 203000,  # 3:23
            "popularity": 90,
            "tempo": 130.0,
            "energy": 0.8,
            "valence": 0.75,
            "danceability": 0.9,
            "explicit": False
        },
        {
            "title": "Будильник",
            "duration_ms": 186000,  # 3:06
            "popularity": 75,
            "tempo": 115.0,
            "energy": 0.6,
            "valence": 0.5,
            "danceability": 0.7,
            "explicit": False
        },
        {
            "title": "58",
            "duration_ms": 172000,  # 2:52
            "popularity": 85,
            "tempo": 140.0,
            "energy": 0.85,
            "valence": 0.8,
            "danceability": 0.95,
            "explicit": False
        }
    ]
}

async def create_test_data():
    """Создает тестовые данные для альбома Егора Крида"""
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 1. Создаем жанр
            print("🎵 Создаем жанр...")
            genre_response = await client.post(f"{BASE_URL}/genres/", json=egor_krid_data["genre"])
            if genre_response.status_code == 201:
                genre_id = genre_response.json()["id"]
                print(f"✅ Жанр создан с ID: {genre_id}")
            else:
                print(f"❌ Ошибка создания жанра: {genre_response.text}")
                # Попробуем найти существующий жанр
                genres_response = await client.get(f"{BASE_URL}/genres/")
                if genres_response.status_code == 200:
                    genres = genres_response.json()
                    hip_hop_genre = next((g for g in genres if "хип" in g["name"].lower()), None)
                    if hip_hop_genre:
                        genre_id = hip_hop_genre["id"]
                        print(f"✅ Используем существующий жанр: {genre_id}")
                    else:
                        genre_id = None
                else:
                    genre_id = None
            
            # 2. Создаем артиста
            print("🎤 Создаем артиста...")
            artist_response = await client.post(f"{BASE_URL}/artists/", json=egor_krid_data["artist"])
            if artist_response.status_code == 201:
                artist_id = artist_response.json()["id"]
                print(f"✅ Артист создан с ID: {artist_id}")
            else:
                print(f"❌ Ошибка создания артиста: {artist_response.text}")
                return
            
            # 3. Создаем альбом
            print("💿 Создаем альбом...")
            album_data = {
                **egor_krid_data["album"],
                "artist_id": artist_id,
                "release_date": egor_krid_data["album"]["release_date"]
            }
            album_response = await client.post(f"{BASE_URL}/albums/", json=album_data)
            if album_response.status_code == 201:
                album_id = album_response.json()["id"]
                print(f"✅ Альбом создан с ID: {album_id}")
            else:
                print(f"❌ Ошибка создания альбома: {album_response.text}")
                return
            
            # 4. Создаем треки
            print("🎶 Создаем треки...")
            created_tracks = []
            for i, track_data in enumerate(egor_krid_data["tracks"], 1):
                track_payload = {
                    **track_data,
                    "artist_id": artist_id,
                    "album_id": album_id,
                    "genre_id": genre_id
                }
                
                track_response = await client.post(f"{BASE_URL}/tracks/", json=track_payload)
                if track_response.status_code == 201:
                    track_id = track_response.json()["id"]
                    created_tracks.append(track_id)
                    print(f"✅ Трек {i}/6 '{track_data['title']}' создан с ID: {track_id}")
                else:
                    print(f"❌ Ошибка создания трека '{track_data['title']}': {track_response.text}")
            
            print(f"\n🎉 Успешно создано:")
            print(f"   🎤 Артист: Егор Крид (ID: {artist_id})")
            print(f"   💿 Альбом: Меньше чем три (ID: {album_id})")
            print(f"   🎵 Жанр: Хип-хоп (ID: {genre_id})")
            print(f"   🎶 Треков: {len(created_tracks)}")
            
            # 5. Проверим результат
            print("\n📋 Проверяем созданные данные...")
            album_response = await client.get(f"{BASE_URL}/albums/{album_id}")
            if album_response.status_code == 200:
                album_info = album_response.json()
                print(f"✅ Альбом найден: {album_info['title']}")
            
            tracks_response = await client.get(f"{BASE_URL}/tracks/", params={"album_id": album_id})
            if tracks_response.status_code == 200:
                tracks = tracks_response.json()
                print(f"✅ Найдено треков в альбоме: {len(tracks)}")
                for track in tracks:
                    print(f"   🎵 {track['title']} ({track['duration_ms']/1000:.0f}с)")
                    
        except Exception as e:
            print(f"❌ Произошла ошибка: {e}")

if __name__ == "__main__":
    print("🚀 Запуск создания тестовых данных для альбома Егора Крида 'Меньше чем три'")
    asyncio.run(create_test_data())
