import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

interface Album {
    id: number;
    title: string;
    artist_id: number;
    release_date: string;
    cover_image_url: string;
    spotify_id: string;
    created_at: string;
}

const AlbumDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [album, setAlbum] = useState<Album | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAlbum = async () => {
            try {
                const response = await axios.get<Album>(`http://localhost:8000/api/v1/albums/${id}`);
                setAlbum(response.data);
            } catch (err) {
                setError('Не удалось загрузить информацию об альбоме.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        if (id) {
            fetchAlbum();
        }
    }, [id]);

    if (loading) return <div className="page-content">Загрузка альбома...</div>;
    if (error) return <div className="page-content" style={{ color: 'red' }}>{error}</div>;
    if (!album) return <div className="page-content">Альбом не найден.</div>;

    return (
        <div className="page-content album-detail-page">
            <h1>{album.title}</h1>
            {album.cover_image_url && <img src={album.cover_image_url} alt={album.title} style={{ width: '200px', height: '200px', objectFit: 'cover' }} />}
            <p>Дата релиза: {new Date(album.release_date).toLocaleDateString()}</p>
            {/* Дополнительная информация об альбоме */}
        </div>
    );
};

export default AlbumDetailPage; 