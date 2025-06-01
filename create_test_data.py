#!/usr/bin/env python3
"""
Скрипт для создания тестовых данных для музыкального сервиса
"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import AsyncSessionLocal
from app.db.models import Genre, Artist, Album, Track
from datetime import datetime

async def create_test_data():
    """Создание тестовых данных"""
    
    async with AsyncSessionLocal() as db:
        print("🎵 Создаем тестовые данные для музыкального сервиса...")
        
        # 1. Создаем жанры
        print("\n📂 Создаем жанры...")
        genres_data = [
            {"name": "Рок", "description": "Рок музыка"},
            {"name": "Поп", "description": "Популярная музыка"},
            {"name": "Хип-хоп", "description": "Хип-хоп и рэп"},
            {"name": "Электронная", "description": "Электронная музыка"},
            {"name": "Джаз", "description": "Джазовая музыка"},
            {"name": "Классическая", "description": "Классическая музыка"},
            {"name": "Блюз", "description": "Блюз"},
            {"name": "Кантри", "description": "Кантри музыка"},
        ]
        
        genres = []
        for genre_data in genres_data:
            # Проверяем, есть ли уже такой жанр
            from sqlalchemy import select
            query = select(Genre).where(Genre.name == genre_data["name"])
            result = await db.execute(query)
            existing_genre = result.scalar_one_or_none()
            
            if not existing_genre:
                genre = Genre(**genre_data)
                db.add(genre)
                genres.append(genre)
                print(f"  ✅ Создан жанр: {genre_data['name']}")
            else:
                genres.append(existing_genre)
                print(f"  ⚠️  Жанр уже существует: {genre_data['name']}")
        
        await db.commit()
        
        # Получаем ID жанров
        for genre in genres:
            await db.refresh(genre)
        
        # 2. Создаем исполнителей
        print("\n🎤 Создаем исполнителей...")
        artists_data = [
            {
                "name": "The Beatles",
                "bio": "Легендарная британская рок-группа",
                "country": "Великобритания",
                "image_url": "https://example.com/beatles.jpg"
            },
            {
                "name": "Queen",
                "bio": "Британская рок-группа",
                "country": "Великобритания",
                "image_url": "https://example.com/queen.jpg"
            },
            {
                "name": "Eminem",
                "bio": "Американский рэпер",
                "country": "США",
                "image_url": "https://example.com/eminem.jpg"
            },
            {
                "name": "Daft Punk",
                "bio": "Французский электронный дуэт",
                "country": "Франция",
                "image_url": "https://example.com/daftpunk.jpg"
            },
            {
                "name": "Кино",
                "bio": "Советская рок-группа",
                "country": "СССР",
                "image_url": "https://example.com/kino.jpg"
            }
        ]
        
        artists = []
        for artist_data in artists_data:
            # Проверяем, есть ли уже такой исполнитель
            query = select(Artist).where(Artist.name == artist_data["name"])
            result = await db.execute(query)
            existing_artist = result.scalar_one_or_none()
            
            if not existing_artist:
                artist = Artist(**artist_data)
                db.add(artist)
                artists.append(artist)
                print(f"  ✅ Создан исполнитель: {artist_data['name']}")
            else:
                artists.append(existing_artist)
                print(f"  ⚠️  Исполнитель уже существует: {artist_data['name']}")
        
        await db.commit()
        
        # Получаем ID исполнителей
        for artist in artists:
            await db.refresh(artist)
        
        # 3. Создаем альбомы
        print("\n💿 Создаем альбомы...")
        albums_data = [
            {
                "title": "Abbey Road",
                "artist_id": artists[0].id,  # The Beatles
                "release_date": datetime(1969, 9, 26),
                "cover_image_url": "https://example.com/abbey-road.jpg"
            },
            {
                "title": "A Night at the Opera",
                "artist_id": artists[1].id,  # Queen
                "release_date": datetime(1975, 11, 21),
                "cover_image_url": "https://example.com/night-opera.jpg"
            },
            {
                "title": "The Marshall Mathers LP",
                "artist_id": artists[2].id,  # Eminem
                "release_date": datetime(2000, 5, 23),
                "cover_image_url": "https://example.com/mmlp.jpg"
            },
            {
                "title": "Discovery",
                "artist_id": artists[3].id,  # Daft Punk
                "release_date": datetime(2001, 2, 26),
                "cover_image_url": "https://example.com/discovery.jpg"
            },
            {
                "title": "Группа крови",
                "artist_id": artists[4].id,  # Кино
                "release_date": datetime(1988, 1, 1),
                "cover_image_url": "https://example.com/gruppa-krovi.jpg"
            }
        ]
        
        albums = []
        for album_data in albums_data:
            # Проверяем, есть ли уже такой альбом
            query = select(Album).where(
                Album.title == album_data["title"],
                Album.artist_id == album_data["artist_id"]
            )
            result = await db.execute(query)
            existing_album = result.scalar_one_or_none()
            
            if not existing_album:
                album = Album(**album_data)
                db.add(album)
                albums.append(album)
                print(f"  ✅ Создан альбом: {album_data['title']}")
            else:
                albums.append(existing_album)
                print(f"  ⚠️  Альбом уже существует: {album_data['title']}")
        
        await db.commit()
        
        # Получаем ID альбомов
        for album in albums:
            await db.refresh(album)
        
        # 4. Создаем треки
        print("\n🎵 Создаем треки...")
        
        # Получаем жанры по именам для удобства
        rock_genre = next(g for g in genres if g.name == "Рок")
        pop_genre = next(g for g in genres if g.name == "Поп")
        hiphop_genre = next(g for g in genres if g.name == "Хип-хоп")
        electronic_genre = next(g for g in genres if g.name == "Электронная")
        
        tracks_data = [
            # The Beatles - Abbey Road
            {
                "title": "Come Together",
                "artist_id": artists[0].id,
                "album_id": albums[0].id,
                "genre_id": rock_genre.id,
                "duration_ms": 259000,
                "popularity": 85,
                "file_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",  # Тестовый аудиофайл
                "explicit": False
            },
            {
                "title": "Something",
                "artist_id": artists[0].id,
                "album_id": albums[0].id,
                "genre_id": rock_genre.id,
                "duration_ms": 183000,
                "popularity": 78,
                "file_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
                "explicit": False
            },
            # Queen - A Night at the Opera
            {
                "title": "Bohemian Rhapsody",
                "artist_id": artists[1].id,
                "album_id": albums[1].id,
                "genre_id": rock_genre.id,
                "duration_ms": 355000,
                "popularity": 95,
                "file_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
                "explicit": False
            },
            # Eminem
            {
                "title": "The Real Slim Shady",
                "artist_id": artists[2].id,
                "album_id": albums[2].id,
                "genre_id": hiphop_genre.id,
                "duration_ms": 284000,
                "popularity": 88,
                "file_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
                "explicit": True
            },
            # Daft Punk
            {
                "title": "One More Time",
                "artist_id": artists[3].id,
                "album_id": albums[3].id,
                "genre_id": electronic_genre.id,
                "duration_ms": 320000,
                "popularity": 82,
                "file_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
                "explicit": False
            },
            # Кино
            {
                "title": "Группа крови",
                "artist_id": artists[4].id,
                "album_id": albums[4].id,
                "genre_id": rock_genre.id,
                "duration_ms": 272000,
                "popularity": 90,
                "file_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
                "explicit": False
            }
        ]
        
        tracks = []
        for track_data in tracks_data:
            # Проверяем, есть ли уже такой трек
            query = select(Track).where(
                Track.title == track_data["title"],
                Track.artist_id == track_data["artist_id"]
            )
            result = await db.execute(query)
            existing_track = result.scalar_one_or_none()
            
            if not existing_track:
                track = Track(**track_data)
                db.add(track)
                tracks.append(track)
                print(f"  ✅ Создан трек: {track_data['title']}")
            else:
                tracks.append(existing_track)
                print(f"  ⚠️  Трек уже существует: {track_data['title']}")
        
        await db.commit()
        
        print(f"\n🎉 Создание тестовых данных завершено!")
        print(f"📊 Статистика:")
        print(f"  Жанров: {len(genres)}")
        print(f"  Исполнителей: {len(artists)}")
        print(f"  Альбомов: {len(albums)}")
        print(f"  Треков: {len(tracks)}")
        print(f"\n🚀 Теперь можете тестировать API!")

if __name__ == "__main__":
    asyncio.run(create_test_data())
