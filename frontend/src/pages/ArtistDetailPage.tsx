import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

interface Artist {
    id: number;
    user_id: number;
    name: string;
    bio: string;
    country: string;
    image_url: string;
    spotify_id: string;
    created_at: string;
}

const ArtistDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [artist, setArtist] = useState<Artist | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchArtist = async () => {
            try {
                const response = await axios.get<Artist>(`http://localhost:8000/api/v1/artists/${id}`);
                setArtist(response.data);
            } catch (err) {
                setError('Не удалось загрузить информацию об исполнителе.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        if (id) {
            fetchArtist();
        }
    }, [id]);

    if (loading) return <div className="page-content">Загрузка исполнителя...</div>;
    if (error) return <div className="page-content" style={{ color: 'red' }}>{error}</div>;
    if (!artist) return <div className="page-content">Исполнитель не найден.</div>;

    return (
        <div className="page-content artist-detail-page">
            <h1>{artist.name}</h1>
            {artist.image_url && <img src={artist.image_url} alt={artist.name} style={{ width: '200px', height: '200px', objectFit: 'cover', borderRadius: '50%' }} />}
            <p>Страна: {artist.country}</p>
            <p>О себе: {artist.bio}</p>
            {/* Дополнительная информация об исполнителе */}
        </div>
    );
};

export default ArtistDetailPage; 