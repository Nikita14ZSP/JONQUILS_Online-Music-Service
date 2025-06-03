from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Form
import aiofiles
import os
from sqlalchemy.orm import Session
from app.db.database import get_db # Исправленный импорт get_db для получения сессии БД
from app.schemas.track import TrackUploadFromFile, Track as TrackSchema, TrackMetadataForAlbumUpload # Импорт схемы Track и TrackUploadFromFile
from app.db.models import Track as TrackModel # Импорт модели Track
from datetime import datetime
from app.schemas.album import AlbumCreate, Album as AlbumSchema
from app.db.models import Album as AlbumModel # Импорт модели Album

router = APIRouter()

UPLOAD_DIR = "app/static/tracks" # Директория для сохранения загруженных треков

@router.post("/uploadfile/")
async def create_upload_file(
    file: UploadFile = File(...),
    data: str = Form(...), # Метаданные трека в виде JSON-строки
    db: Session = Depends(get_db)
):
    track_data = TrackUploadFromFile.parse_raw(data) # Парсим JSON-строку в Pydantic-модель

    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    # Генерируем уникальное имя файла для предотвращения коллизий
    # Можно использовать UUID или добавить к имени timestamp
    file_extension = os.path.splitext(file.filename)[1]
    timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = f"{track_data.title}_{timestamp_str}{file_extension}"
    file_location = os.path.join(UPLOAD_DIR, unique_filename)
    relative_file_path = f"static/tracks/{unique_filename}" # Путь для сохранения в БД

    try:
        async with aiofiles.open(file_location, "wb") as out_file:
            while content := await file.read(1024):  # Читаем по 1024 байта
                await out_file.write(content)
        
        # Создаем запись о треке в базе данных
        db_track = TrackModel(
            title=track_data.title,
            artist_id=track_data.artist_id,
            album_id=track_data.album_id,
            genre_id=track_data.genre_id,
            explicit=track_data.explicit,
            duration_ms=track_data.duration_ms,
            file_path=relative_file_path, # Сохраняем локальный путь
            created_at=datetime.utcnow()
        )
        db.add(db_track)
        db.commit()
        db.refresh(db_track)

        return TrackSchema.model_validate(db_track) # Возвращаем полную схему трека
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не удалось загрузить файл или сохранить данные трека: {e}"
        )

@router.post("/uploadalbum/")
async def create_upload_album(
    album_data: str = Form(...),
    track_data: str = Form(...),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    try:
        album_info = AlbumCreate.parse_raw(album_data)
        tracks_metadata = [TrackMetadataForAlbumUpload.parse_raw(t) for t in track_data.split('__TRACK_DELIMITER__') if t.strip()] # Разделяем строки метаданных
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неверный формат метаданных: {e}"
        )

    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    # Создаем запись об альбоме в базе данных
    db_album = AlbumModel(
        title=album_info.title,
        artist_id=album_info.artist_id,
        release_date=album_info.release_date,
        genre_id=album_info.genre_id,
        created_at=datetime.utcnow()
    )
    db.add(db_album)
    db.flush() # Используем flush, чтобы получить id альбома до commit

    uploaded_tracks = []

    for file in files:
        # Ищем соответствующую метаданные по имени файла
        track_meta = next((tm for tm in tracks_metadata if tm.file_name == file.filename), None)
        if not track_meta:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Метаданные для файла {file.filename} не найдены."
            )

        file_extension = os.path.splitext(file.filename)[1]
        timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_filename = f"{track_meta.title}_{timestamp_str}{file_extension}"
        file_location = os.path.join(UPLOAD_DIR, unique_filename)
        relative_file_path = f"static/tracks/{unique_filename}"

        try:
            async with aiofiles.open(file_location, "wb") as out_file:
                while content := await file.read(1024):
                    await out_file.write(content)
            
            # Создаем запись о треке в базе данных
            db_track = TrackModel(
                title=track_meta.title,
                artist_id=db_album.artist_id, # Используем artist_id альбома
                album_id=db_album.id, # Привязываем трек к созданному альбому
                genre_id=track_meta.genre_id or db_album.genre_id, # Используем жанр трека или альбома
                explicit=track_meta.explicit,
                duration_ms=track_meta.duration_ms,
                file_path=relative_file_path,
                created_at=datetime.utcnow()
            )
            db.add(db_track)
            uploaded_tracks.append(TrackSchema.model_validate(db_track))

        except Exception as e:
            # Откатываем изменения, если загрузка или сохранение трека не удались
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Не удалось загрузить файл {file.filename} или сохранить данные трека: {e}"
            )
    
    db.commit() # Коммитим все изменения после успешной обработки всех треков
    db.refresh(db_album)

    return {"album": AlbumSchema.model_validate(db_album), "tracks": uploaded_tracks} 