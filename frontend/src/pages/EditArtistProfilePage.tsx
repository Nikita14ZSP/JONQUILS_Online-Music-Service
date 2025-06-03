import React, { useState, useEffect } from 'react';
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

const EditArtistProfilePage: React.FC = () => {
    const [artistName, setArtistName] = useState('');
    const [bio, setBio] = useState('');
    const [country, setCountry] = useState('');
    const [imageUrl, setImageUrl] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const navigate = useNavigate();

    const artistId = localStorage.getItem('artist_id');

    useEffect(() => {
        if (!artistId) {
            setError("Artist ID not found. Please log in again.");
            setLoading(false);
            navigate('/login');
            return;
        }

        const fetchArtistData = async () => {
            try {
                setLoading(true);
                const response = await api.get(`/api/v1/artists/${artistId}`);
                const artist = response.data;
                setArtistName(artist.name || '');
                setBio(artist.bio || '');
                setCountry(artist.country || '');
                setImageUrl(artist.image_url || '');
                setLoading(false);
            } catch (err) {
                console.error("Failed to fetch artist data:", err);
                setError("Не удалось загрузить данные артиста.");
                setLoading(false);
            }
        };

        fetchArtistData();
    }, [artistId, navigate]);

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        setError(null);
        setSuccessMessage(null);

        if (!artistId) {
            setError("Artist ID is missing.");
            return;
        }

        const updatedData = {
            name: artistName,
            bio: bio,
            country: country,
            image_url: imageUrl,
        };

        try {
            await api.put(`/api/v1/artists/${artistId}`, updatedData);
            setSuccessMessage("Профиль артиста успешно обновлен!");
            // Optionally redirect or give time to read message
            setTimeout(() => {
                navigate('/profile');
            }, 2000);
        } catch (err: any) {
            console.error("Failed to update artist profile:", err);
            setError(err.response?.data?.detail || "Не удалось обновить профиль артиста.");
        }
    };

    if (loading) {
        return <p>Загрузка данных профиля артиста...</p>;
    }

    return (
        <div className="container">
            <h2>Редактировать профиль артиста</h2>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            {successMessage && <p style={{ color: 'green' }}>{successMessage}</p>}
            <form onSubmit={handleSubmit}>
                <div>
                    <label htmlFor="artistName">Имя артиста:</label>
                    <input
                        type="text"
                        id="artistName"
                        value={artistName}
                        onChange={(e) => setArtistName(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label htmlFor="bio">Биография:</label>
                    <textarea
                        id="bio"
                        value={bio}
                        onChange={(e) => setBio(e.target.value)}
                    />
                </div>
                <div>
                    <label htmlFor="country">Страна:</label>
                    <input
                        type="text"
                        id="country"
                        value={country}
                        onChange={(e) => setCountry(e.target.value)}
                    />
                </div>
                <div>
                    <label htmlFor="imageUrl">URL изображения:</label>
                    <input
                        type="url"
                        id="imageUrl"
                        value={imageUrl}
                        onChange={(e) => setImageUrl(e.target.value)}
                    />
                </div>
                <button type="submit">Сохранить изменения</button>
            </form>
        </div>
    );
};

export default EditArtistProfilePage;
