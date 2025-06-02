import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

interface TrackUploadData {
    title: string;
    artist_id: number;
    album_id?: number;
    genre_id?: number;
    explicit?: boolean;
    duration_ms?: number;
}

interface AlbumUploadData {
    title: string;
    artist_id: number;
    release_date?: string;
    genre_id?: number;
}

const ArtistUploadPage: React.FC = () => {
    const navigate = useNavigate();
    const [trackFile, setTrackFile] = useState<File | null>(null);
    const [trackTitle, setTrackTitle] = useState<string>('');
    const [artistId, setArtistId] = useState<number>(0);
    const [albumId, setAlbumId] = useState<number | undefined>(undefined);
    const [genreId, setGenreId] = useState<number | undefined>(undefined);
    const [explicit, setExplicit] = useState<boolean>(false);
    const [durationMs, setDurationMs] = useState<number | undefined>(undefined);
    const [message, setMessage] = useState<string>('');

    // Новые состояния для загрузки альбома
    const [albumTitle, setAlbumTitle] = useState<string>('');
    const [albumArtistId, setAlbumArtistId] = useState<number>(0);
    const [albumReleaseDate, setAlbumReleaseDate] = useState<string>('');
    const [albumGenreId, setAlbumGenreId] = useState<number | undefined>(undefined);
    const [albumTrackFiles, setAlbumTrackFiles] = useState<File[]>([]);
    const [albumMessage, setAlbumMessage] = useState<string>('');

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files && event.target.files.length > 0) {
            setTrackFile(event.target.files[0]);
        }
    };

    const handleAlbumFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        if (event.target.files) {
            setAlbumTrackFiles(Array.from(event.target.files));
        }
    };

    const handleUploadSingleTrack = async () => {
        if (!trackFile || !trackTitle || !artistId) {
            setMessage('Пожалуйста, заполните все обязательные поля (файл, название, ID артиста).');
            return;
        }

        const formData = new FormData();
        formData.append('file', trackFile);

        const trackData: TrackUploadData = {
            title: trackTitle,
            artist_id: artistId,
            ...(albumId && { album_id: albumId }),
            ...(genreId && { genre_id: genreId }),
            ...(explicit && { explicit: explicit }),
            ...(durationMs && { duration_ms: durationMs }),
        };
        
        formData.append('data', JSON.stringify(trackData));

        try {
            setMessage('Загрузка трека...');
            const response = await axios.post(
                `http://localhost:8000/api/v1/upload/uploadfile/`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                }
            );
            setMessage(`Трек успешно загружен: ${response.data.title} (ID: ${response.data.id})`);
            setTrackFile(null);
            setTrackTitle('');
            setArtistId(0);
            setAlbumId(undefined);
            setGenreId(undefined);
            setExplicit(false);
            setDurationMs(undefined);
        } catch (error) {
            setMessage('Ошибка при загрузке трека.');
            console.error('Ошибка загрузки трека:', error);
        }
    };

    const handleUploadAlbum = async () => {
        if (!albumTitle || !albumArtistId || albumTrackFiles.length === 0) {
            setAlbumMessage('Пожалуйста, заполните название альбома, ID артиста и выберите хотя бы один трек.');
            return;
        }

        setAlbumMessage('Загрузка альбома...');

        const formData = new FormData();

        const albumData: AlbumUploadData = {
            title: albumTitle,
            artist_id: albumArtistId,
            ...(albumReleaseDate && { release_date: albumReleaseDate }),
            ...(albumGenreId && { genre_id: albumGenreId }),
        };
        formData.append('album_data', JSON.stringify(albumData));

        const trackMetadataArray = albumTrackFiles.map(file => {
            // В реальном приложении метаданные треков должны быть введены пользователем или извлечены из файлов
            // Для простоты, пока используем имя файла как название трека
            return {
                file_name: file.name,
                title: file.name.split('.')[0], // Используем имя файла без расширения как название трека
                duration_ms: undefined, // Заглушка, можно извлечь из файла
                explicit: false,
                genre_id: albumGenreId // Используем жанр альбома для треков
            };
        });

        // Сериализуем метаданные треков в строку, разделенную специальным символом
        const trackDataString = trackMetadataArray.map(t => JSON.stringify(t)).join('__TRACK_DELIMITER__');
        formData.append('track_data', trackDataString);

        albumTrackFiles.forEach(file => {
            formData.append('files', file);
        });

        try {
            const response = await axios.post(
                `http://localhost:8000/api/v1/upload/uploadalbum/`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                }
            );
            setAlbumMessage(`Альбом \'${response.data.album.title}\' (ID: ${response.data.album.id}) успешно загружен. Загружено треков: ${response.data.tracks.length}`);
            // Очищаем форму альбома
            setAlbumTitle('');
            setAlbumArtistId(0);
            setAlbumReleaseDate('');
            setAlbumGenreId(undefined);
            setAlbumTrackFiles([]);
        } catch (error) {
            console.error('Ошибка загрузки альбома:', error);
            if (axios.isAxiosError(error) && error.response) {
                setAlbumMessage(`Ошибка при загрузке альбома: ${error.response.data.detail || error.message}`);
            } else {
                setAlbumMessage('Ошибка при загрузке альбома.');
            }
        }
    };

    return (
        <div className="page-content upload-track-page">
            <h1>Загрузить контент</h1>
            <div className="upload-section">
                <h2>Загрузить один трек</h2>
                <div>
                    <label>Файл трека (MP3):</label>
                    <input type="file" accept="audio/mp3" onChange={handleFileChange} />
                </div>
                <div>
                    <label>Название трека:</label>
                    <input type="text" value={trackTitle} onChange={(e) => setTrackTitle(e.target.value)} placeholder="Название трека" />
                </div>
                <div>
                    <label>ID Артиста:</label>
                    <input type="number" value={artistId || ''} onChange={(e) => setArtistId(parseInt(e.target.value) || 0)} placeholder="ID Артиста" />
                </div>
                <div>
                    <label>ID Альбома (опционально):</label>
                    <input type="number" value={albumId || ''} onChange={(e) => setAlbumId(parseInt(e.target.value) || undefined)} placeholder="ID Альбома" />
                </div>
                <div>
                    <label>ID Жанра (опционально):</label>
                    <input type="number" value={genreId || ''} onChange={(e) => setGenreId(parseInt(e.target.value) || undefined)} placeholder="ID Жанра" />
                </div>
                <div>
                    <label>Продолжительность (мс, опционально):</label>
                    <input type="number" value={durationMs || ''} onChange={(e) => setDurationMs(parseInt(e.target.value) || undefined)} placeholder="Длительность в мс" />
                </div>
                <div>
                    <label>
                        <input type="checkbox" checked={explicit} onChange={(e) => setExplicit(e.target.checked)} />
                        Явный контент
                    </label>
                </div>
                <button onClick={handleUploadSingleTrack} disabled={!trackFile || !trackTitle || !artistId}>Загрузить трек</button>
            </div>

            <div className="upload-section">
                <h2>Загрузить альбом</h2>
                <div>
                    <label>Название альбома:</label>
                    <input type="text" value={albumTitle} onChange={(e) => setAlbumTitle(e.target.value)} placeholder="Название альбома" />
                </div>
                <div>
                    <label>ID Артиста для альбома:</label>
                    <input type="number" value={albumArtistId || ''} onChange={(e) => setAlbumArtistId(parseInt(e.target.value) || 0)} placeholder="ID Артиста" />
                </div>
                <div>
                    <label>Дата выпуска (YYYY-MM-DD, опционально):</label>
                    <input type="date" value={albumReleaseDate} onChange={(e) => setAlbumReleaseDate(e.target.value)} />
                </div>
                <div>
                    <label>ID Жанра альбома (опционально):</label>
                    <input type="number" value={albumGenreId || ''} onChange={(e) => setAlbumGenreId(parseInt(e.target.value) || undefined)} placeholder="ID Жанра" />
                </div>
                <div>
                    <label>Файлы треков (MP3):</label>
                    <input type="file" accept="audio/mp3" multiple onChange={handleAlbumFileChange} />
                </div>
                <button onClick={handleUploadAlbum} disabled={!albumTitle || !albumArtistId || albumTrackFiles.length === 0}>Загрузить альбом</button>
                {albumMessage && <p className="message">{albumMessage}</p>}
            </div>

            {message && <p className="message">{message}</p>}
        </div>
    );
};

export default ArtistUploadPage; 