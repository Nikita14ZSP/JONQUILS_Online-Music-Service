import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

// Создаем локальный экземпляр axios
const api = axios.create({
    baseURL: 'http://localhost:8001',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Добавляем интерцептор для токена
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

const UploadTrackPage: React.FC = () => {
    const [title, setTitle] = useState('');
    const [albumId, setAlbumId] = useState('');
    const [genreId, setGenreId] = useState('');
    const [fileUrl, setFileUrl] = useState('');
    const [previewUrl, setPreviewUrl] = useState('');
    const [explicit, setExplicit] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const navigate = useNavigate();

    const artistId = localStorage.getItem('artist_id');

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        setError(null);
        setSuccessMessage(null);

        if (!artistId) {
            setError("Artist ID не найден. Пожалуйста, войдите снова.");
            return;
        }

        const trackData = {
            title,
            file_url: fileUrl,
            artist_id: parseInt(artistId),
            album_id: albumId ? parseInt(albumId) : null,
            genre_id: genreId ? parseInt(genreId) : null,
            explicit,
            preview_url: previewUrl || null
        };

        try {
            setLoading(true);
            const response = await api.post('/api/v1/tracks/upload-from-url/', trackData);
            setSuccessMessage("Трек успешно загружен!");
            
            // Очищаем форму
            setTitle('');
            setAlbumId('');
            setGenreId('');
            setFileUrl('');
            setPreviewUrl('');
            setExplicit(false);

            // Перенаправляем на профиль через 2 секунды
            setTimeout(() => {
                navigate('/profile');
            }, 2000);
        } catch (err: any) {
            console.error("Failed to upload track:", err);
            setError(err.response?.data?.detail || "Не удалось загрузить трек.");
        } finally {
            setLoading(false);
        }
    };

    if (!artistId) {
        return (
            <div className="container">
                <h2>Ошибка доступа</h2>
                <p>Вы должны быть артистом для загрузки треков.</p>
            </div>
        );
    }

    return (
        <div className="container">
            <h2>Загрузка нового трека</h2>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            {successMessage && <p style={{ color: 'green' }}>{successMessage}</p>}
            
            <form onSubmit={handleSubmit} style={{ maxWidth: '600px' }}>
                <div className="form-group">
                    <label htmlFor="title">Название трека *:</label>
                    <input
                        type="text"
                        id="title"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        required
                        style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="fileUrl">URL аудиофайла *:</label>
                    <input
                        type="url"
                        id="fileUrl"
                        value={fileUrl}
                        onChange={(e) => setFileUrl(e.target.value)}
                        placeholder="https://example.com/track.mp3"
                        required
                        style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
                    />
                    <small style={{ color: '#ccc' }}>
                        Поддерживаемые форматы: MP3, WAV, FLAC, M4A, OGG, AAC
                    </small>
                </div>

                <div className="form-group">
                    <label htmlFor="albumId">ID альбома (опционально):</label>
                    <input
                        type="number"
                        id="albumId"
                        value={albumId}
                        onChange={(e) => setAlbumId(e.target.value)}
                        placeholder="Оставьте пустым для сингла"
                        style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="genreId">ID жанра (опционально):</label>
                    <input
                        type="number"
                        id="genreId"
                        value={genreId}
                        onChange={(e) => setGenreId(e.target.value)}
                        placeholder="Оставьте пустым если неизвестно"
                        style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="previewUrl">URL превью (опционально):</label>
                    <input
                        type="url"
                        id="previewUrl"
                        value={previewUrl}
                        onChange={(e) => setPreviewUrl(e.target.value)}
                        placeholder="https://example.com/preview.mp3"
                        style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="explicit" style={{ display: 'flex', alignItems: 'center' }}>
                        <input
                            type="checkbox"
                            id="explicit"
                            checked={explicit}
                            onChange={(e) => setExplicit(e.target.checked)}
                            style={{ marginRight: '8px' }}
                        />
                        Содержит нецензурную лексику
                    </label>
                </div>

                <button 
                    type="submit" 
                    disabled={loading}
                    style={{ 
                        padding: '10px 20px', 
                        backgroundColor: loading ? '#666' : '#4CAF50',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: loading ? 'not-allowed' : 'pointer'
                    }}
                >
                    {loading ? 'Загружается...' : 'Загрузить трек'}
                </button>
            </form>

            <div style={{ marginTop: '20px' }}>
                <button onClick={() => navigate('/profile')} style={{ 
                    padding: '8px 16px', 
                    backgroundColor: '#666', 
                    color: 'white', 
                    border: 'none', 
                    borderRadius: '4px',
                    cursor: 'pointer'
                }}>
                    Назад к профилю
                </button>
            </div>
        </div>
    );
};

export default UploadTrackPage;
