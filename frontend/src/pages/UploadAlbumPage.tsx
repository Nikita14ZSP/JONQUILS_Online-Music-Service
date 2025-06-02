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

const UploadAlbumPage: React.FC = () => {
    const [title, setTitle] = useState('');
    const [releaseDate, setReleaseDate] = useState('');
    const [coverImageUrl, setCoverImageUrl] = useState('');
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

        const albumData = {
            title,
            artist_id: parseInt(artistId),
            release_date: releaseDate ? new Date(releaseDate).toISOString() : null,
            cover_image_url: coverImageUrl || null
        };

        try {
            setLoading(true);
            const response = await api.post('/api/v1/albums/', albumData);
            setSuccessMessage(`Альбом "${title}" успешно создан! ID: ${response.data.id}`);
            
            // Очищаем форму
            setTitle('');
            setReleaseDate('');
            setCoverImageUrl('');

            // Перенаправляем на профиль через 2 секунды
            setTimeout(() => {
                navigate('/profile');
            }, 2000);
        } catch (err: any) {
            console.error("Failed to create album:", err);
            setError(err.response?.data?.detail || "Не удалось создать альбом.");
        } finally {
            setLoading(false);
        }
    };

    if (!artistId) {
        return (
            <div className="container">
                <h2>Ошибка доступа</h2>
                <p>Вы должны быть артистом для создания альбомов.</p>
            </div>
        );
    }

    return (
        <div className="container">
            <h2>Создание нового альбома</h2>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            {successMessage && <p style={{ color: 'green' }}>{successMessage}</p>}
            
            <form onSubmit={handleSubmit} style={{ maxWidth: '600px' }}>
                <div className="form-group">
                    <label htmlFor="title">Название альбома *:</label>
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
                    <label htmlFor="releaseDate">Дата выпуска (опционально):</label>
                    <input
                        type="date"
                        id="releaseDate"
                        value={releaseDate}
                        onChange={(e) => setReleaseDate(e.target.value)}
                        style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="coverImageUrl">URL обложки альбома (опционально):</label>
                    <input
                        type="url"
                        id="coverImageUrl"
                        value={coverImageUrl}
                        onChange={(e) => setCoverImageUrl(e.target.value)}
                        placeholder="https://example.com/album-cover.jpg"
                        style={{ width: '100%', padding: '8px', marginBottom: '10px' }}
                    />
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
                    {loading ? 'Создается...' : 'Создать альбом'}
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

            <div style={{ marginTop: '20px', padding: '15px', backgroundColor: '#333', borderRadius: '4px' }}>
                <h3>Совет:</h3>
                <p>После создания альбома вы можете загружать треки и указывать ID этого альбома при загрузке.</p>
            </div>
        </div>
    );
};

export default UploadAlbumPage;
